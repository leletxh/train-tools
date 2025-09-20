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

// 检查是否需要加载历史日志
document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/config')
        .then(response => response.json())
        .then(config => {
            if (config.OPEN_HISTORY_LOG) {
                socket.on('history_log', (msg) => {
                    const output = document.getElementById("output");
                    var ansi_up = new AnsiUp();
                    const html = ansi_up.ansi_to_html(msg.data + "\x1b[44m\x1b[37m*\x1b[0m上方历史日志");
                    output.innerHTML += html + '<br>';
                    limitLines(output, MAX_LINES);
                    output.scrollTop = output.scrollHeight;
                });
            }
        });
});
