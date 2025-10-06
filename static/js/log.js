const MAX_LINES = 500;

// 信息提取相关变量
let regexItems = [];
let currentValues = {}; // 当前显示的值
let nextItemId = 1;

function scrollToBottom() {
    const output = document.getElementById("output");
    output.scrollTop = output.scrollHeight;
}

function limitLines(element, maxLines) {
    const lines = element.innerHTML.split('<br>');
    if (lines.length > maxLines) {
        element.innerHTML = lines.slice(-maxLines).join('<br>');
    }
}

// 初始化 socket.io 连接
const socket = io();

socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('command_output', (msg) => {
    var ansi_up = new AnsiUp();
    ansi_up.use_classes = true;  // 使用CSS类而不是内联样式
    
    // 处理特殊字符和编码问题
    let data = msg.data;
    
    // 确保正确处理UTF-8字符
    try {
        if (typeof data === 'string') {
            // 替换常见的乱码字符
            data = data.replace(/\?/g, '?');
            // 确保进度条字符正确显示
            data = data.replace(/\u2588/g, '█');  // 完整块
            data = data.replace(/\u2591/g, '░');  // 浅阴影
            data = data.replace(/\u2592/g, '▒');  // 中等阴影
            data = data.replace(/\u2593/g, '▓');  // 深阴影
        }
    } catch (e) {
        console.log('字符处理错误:', e);
    }
    
    const html = ansi_up.ansi_to_html(data);
    processNewOutput(html, data);
});

// 加载历史日志
function loadHistoryLog() {
    fetch('/api/command_history')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.history) {
                const output = document.getElementById("output");
                var ansi_up = new AnsiUp();
                ansi_up.use_classes = true;
                
                // 清空当前内容
                output.innerHTML = '';
                
                // 添加历史日志标识
                const historyHeader = "\x1b[44m\x1b[37m=== 历史日志 ===\x1b[0m";
                const headerHtml = ansi_up.ansi_to_html(historyHeader);
                output.innerHTML += headerHtml + '<br>';
                
                // 处理历史日志内容，只加载最后50行
                if (data.history.trim()) {
                    const lines = data.history.split('\n').filter(line => line.trim());
                    // 只取最后50行
                    const lastLines = lines.slice(-50);
                    lastLines.forEach(line => {
                        const html = ansi_up.ansi_to_html(line);
                        output.innerHTML += html + '<br>';
                        // 对历史日志也进行信息提取
                        extractInfoFromLine(line);
                    });
                }
                
                // 添加分隔线
                const separator = "\x1b[44m\x1b[37m=== 实时日志 ===\x1b[0m";
                const separatorHtml = ansi_up.ansi_to_html(separator);
                output.innerHTML += separatorHtml + '<br>';
                
                limitLines(output, MAX_LINES);
                scrollToBottom();
                updateExtractedInfoTable();
            }
        })
        .catch(error => {
            console.error('加载历史日志失败:', error);
        });
}

// 清空历史日志
function clearHistoryLog() {
    if (confirm('确定要清空所有历史日志吗？此操作不可撤销。')) {
        fetch('/api/clear_command_history', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const output = document.getElementById("output");
                output.innerHTML = '';
                alert('历史日志已清空');
            } else {
                alert('清空历史日志失败: ' + data.error);
            }
        })
        .catch(error => {
            console.error('清空历史日志失败:', error);
            alert('清空历史日志失败');
        });
    }
}

// 正则匹配面板控制
function toggleRegexPanel() {
    const panel = document.getElementById('regexPanel');
    const btn = document.getElementById('regexToggleBtn');
    
    if (panel.style.display === 'none') {
        panel.style.display = 'block';
        btn.textContent = '隐藏信息提取';
        btn.classList.add('active');
    } else {
        panel.style.display = 'none';
        btn.textContent = '信息提取';
        btn.classList.remove('active');
    }
}

