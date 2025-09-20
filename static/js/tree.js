// 递归渲染文件树，添加点击事件
function renderTree(tree, parentPath = '', collapsed = true) {
    if (!tree || tree.length === 0) return '';
    let html = '<ul>';
    for (const node of tree) {
        const fullPath = parentPath ? parentPath + '/' + node.name : node.name;
        if (node.is_dir) {
            html += `<li><span class='folder' onclick="toggleFolder(this)">${node.name}</span>`;
            if (node.children && node.children.length > 0) {
                html += `<ul style='display:none;'>` + renderTree(node.children, fullPath, true).replace(/^<ul>|<\/ul>$/g, '') + `</ul>`;
            }
            html += '</li>';
        } else {
            html += `<li><span class='file' onclick="previewFile('${encodeURIComponent(fullPath)}')">${node.name}</span></li>`;
        }
    }
    html += '</ul>';
    return html;
}

// 获取文件树数据并渲染
function loadFileTree() {
    fetch('/api/tree')
        .then(res => res.json())
        .then(data => {
            document.getElementById('file-tree').innerHTML = renderTree(data.tree, '', true);
        });
}

// 展开/折叠文件夹
function toggleFolder(el) {
    const li = el.parentElement;
    const ul = li.querySelector('ul');
    if (ul) {
        if (ul.children.length === 0 || (ul.innerHTML.trim() === '')) {
            alert('该文件夹是空的');
            return;
        }
        ul.style.display = ul.style.display === 'none' ? '' : 'none';
    }
}

// 文件预览
function previewFile(path) {
    fetch('/api/preview?path=' + path)
        .then(res => res.json())
        .then(data => {
            const body = document.getElementById('preview-body');
            if (data.type === 'text') {
                body.innerHTML = `<pre style='white-space:pre-wrap;'>${escapeHtml(data.content)}</pre>`;
            } else if (data.type === 'image') {
                body.innerHTML = `<img src='data:${data.mimetype};base64,${data.content}' style='max-width:70vw;max-height:70vh;' />`;
            } else if (data.type === 'video') {
                body.innerHTML = `<video src='data:${data.mimetype};base64,${data.content}' controls style='max-width:70vw;max-height:70vh;'></video>`;
            } else {
                body.innerHTML = '无法预览该文件类型';
            }
            document.getElementById('preview-modal').style.display = 'flex';
        });
}

function closePreview() {
    document.getElementById('preview-modal').style.display = 'none';
}

function escapeHtml(text) {
    var map = { '&': '&', '<': '<', '>': '>', '"': '"', "'": '&#39;' };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// 右键菜单
let contextTarget = null;
let contextTargetType = null;
let contextTargetPath = null;
document.addEventListener('contextmenu', function(e) {
    let node = e.target;
    const menu = document.getElementById('context-menu');
    if (node.classList.contains('folder') || node.classList.contains('file')) {
        e.preventDefault();
        contextTarget = node;
        contextTargetType = node.classList.contains('folder') ? 'folder' : 'file';
        // 解析路径
        let path = '';
        let cur = node;
        while (cur && cur.tagName === 'SPAN') {
            let li = cur.parentElement;
            let parentUl = li.parentElement;
            let parentLi = parentUl && parentUl.parentElement && parentUl.parentElement.tagName === 'LI' ? parentUl.parentElement : null;
            path = (cur.textContent + (path ? '/' + path : ''));
            cur = parentLi ? parentLi.querySelector('span.folder') : null;
        }
        contextTargetPath = encodeURIComponent(path);
        // 菜单显示
        menu.style.display = 'block';
        menu.style.left = e.pageX + 'px';
        menu.style.top = e.pageY + 'px';
        document.getElementById('menu-upload').style.display = contextTargetType === 'folder' ? '' : 'none';
    } else {
        // 空白处右键，视为根目录，只允许上传
        e.preventDefault();
        contextTarget = null;
        contextTargetType = 'root';
        contextTargetPath = encodeURIComponent('');
        menu.style.display = 'block';
        menu.style.left = e.pageX + 'px';
        menu.style.top = e.pageY + 'px';
        document.getElementById('menu-upload').style.display = '';
        document.getElementById('menu-download').style.display = 'none';
        document.getElementById('menu-delete').style.display = 'none';
    }
});

document.addEventListener('click', function() {
    const menu = document.getElementById('context-menu');
    menu.style.display = 'none';
    // 恢复菜单项显示
    document.getElementById('menu-download').style.display = '';
    document.getElementById('menu-delete').style.display = '';
});

// 下载
document.getElementById('menu-download').onclick = function(e) {
    e.stopPropagation();
    if (contextTargetType === 'file') {
        window.open('/api/download?path=' + contextTargetPath, '_blank');
    } else if (contextTargetType === 'folder') {
        window.open('/api/download_folder?path=' + contextTargetPath, '_blank');
    }
    document.getElementById('context-menu').style.display = 'none';
};

// 上传
document.getElementById('menu-upload').onclick = function(e) {
    e.stopPropagation();
    // 如果是根目录上传，传递'/'
    if (contextTargetType === 'root') {
        openUploadModal(""); // 直接传空字符串
    } else {
        openUploadModal(contextTargetPath);
    }
    document.getElementById('context-menu').style.display = 'none';
};

// 删除
document.getElementById('menu-delete').onclick = function(e) {
    e.stopPropagation();
    if (!contextTargetPath) return;
    if (!confirm('确定要删除此' + (contextTargetType === 'folder' ? '文件夹' : '文件') + '吗？')) return;
    fetch('/api/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: contextTargetPath, type: contextTargetType })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            refreshFileTree();
        } else {
            alert('删除失败' + ': ' + (data.error || '未知错误'));
        }
    })
    .catch(err => {
        alert('删除失败' + ': ' + err);
    });
    document.getElementById('context-menu').style.display = 'none';
};

