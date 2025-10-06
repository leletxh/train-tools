// 文件浏览器管理器 - 平铺展示版本
class FileBrowserManager {
    constructor() {
        this.currentPath = '.';
        this.currentItems = [];
        this.sortType = 'default';
        this.previewCache = new Map();
        this.maxCacheSize = 20;
        
        // 上下文菜单状态
        this.contextTarget = null;
        this.contextTargetType = null;
        this.contextTargetPath = null;
        this.uploadTargetPath = '';
        
        // 编辑器状态
        this.currentEditFile = null;
        this.isEditing = false;
        
        // 初始化
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.addToolbar();
        this.loadDirectory();
        this.setupKeyboardShortcuts();
    }
    
    setupEventListeners() {
        // 右键菜单事件
        document.addEventListener('contextmenu', this.handleContextMenu.bind(this));
        document.addEventListener('click', this.hideContextMenu.bind(this));
        
        // 菜单项点击事件
        document.getElementById('menu-download').onclick = this.handleDownload.bind(this);
        document.getElementById('menu-upload').onclick = this.handleUpload.bind(this);
        document.getElementById('menu-delete').onclick = this.handleDelete.bind(this);
        
        // 上传相关事件
        this.setupUploadEvents();
        
        // 预览模态框事件
        document.getElementById('preview-close-btn').onclick = this.closePreview.bind(this);
        document.getElementById('preview-modal').onclick = (e) => {
            if (e.target === e.currentTarget) this.closePreview();
        };
    }
    
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl+R 刷新
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                this.refreshDirectory();
            }
            // ESC 关闭窗口
            if (e.key === 'Escape') {
                this.closePreview();
                this.closeUploadModal();
                this.closeEditor();
            }
            // F5 刷新
            if (e.key === 'F5') {
                e.preventDefault();
                this.refreshDirectory();
            }
            // Ctrl+S 保存文件（编辑模式）
            if (e.ctrlKey && e.key === 's' && this.isEditing) {
                e.preventDefault();
                this.saveFile();
            }
        });
    }
    
    addToolbar() {
        const toolbar = document.createElement('div');
        toolbar.className = 'file-browser-toolbar';
        toolbar.innerHTML = `
            <div class="toolbar-section">
                <div class="breadcrumb" id="breadcrumb"></div>
            </div>
            <div class="toolbar-section">
                <button id="refresh-btn" title="刷新 (F5)">🔄</button>
                <button id="new-file-btn" title="新建文件">📄+</button>
                <button id="upload-btn" title="上传文件">📤</button>
            </div>
            <div class="toolbar-section">
                <label>排序:</label>
                <select id="sort-select">
                    <option value="default">默认</option>
                    <option value="name">名称</option>
                    <option value="size">大小</option>
                    <option value="modified">修改时间</option>
                </select>
            </div>
            <div class="toolbar-section">
                <button id="cache-stats-btn" title="缓存统计">📊</button>
                <button id="clear-cache-btn" title="清理缓存">🗑️</button>
            </div>
        `;
        
        const fileTree = document.getElementById('file-tree');
        fileTree.parentNode.insertBefore(toolbar, fileTree);
        
        // 绑定工具栏事件
        document.getElementById('refresh-btn').onclick = () => this.refreshDirectory();
        document.getElementById('new-file-btn').onclick = () => this.showNewFileDialog();
        document.getElementById('upload-btn').onclick = () => this.openUploadModal(this.currentPath);
        document.getElementById('sort-select').onchange = (e) => this.changeSortType(e.target.value);
        document.getElementById('cache-stats-btn').onclick = () => this.showCacheStats();
        document.getElementById('clear-cache-btn').onclick = () => this.clearCache();
    }
    
    setupUploadEvents() {
        const uploadForm = document.getElementById('upload-form');
        const uploadInput = document.getElementById('upload-input');
        const dropArea = document.getElementById('drop-area');
        
        // 表单提交
        uploadForm.onsubmit = this.handleUploadSubmit.bind(this);
        
        // 拖拽上传
        dropArea.addEventListener('dragover', this.handleDragOver.bind(this));
        dropArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        dropArea.addEventListener('drop', this.handleDrop.bind(this));
        
        // 文件选择变化
        uploadInput.addEventListener('change', this.updateDropAreaText.bind(this));
        
        // 上传模态框关闭
        document.getElementById('upload-modal').addEventListener('click', (e) => {
            if (e.target === e.currentTarget) this.closeUploadModal();
        });
    }
    
    // 目录加载和渲染
    async loadDirectory(path = this.currentPath) {
        try {
            this.showLoading('正在加载目录...');
            
            const response = await fetch(`/api/directory?path=${encodeURIComponent(path)}&sort=${this.sortType}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.currentPath = path;
            this.currentItems = data.items;
            this.renderDirectory();
            this.updateBreadcrumb();
            this.hideLoading();
            
        } catch (error) {
            this.showError('加载目录失败: ' + error.message);
            this.hideLoading();
        }
    }
    
    renderDirectory() {
        const container = document.getElementById('file-tree');
        container.innerHTML = '';
        
        if (this.currentItems.length === 0) {
            container.innerHTML = '<div class="empty-directory">目录为空</div>';
            return;
        }
        
        const grid = document.createElement('div');
        grid.className = 'file-grid';
        
        for (const item of this.currentItems) {
            const itemEl = this.createFileItem(item);
            grid.appendChild(itemEl);
        }
        
        container.appendChild(grid);
    }
    
    createFileItem(item) {
        const itemEl = document.createElement('div');
        itemEl.className = 'file-item';
        itemEl.dataset.path = item.relative_path || item.name;
        itemEl.dataset.type = item.is_dir ? 'folder' : 'file';
        
        if (item.is_parent) {
            itemEl.classList.add('parent-folder');
        }
        
        const icon = this.getFileIcon(item);
        const size = item.is_dir ? '' : this.formatFileSize(item.size);
        const modified = item.modified ? new Date(item.modified * 1000).toLocaleDateString() : '';
        
        itemEl.innerHTML = `
            <div class="file-icon">${icon}</div>
            <div class="file-name" title="${item.name}">${this.escapeHtml(item.name)}</div>
            <div class="file-info">
                <span class="file-size">${size}</span>
                <span class="file-date">${modified}</span>
            </div>
        `;
        
        // 添加状态指示器
        if (!item.is_dir) {
            const indicators = document.createElement('div');
            indicators.className = 'file-indicators';
            
            if (item.preview_supported) {
                indicators.innerHTML += '<span class="indicator preview" title="支持预览">👁️</span>';
            }
            if (item.editable) {
                indicators.innerHTML += '<span class="indicator editable" title="可编辑">✏️</span>';
            }
            
            itemEl.appendChild(indicators);
        }
        
        // 点击事件
        itemEl.onclick = (e) => {
            e.stopPropagation();
            this.handleItemClick(item);
        };
        
        // 双击事件
        itemEl.ondblclick = (e) => {
            e.stopPropagation();
            this.handleItemDoubleClick(item);
        };
        
        return itemEl;
    }
    
    handleItemClick(item) {
        // 移除其他选中状态
        document.querySelectorAll('.file-item.selected').forEach(el => {
            el.classList.remove('selected');
        });
        
        // 添加选中状态
        const itemEl = document.querySelector(`[data-path="${item.relative_path || item.name}"]`);
        if (itemEl) {
            itemEl.classList.add('selected');
        }
    }
    
    handleItemDoubleClick(item) {
        if (item.is_dir) {
            // 进入目录
            if (item.is_parent) {
                this.loadDirectory(item.path);
            } else {
                this.loadDirectory(item.relative_path || item.path);
            }
        } else {
            // 预览或编辑文件
            if (item.editable) {
                this.editFile(item.relative_path || item.path);
            } else if (item.preview_supported) {
                this.previewFile(item.relative_path || item.path);
            }
        }
    }
    
    updateBreadcrumb() {
        const breadcrumb = document.getElementById('breadcrumb');
        const parts = this.currentPath === '.' ? [] : this.currentPath.split('/').filter(p => p);
        
        let html = '<span class="breadcrumb-item" onclick="fileBrowserManager.loadDirectory(\'.\')" title="根目录">🏠</span>';
        
        let currentPath = '.';
        for (let i = 0; i < parts.length; i++) {
            currentPath += '/' + parts[i];
            const isLast = i === parts.length - 1;
            
            if (isLast) {
                html += ` <span class="breadcrumb-separator">/</span> <span class="breadcrumb-item current">${this.escapeHtml(parts[i])}</span>`;
            } else {
                html += ` <span class="breadcrumb-separator">/</span> <span class="breadcrumb-item" onclick="fileBrowserManager.loadDirectory('${currentPath}')">${this.escapeHtml(parts[i])}</span>`;
            }
        }
        
        breadcrumb.innerHTML = html;
    }
    
    getFileIcon(item) {
        if (item.is_parent) {
            return '⬆️';
        }
        
        if (item.is_dir) {
            return '📁';
        }
        
        const ext = item.name.split('.').pop()?.toLowerCase() || '';
        const iconMap = {
            'py': '🐍', 'js': '📜', 'ts': '📘', 'html': '🌐', 'css': '🎨', 
            'json': '📋', 'md': '📝', 'txt': '📄', 'log': '📊', 'csv': '📈', 
            'xml': '📰', 'yaml': '⚙️', 'yml': '⚙️', 'sql': '🗃️',
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️', 'svg': '🖼️',
            'bmp': '🖼️', 'webp': '🖼️', 'ico': '🖼️',
            'mp4': '🎬', 'avi': '🎬', 'mov': '🎬', 'wmv': '🎬', 'mkv': '🎬',
            'mp3': '🎵', 'wav': '🎵', 'flac': '🎵', 'aac': '🎵',
            'pdf': '📕', 'doc': '📘', 'docx': '📘', 'xls': '📗', 'xlsx': '📗',
            'zip': '📦', 'rar': '📦', '7z': '📦', 'tar': '📦', 'gz': '📦'
        };
        
        return iconMap[ext] || '📄';
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // 文件预览
    async previewFile(path) {
        try {
            // 检查缓存
            if (this.previewCache.has(path)) {
                const cached = this.previewCache.get(path);
                this.showPreview(cached);
                return;
            }
            
            this.showLoading('正在加载预览...');
            
            const response = await fetch(`/api/preview?path=${encodeURIComponent(path)}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // 缓存结果
            this.cachePreview(path, data);
            
            this.showPreview(data);
            this.hideLoading();
            
        } catch (error) {
            this.showError('预览失败: ' + error.message);
            this.hideLoading();
        }
    }
    
    showPreview(data) {
        const modal = document.getElementById('preview-modal');
        const body = document.getElementById('preview-body');
        
        body.innerHTML = '';
        
        if (data.type === 'text') {
            const container = document.createElement('div');
            container.className = 'text-preview-container';
            
            // 添加编辑按钮
            const editBtn = document.createElement('button');
            editBtn.className = 'edit-btn';
            editBtn.textContent = '编辑文件';
            editBtn.onclick = () => {
                this.closePreview();
                this.editFile(this.currentEditFile);
            };
            
            const pre = document.createElement('pre');
            pre.className = 'text-preview';
            pre.textContent = data.content;
            
            // 添加文件信息
            const info = document.createElement('div');
            info.className = 'file-info';
            info.innerHTML = `
                <span>编码: ${data.encoding}</span>
                <span>行数: ${data.lines}</span>
                <span>大小: ${this.formatFileSize(data.size)}</span>
                ${data.truncated ? '<span style="color: orange;">文件已截断</span>' : ''}
            `;
            
            container.appendChild(info);
            container.appendChild(editBtn);
            container.appendChild(pre);
            body.appendChild(container);
            
        } else if (data.type === 'image') {
            if (data.url) {
                const img = document.createElement('img');
                img.src = data.url;
                img.style.cssText = 'max-width: 70vw; max-height: 70vh; object-fit: contain;';
                body.appendChild(img);
                
                if (data.warning) {
                    const warning = document.createElement('div');
                    warning.className = 'warning';
                    warning.textContent = data.warning;
                    body.insertBefore(warning, img);
                }
            } else {
                const img = document.createElement('img');
                img.src = `data:${data.mimetype};base64,${data.content}`;
                img.style.cssText = 'max-width: 70vw; max-height: 70vh; object-fit: contain;';
                body.appendChild(img);
            }
            
        } else if (data.type === 'video') {
            const video = document.createElement('video');
            video.src = data.url;
            video.controls = true;
            video.style.cssText = 'max-width: 70vw; max-height: 70vh;';
            body.appendChild(video);
            
        } else if (data.type === 'audio') {
            const audio = document.createElement('audio');
            audio.src = data.url;
            audio.controls = true;
            audio.style.width = '100%';
            body.appendChild(audio);
            
        } else {
            body.innerHTML = `<div class="no-preview">无法预览该文件类型<br><small>${data.message || ''}</small></div>`;
        }
        
        modal.style.display = 'flex';
    }
    
    closePreview() {
        document.getElementById('preview-modal').style.display = 'none';
    }
    
    cachePreview(path, data) {
        // 清理旧缓存
        if (this.previewCache.size >= this.maxCacheSize) {
            const firstKey = this.previewCache.keys().next().value;
            this.previewCache.delete(firstKey);
        }
        
        this.previewCache.set(path, data);
    }
    
    // 文件编辑
    async editFile(path) {
        try {
            this.showLoading('正在加载文件...');
            
            const response = await fetch(`/api/edit_file?path=${encodeURIComponent(path)}`);
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.currentEditFile = path;
            this.showEditor(data);
            this.hideLoading();
            
        } catch (error) {
            this.showError('加载文件失败: ' + error.message);
            this.hideLoading();
        }
    }
    
    showEditor(data) {
        // 创建编辑器模态框
        let editorModal = document.getElementById('editor-modal');
        if (!editorModal) {
            editorModal = document.createElement('div');
            editorModal.id = 'editor-modal';
            editorModal.className = 'editor-modal';
            editorModal.innerHTML = `
                <div class="editor-container">
                    <div class="editor-header">
                        <div class="editor-title">
                            <span id="editor-file-name"></span>
                            <span id="editor-file-info"></span>
                        </div>
                        <div class="editor-actions">
                            <button id="save-btn" title="保存 (Ctrl+S)">💾 保存</button>
                            <button id="close-editor-btn" title="关闭">✖</button>
                        </div>
                    </div>
                    <div class="editor-content">
                        <textarea id="file-editor" spellcheck="false"></textarea>
                    </div>
                    <div class="editor-status">
                        <span id="editor-status-text">就绪</span>
                        <span id="editor-cursor-pos">行 1, 列 1</span>
                    </div>
                </div>
            `;
            document.body.appendChild(editorModal);
            
            // 绑定事件
            document.getElementById('save-btn').onclick = () => this.saveFile();
            document.getElementById('close-editor-btn').onclick = () => this.closeEditor();
            
            // 编辑器事件
            const editor = document.getElementById('file-editor');
            editor.addEventListener('input', () => {
                this.markAsModified();
            });
            
            editor.addEventListener('keydown', (e) => {
                // Tab键插入空格
                if (e.key === 'Tab') {
                    e.preventDefault();
                    const start = editor.selectionStart;
                    const end = editor.selectionEnd;
                    editor.value = editor.value.substring(0, start) + '    ' + editor.value.substring(end);
                    editor.selectionStart = editor.selectionEnd = start + 4;
                }
            });
            
            // 光标位置更新
            editor.addEventListener('selectionchange', this.updateCursorPosition.bind(this));
            editor.addEventListener('keyup', this.updateCursorPosition.bind(this));
            editor.addEventListener('mouseup', this.updateCursorPosition.bind(this));
        }
        
        // 设置文件内容
        document.getElementById('editor-file-name').textContent = this.currentEditFile;
        document.getElementById('editor-file-info').textContent = 
            `${data.encoding} | ${data.lines} 行 | ${this.formatFileSize(data.size)}`;
        document.getElementById('file-editor').value = data.content;
        
        this.isEditing = true;
        this.isModified = false;
        editorModal.style.display = 'flex';
        
        // 聚焦编辑器
        setTimeout(() => {
            document.getElementById('file-editor').focus();
        }, 100);
    }
    
    markAsModified() {
        if (!this.isModified) {
            this.isModified = true;
            const title = document.getElementById('editor-file-name');
            title.textContent = this.currentEditFile + ' *';
            document.getElementById('editor-status-text').textContent = '已修改';
        }
    }
    
    updateCursorPosition() {
        const editor = document.getElementById('file-editor');
        const pos = editor.selectionStart;
        const lines = editor.value.substring(0, pos).split('\n');
        const line = lines.length;
        const col = lines[lines.length - 1].length + 1;
        
        document.getElementById('editor-cursor-pos').textContent = `行 ${line}, 列 ${col}`;
    }
    
    async saveFile() {
        try {
            const content = document.getElementById('file-editor').value;
            const encoding = 'utf-8'; // 默认使用UTF-8
            
            document.getElementById('editor-status-text').textContent = '保存中...';
            
            const response = await fetch('/api/save_file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    path: this.currentEditFile,
                    content: content,
                    encoding: encoding
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.isModified = false;
            document.getElementById('editor-file-name').textContent = this.currentEditFile;
            document.getElementById('editor-status-text').textContent = '保存成功';
            document.getElementById('editor-file-info').textContent = 
                `${encoding} | ${data.lines} 行 | ${this.formatFileSize(data.size)}`;
            
            // 清理相关缓存
            this.previewCache.delete(this.currentEditFile);
            
            setTimeout(() => {
                document.getElementById('editor-status-text').textContent = '就绪';
            }, 2000);
            
        } catch (error) {
            document.getElementById('editor-status-text').textContent = '保存失败: ' + error.message;
        }
    }
    
    closeEditor() {
        if (this.isModified) {
            if (!confirm('文件已修改，确定要关闭吗？未保存的更改将丢失。')) {
                return;
            }
        }
        
        document.getElementById('editor-modal').style.display = 'none';
        this.isEditing = false;
        this.currentEditFile = null;
        this.isModified = false;
    }
    
    // 新建文件
    showNewFileDialog() {
        const fileName = prompt('请输入文件名（包含扩展名）:');
        if (!fileName) return;
        
        const filePath = this.currentPath === '.' ? fileName : `${this.currentPath}/${fileName}`;
        this.createFile(filePath);
    }
    
    async createFile(path) {
        try {
            const response = await fetch('/api/create_file', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    path: path,
                    content: '',
                    encoding: 'utf-8'
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            this.showSuccess('文件创建成功');
            this.refreshDirectory();
            
            // 自动打开编辑器
            setTimeout(() => {
                this.editFile(path);
            }, 500);
            
        } catch (error) {
            this.showError('创建文件失败: ' + error.message);
        }
    }
    
    // 右键菜单处理
    handleContextMenu(e) {
        const item = e.target.closest('.file-item');
        const menu = document.getElementById('context-menu');
        
        if (item) {
            e.preventDefault();
            this.contextTarget = item;
            this.contextTargetType = item.dataset.type;
            this.contextTargetPath = item.dataset.path;
            
            // 菜单显示
            menu.style.display = 'block';
            menu.style.left = e.pageX + 'px';
            menu.style.top = e.pageY + 'px';
            
            // 根据类型显示/隐藏菜单项
            document.getElementById('menu-upload').style.display = 
                this.contextTargetType === 'folder' ? '' : 'none';
                
        } else if (!item) {
            // 空白处右键
            e.preventDefault();
            this.contextTarget = null;
            this.contextTargetType = 'root';
            this.contextTargetPath = this.currentPath;
            
            menu.style.display = 'block';
            menu.style.left = e.pageX + 'px';
            menu.style.top = e.pageY + 'px';
            
            document.getElementById('menu-upload').style.display = '';
            document.getElementById('menu-download').style.display = 'none';
            document.getElementById('menu-delete').style.display = 'none';
        }
    }
    
    hideContextMenu() {
        const menu = document.getElementById('context-menu');
        menu.style.display = 'none';
        
        // 恢复菜单项显示
        document.getElementById('menu-download').style.display = '';
        document.getElementById('menu-delete').style.display = '';
    }
    
    handleDownload(e) {
        e.stopPropagation();
        if (this.contextTargetType === 'file') {
            window.open(`/api/download?path=${encodeURIComponent(this.contextTargetPath)}`, '_blank');
        } else if (this.contextTargetType === 'folder') {
            window.open(`/api/download_folder?path=${encodeURIComponent(this.contextTargetPath)}`, '_blank');
        }
        this.hideContextMenu();
    }
    
    handleUpload(e) {
        e.stopPropagation();
        const uploadPath = this.contextTargetType === 'folder' ? this.contextTargetPath : this.currentPath;
        this.openUploadModal(uploadPath);
        this.hideContextMenu();
    }
    
    async handleDelete(e) {
        e.stopPropagation();
        if (!this.contextTargetPath) return;
        
        const confirmMsg = `确定要删除此${this.contextTargetType === 'folder' ? '文件夹' : '文件'}吗？\n${this.contextTargetPath}`;
        if (!confirm(confirmMsg)) return;
        
        try {
            const response = await fetch('/api/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    path: this.contextTargetPath, 
                    type: this.contextTargetType 
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('删除成功');
                this.refreshDirectory();
            } else {
                throw new Error(data.error || '删除失败');
            }
            
        } catch (error) {
            this.showError('删除失败: ' + error.message);
        }
        
        this.hideContextMenu();
    }
    
    // 上传处理
    openUploadModal(path) {
        this.uploadTargetPath = path;
        document.getElementById('upload-modal').style.display = 'flex';
        document.getElementById('upload-status').textContent = '';
        document.getElementById('upload-form').reset();
        this.updateDropAreaText();
    }
    
    closeUploadModal() {
        document.getElementById('upload-modal').style.display = 'none';
    }
    
    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.style.background = '#e0e0e0';
        e.currentTarget.style.borderColor = '#007bff';
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        e.currentTarget.style.background = '';
        e.currentTarget.style.borderColor = '#aaa';
    }
    
    handleDrop(e) {
        e.preventDefault();
        const dropArea = e.currentTarget;
        dropArea.style.background = '';
        dropArea.style.borderColor = '#aaa';
        
        const files = e.dataTransfer.files;
        document.getElementById('upload-input').files = files;
        this.updateDropAreaText();
    }
    
    updateDropAreaText() {
        const files = document.getElementById('upload-input').files;
        const dropArea = document.getElementById('drop-area');
        
        if (files.length > 0) {
            dropArea.textContent = `已选择 ${files.length} 个文件`;
        } else {
            dropArea.textContent = '拖拽文件到此处或点击选择文件';
        }
    }
    
    async handleUploadSubmit(e) {
        e.preventDefault();
        
        const files = document.getElementById('upload-input').files;
        if (!files.length) {
            this.showError('请选择文件');
            return;
        }
        
        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }
        
        const statusEl = document.getElementById('upload-status');
        statusEl.textContent = '上传中...';
        
        try {
            const response = await fetch(`/api/upload?path=${encodeURIComponent(this.uploadTargetPath)}`, {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                statusEl.textContent = `上传成功: ${data.files.join(', ')}`;
                setTimeout(() => {
                    this.closeUploadModal();
                    this.refreshDirectory();
                }, 1000);
            } else {
                throw new Error(data.error || '上传失败');
            }
            
        } catch (error) {
            statusEl.textContent = '上传失败: ' + error.message;
        }
    }
    
    // 工具栏功能
    changeSortType(sortType) {
        this.sortType = sortType;
        this.refreshDirectory();
    }
    
    async showCacheStats() {
        try {
            const response = await fetch('/api/cache_stats');
            const stats = await response.json();
            
            alert(`缓存统计:\n` +
                  `当前缓存: ${stats.cache_size}/${stats.max_size}\n` +
                  `最大预览大小: ${this.formatFileSize(stats.max_preview_size)}\n` +
                  `前端缓存: ${this.previewCache.size}/${this.maxCacheSize}`);
                  
        } catch (error) {
            this.showError('获取缓存统计失败: ' + error.message);
        }
    }
    
    async clearCache() {
        if (!confirm('确定要清理所有缓存吗？')) return;
        
        try {
            const response = await fetch('/api/clear_cache', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.previewCache.clear();
                this.showSuccess('缓存已清理');
            } else {
                throw new Error(data.error || '清理失败');
            }
            
        } catch (error) {
            this.showError('清理缓存失败: ' + error.message);
        }
    }
    
    // 刷新目录
    async refreshDirectory() {
        await this.loadDirectory(this.currentPath);
    }
    
    // 工具方法
    escapeHtml(text) {
        const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
    
    showLoading(message) {
        console.log('Loading:', message);
        // 可以添加加载指示器
    }
    
    hideLoading() {
        console.log('Loading complete');
        // 隐藏加载指示器
    }
    
    showError(message) {
        alert('错误: ' + message);
        console.error(message);
    }
    
    showSuccess(message) {
        console.log('Success:', message);
        // 可以添加成功提示
    }
}

// 全局实例
let fileBrowserManager;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    fileBrowserManager = new FileBrowserManager();
});

// 兼容性函数（保持向后兼容）
function refreshFileTree() {
    if (fileBrowserManager) {
        fileBrowserManager.refreshDirectory();
    }
}

function previewFile(path) {
    if (fileBrowserManager) {
        fileBrowserManager.previewFile(decodeURIComponent(path));
    }
}

function closePreview() {
    if (fileBrowserManager) {
        fileBrowserManager.closePreview();
    }
}

function openUploadModal(path) {
    if (fileBrowserManager) {
        fileBrowserManager.openUploadModal(path);
    }
}

function closeUploadModal() {
    if (fileBrowserManager) {
        fileBrowserManager.closeUploadModal();
    }
}