// 添加正则提取项
function addRegexItem(name = '', regex = '') {
    const itemId = nextItemId++;
    const item = {
        id: itemId,
        name: name || `项目${itemId}`,
        regex: regex,
        compiled: null,
        active: false
    };
    
    regexItems.push(item);
    renderRegexItems();
    updateTableHeaders();
    
    return item;
}

// 添加预设正则项
function addPresetRegex(type) {
    const presets = {
        'error': {
            name: '错误信息',
            regex: '(error|错误|失败|failed|exception|Error|ERROR)[:\\s]*([^\\n\\r]*)'
        },
        'warning': {
            name: '警告信息',
            regex: '(warning|warn|警告|注意|Warning|WARN)[:\\s]*([^\\n\\r]*)'
        },
        'progress': {
            name: '训练进度',
            regex: '(\\d+(?:\\.\\d+)?%)|(\\d+/\\d+)|进度[:\\s]*(\\d+(?:\\.\\d+)?%?)'
        },
        'epoch': {
            name: '训练轮次',
            regex: '(epoch|轮次|Epoch)[:\\s]*(\\d+)'
        },
        'loss': {
            name: '损失值',
            regex: '(loss|损失|Loss)[:\\s]*([0-9]+\\.?[0-9]*(?:[eE][+-]?[0-9]+)?)'
        },
        'accuracy': {
            name: '准确率',
            regex: '(accuracy|acc|准确率|Accuracy|ACC)[:\\s]*([0-9.]+%?)'
        }
    };
    
    if (presets[type]) {
        addRegexItem(presets[type].name, presets[type].regex);
    }
}

// 渲染正则项列表
function renderRegexItems() {
    const container = document.getElementById('regexItemsList');
    container.innerHTML = '';
    
    regexItems.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.className = 'regex-item';
        itemDiv.innerHTML = `
            <input type="text" class="item-name" value="${item.name}" 
                   onchange="updateRegexItem(${item.id}, 'name', this.value)" 
                   placeholder="项目名称">
            <input type="text" class="item-regex" value="${item.regex}" 
                   onchange="updateRegexItem(${item.id}, 'regex', this.value)" 
                   placeholder="正则表达式">
            <span class="item-status" id="status-${item.id}">
                ${item.active ? '已启用' : '未启用'}
            </span>
            <button onclick="toggleRegexItem(${item.id})" class="btn btn-small ${item.active ? 'btn-secondary' : 'btn-primary'}">
                ${item.active ? '停用' : '启用'}
            </button>
            <button onclick="removeRegexItem(${item.id})" class="btn btn-small btn-danger">删除</button>
        `;
        container.appendChild(itemDiv);
    });
}

// 更新正则项
function updateRegexItem(id, field, value) {
    const item = regexItems.find(item => item.id === id);
    if (item) {
        item[field] = value;
        if (field === 'regex' && item.active) {
            // 重新编译正则表达式
            try {
                item.compiled = new RegExp(value, 'gi');
                updateItemStatus(id, 'active');
            } catch (error) {
                item.compiled = null;
                item.active = false;
                updateItemStatus(id, 'error');
                console.error('正则表达式错误:', error);
            }
        }
        if (field === 'name') {
            updateTableHeaders();
        }
    }
}

// 切换正则项状态
function toggleRegexItem(id) {
    const item = regexItems.find(item => item.id === id);
    if (item) {
        if (item.active) {
            item.active = false;
            item.compiled = null;
        } else {
            try {
                item.compiled = new RegExp(item.regex, 'gi');
                item.active = true;
            } catch (error) {
                alert('正则表达式错误: ' + error.message);
                return;
            }
        }
        renderRegexItems();
        updateTableHeaders();
    }
}

// 删除正则项
function removeRegexItem(id) {
    regexItems = regexItems.filter(item => item.id !== id);
    renderRegexItems();
    updateTableHeaders();
    updateExtractedInfoTable();
}

// 更新项目状态显示
function updateItemStatus(id, status) {
    const statusElement = document.getElementById(`status-${id}`);
    if (statusElement) {
        statusElement.className = `item-status ${status}`;
        switch (status) {
            case 'active':
                statusElement.textContent = '已启用';
                break;
            case 'error':
                statusElement.textContent = '错误';
                break;
            default:
                statusElement.textContent = '未启用';
        }
    }
}

