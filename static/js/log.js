const MAX_LINES = 500;

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
    const output = document.getElementById("output");
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
    output.innerHTML += html + '<br>';
    limitLines(output, MAX_LINES);
    output.scrollTop = output.scrollHeight;
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
                
                // 处理历史日志内容
                if (data.history.trim()) {
                    const lines = data.history.split('\n');
                    lines.forEach(line => {
                        if (line.trim()) {
                            const html = ansi_up.ansi_to_html(line);
                            output.innerHTML += html + '<br>';
                        }
                    });
                }
                
                // 添加分隔线
                const separator = "\x1b[44m\x1b[37m=== 实时日志 ===\x1b[0m";
                const separatorHtml = ansi_up.ansi_to_html(separator);
                output.innerHTML += separatorHtml + '<br>';
                
                limitLines(output, MAX_LINES);
                scrollToBottom();
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

// 检查是否需要加载历史日志
document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/config')
        .then(response => response.json())
        .then(config => {
            if (config.OPEN_HISTORY_LOG) {
                // 直接加载历史日志
                loadHistoryLog();
                
                // 保留原有的socket监听，用于接收实时日志
                socket.on('history_log', (msg) => {
                    const output = document.getElementById("output");
                    var ansi_up = new AnsiUp();
                    const html = ansi_up.ansi_to_html(msg.data);
                    output.innerHTML += html + '<br>';
                    limitLines(output, MAX_LINES);
                    scrollToBottom();
                });
            }
        })
        .catch(error => {
            console.error('获取配置失败:', error);
            // 即使配置获取失败，也尝试加载历史日志
            loadHistoryLog();
        });
});
