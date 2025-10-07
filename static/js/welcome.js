// TensorBoard面板选项的显示/隐藏控制
document.getElementById('enable-panel').addEventListener('change', function() {
    const panelPathGroup = document.getElementById('panel-path-group');
    if (this.checked) {
        panelPathGroup.style.display = 'block';
    } else {
        panelPathGroup.style.display = 'none';
    }
});

// 表单提交处理
document.getElementById('config-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const command = document.getElementById('command').value.trim();
    const enablePanel = document.getElementById('enable-panel').checked;
    const panelPath = document.getElementById('panel-path').value.trim();
    
    // 简单验证
    if (!command) {
        showMessage('请输入训练命令', 'error');
        return;
    }
    
    if (enablePanel && !panelPath) {
        showMessage('请指定面板路径', 'error');
        return;
    }
    
    // 准备配置数据
    const config = {
        command: command,
        enablePanel: enablePanel,
        panelPath: panelPath || 'logs'
    };
    
    // 发送配置到服务器
    fetch('/api/start-training', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showMessage('配置已保存，正在启动训练...', 'success');
            // 延迟跳转到主页面
            setTimeout(() => {
                window.location.href = '/';
            }, 2000);
        } else {
            showMessage('启动失败: ' + (data.error || '未知错误'), 'error');
        }
    })
    .catch(error => {
        showMessage('网络错误: ' + error.message, 'error');
    });
});

// 显示消息函数
function showMessage(text, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = text;
    messageDiv.className = type + '-message';
}