// 更新表格头部
function updateTableHeaders() {
    const headerRow = document.getElementById('tableHeader');
    if (!headerRow) return;
    
    headerRow.innerHTML = '<th class="timestamp">最新更新时间</th>';
    
    regexItems.forEach(item => {
        const th = document.createElement('th');
        th.textContent = item.name;
        headerRow.appendChild(th);
    });
    
    // 表格面板始终显示，预留位置
    const infoPanel = document.getElementById('extractedInfoPanel');
    infoPanel.style.display = 'block';
    updateExtractedInfoTable();
}

// 处理新输出
function processNewOutput(html, rawText) {
    const output = document.getElementById("output");
    output.innerHTML += html + '<br>';
    
    // 提取信息
    extractInfoFromLine(rawText);
    
    limitLines(output, MAX_LINES);
    output.scrollTop = output.scrollHeight;
}

// 从日志行中提取信息
function extractInfoFromLine(line) {
    if (!line || !line.trim()) return;
    
    const activeItems = regexItems.filter(item => item.active && item.compiled);
    if (activeItems.length === 0) return;
    
    let hasMatch = false;
    let lastUpdateTime = null;
    
    activeItems.forEach(item => {
        const matches = line.match(item.compiled);
        if (matches) {
            // 提取匹配的值，优先使用捕获组
            let value = matches[0];
            if (matches.length > 1) {
                // 找到第一个非空的捕获组
                for (let i = 1; i < matches.length; i++) {
                    if (matches[i] && matches[i].trim()) {
                        value = matches[i].trim();
                        break;
                    }
                }
            }
            currentValues[item.id] = value;
            lastUpdateTime = new Date().toLocaleTimeString();
            hasMatch = true;
        }
    });
    
    if (hasMatch) {
        currentValues.lastUpdateTime = lastUpdateTime;
        updateExtractedInfoTable();
    }
}

// 更新提取信息表格
function updateExtractedInfoTable() {
    const tbody = document.getElementById('tableBody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    // 只显示一行数据
    const tr = document.createElement('tr');
    
    // 时间列
    const timestampTd = document.createElement('td');
    timestampTd.className = 'timestamp';
    timestampTd.textContent = currentValues.lastUpdateTime || '-';
    tr.appendChild(timestampTd);
    
    // 数据列
    regexItems.forEach(item => {
        const td = document.createElement('td');
        td.className = 'value';
        td.textContent = currentValues[item.id] || '-';
        td.title = currentValues[item.id] || '';
        tr.appendChild(td);
    });
    
    tbody.appendChild(tr);
}

// 清空提取的信息
function clearExtractedInfo() {
    currentValues = {};
    updateExtractedInfoTable();
}

// 键盘事件处理
document.addEventListener('keydown', function(event) {
    // Ctrl+F 快捷键打开正则面板
    if (event.ctrlKey && event.key === 'f') {
        event.preventDefault();
        toggleRegexPanel();
    }
});

// 检查是否需要加载历史日志
document.addEventListener('DOMContentLoaded', function() {
    // 初始化表格显示
    const infoPanel = document.getElementById('extractedInfoPanel');
    if (infoPanel) {
        infoPanel.style.display = 'block';
    }
    updateTableHeaders();
    
    fetch('/api/config')
        .then(response => response.json())
        .then(config => {
            if (config.OPEN_HISTORY_LOG) {
                // 直接加载历史日志
                loadHistoryLog();
                
                // 保留原有的socket监听，用于接收实时日志
                socket.on('history_log', (msg) => {
                    var ansi_up = new AnsiUp();
                    const html = ansi_up.ansi_to_html(msg.data);
                    processNewOutput(html, msg.data);
                });
            }
        })
        .catch(error => {
            console.error('获取配置失败:', error);
            // 即使配置获取失败，也尝试加载历史日志
            loadHistoryLog();
        });
});