// 上传弹窗逻辑
let uploadTargetPath = '';
function openUploadModal(path) {
    // 这里 path 已经被 encodeURIComponent 过了，直接用
    uploadTargetPath = path;
    document.getElementById('upload-modal').style.display = 'flex';
    document.getElementById('upload-status').innerText = '';
    document.getElementById('upload-form').reset();
}

function closeUploadModal() {
    document.getElementById('upload-modal').style.display = 'none';
}

// 关闭上传弹窗时清空文件选择
document.getElementById('upload-modal').addEventListener('click', function(e) {
    if (e.target === this) closeUploadModal();
});

// 拖拽上传
const dropArea = document.getElementById('drop-area');
dropArea.addEventListener('dragover', function(e) {
    e.preventDefault();
    dropArea.style.background = '#e0e0e0';
});

dropArea.addEventListener('dragleave', function(e) {
    e.preventDefault();
    dropArea.style.background = '';
});

dropArea.addEventListener('drop', function(e) {
    e.preventDefault();
    dropArea.style.background = '';
    document.getElementById('upload-input').files = e.dataTransfer.files;
});

// 上传表单提交
document.getElementById('upload-form').onsubmit = function(e) {
    e.preventDefault();
    const files = document.getElementById('upload-input').files;
    if (!files.length) return;
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }
    fetch('/api/upload?path=' + uploadTargetPath, {
        method: 'POST',
        body: formData
    }).then(res => res.json()).then(data => {
        document.getElementById('upload-status').innerText = data.success ? '上传成功' : ('上传失败' + ': ' + (data.error || ''));
        if (data.success) {
            setTimeout(() => {
                closeUploadModal();
                refreshFileTree();
            }, 800);
        }
    }).catch(err => {
        document.getElementById('upload-status').innerText = '上传失败' + ': ' + err;
    });
};

// Windows风格排序：文件夹在上，文件在下，数字优先，字母/拼音顺序，区分大小写，和资源管理器一致
function windowsSort(a, b) {
    // 文件夹优先
    if (a.is_dir !== b.is_dir) return a.is_dir ? -1 : 1;
    // 数字优先
    const aIsNum = /^\d/.test(a.name);
    const bIsNum = /^\d/.test(b.name);
    if (aIsNum && !bIsNum) return -1;
    if (!aIsNum && bIsNum) return 1;
    // 自然顺序（数字按数值，字母区分大小写，中文拼音）
    return a.name.localeCompare(b.name, 'zh-CN', { numeric: true, sensitivity: 'case' });
}

function sortTree(tree) {
    tree.sort(windowsSort);
    for (const node of tree) {
        if (node.is_dir && node.children) {
            sortTree(node.children);
        }
    }
}

// 刷新文件树
function refreshFileTree() {
    fetch('/api/tree')
        .then(res => res.json())
        .then(data => {
            sortTree(data.tree);
            document.getElementById('file-tree').innerHTML = renderTree(data.tree, '', true);
        });
}

// 美化文件树样式
const style = document.createElement('style');
style.innerHTML = `
    #file-tree ul { padding-left: 18px; }
    #file-tree li { margin: 2px 0; transition: background 0.2s; border-radius: 4px; }
    #file-tree li:hover { background: #f0f4ff; }
    #file-tree .folder { color: #1a73e8; font-weight: 600; }
    #file-tree .file { color: #333; }
    #file-tree .folder::before { content: '📂 '; }
    #file-tree .file::before { content: '📄 '; }
`;
document.head.appendChild(style);

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始加载
    refreshFileTree();
});
