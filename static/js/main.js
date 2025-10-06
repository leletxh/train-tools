// 性能监控页面的JavaScript代码
var max_memory = 0;
var max_gpu_memory = 0;
var max_save_memory = 0;
var dataLen = 20;

var cpuData = Array(dataLen).fill(0);
var memoryData = Array(dataLen).fill(0);
// GPU和显存数据支持多卡
var gpuData = Array(dataLen).fill(null).map(() => []);
var gpuMemoryData = Array(dataLen).fill(null).map(() => []);
var gpuCount = 1; // 默认1，后续根据数据动态调整
var timeData = Array.from({length: dataLen}, (_, i) => {
    var now = new Date();
    now.setSeconds(now.getSeconds() - (dataLen - i - 1));
    return now.toLocaleTimeString();
});

var cpuChart, memoryChart, gpuChart, gpuMemoryChart, diskChart;

function initCharts() {
    cpuChart = echarts.init(document.getElementById('cpu'));
    memoryChart = echarts.init(document.getElementById('memory'));
    gpuChart = echarts.init(document.getElementById('gpu'));
    gpuMemoryChart = echarts.init(document.getElementById('gpu_memory'));
    diskChart = echarts.init(document.getElementById('disk'));

    var cpuOption = {
        title: { text: 'CPU使用率' },
        tooltip: { trigger: 'axis' },
        legend: { data: ['CPU使用率(%)'] },
        xAxis: { type: 'category', data: timeData },
        yAxis: { type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value} %' } },
        series: [{ name: 'CPU使用率(%)', type: 'line', data: cpuData, smooth: true }]
    };
    cpuChart.setOption(cpuOption);

    var memoryOption = {
        title: { text: '内存使用量(GB)' },
        tooltip: { trigger: 'axis' },
        legend: { data: ['内存使用量(GB)'] },
        xAxis: { type: 'category', data: timeData },
        yAxis: { type: 'value', min: 0, max: max_memory, axisLabel: { formatter: '{value} GB' } },
        series: [{ name: '内存使用量(GB)', type: 'line', data: memoryData, smooth: true }]
    };
    memoryChart.setOption(memoryOption);

    var gpuOption = {
        title: { text: 'GPU使用率' },
        tooltip: { trigger: 'axis' },
        legend: { data: ['GPU使用率(%)'] },
        xAxis: { type: 'category', data: timeData },
        yAxis: { type: 'value', min: 0, max: 100, axisLabel: { formatter: '{value} %' } },
        series: [{ name: 'GPU使用率(%)', type: 'line', data: gpuData, smooth: true }]
    };
    gpuChart.setOption(gpuOption);

    var gpuMemoryOption = {
        title: { text: '显存使用量(GB)' },
        tooltip: { trigger: 'axis' },
        legend: { data: ['显存使用量(GB)'] },
        xAxis: { type: 'category', data: timeData },
        yAxis: { type: 'value', min: 0, max: max_gpu_memory, axisLabel: { formatter: '{value} GB' } },
        series: [{ name: '显存使用量(GB)', type: 'line', data: gpuMemoryData, smooth: true }]
    };
    gpuMemoryChart.setOption(gpuMemoryOption);

    var diskOption = {
        title: { text: '磁盘空间', left: 'center' },
        tooltip: { trigger: 'item', formatter: '{b}: {c} GB ({d}%)' },
        legend: { orient: 'vertical', left: 'left', data: ['已用', '剩余'] },
        series: [
            {
                name: '磁盘空间',
                type: 'pie',
                radius: '60%',
                data: [
                    { value: 0, name: '已用' },
                    { value: 0, name: '剩余' }
                ],
                emphasis: {
                    itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' }
                },
                label: { formatter: '{b}: {c} GB ({d}%)' }
            }
        ]
    };
    diskChart.setOption(diskOption);
}

var socket;
var historyLoaded = false;

function initSocket() {
    socket = io();
    
    // 请求历史数据
    socket.emit('usage');
    
    // 历史数据加载
    socket.on('usage_history', function(msg) {
        if (historyLoaded) return;
        historyLoaded = true;
        var history = msg.data;
        if (history && history.length > 0) {
            cpuData = history.map(item => item.cpu);
            memoryData = history.map(item => item.memory);
            timeData = history.map(item => item.time);
            // 取最大GPU数量
            gpuCount = 0;
            history.forEach(item => {
                if (item.gpu && item.gpu.length > gpuCount) gpuCount = item.gpu.length;
            });
            // 初始化二维数组
            gpuData = Array(dataLen).fill(null).map(() => Array(gpuCount).fill(0));
            gpuMemoryData = Array(dataLen).fill(null).map(() => Array(gpuCount).fill(0));
            for (let i = 0; i < history.length; i++) {
                for (let j = 0; j < gpuCount; j++) {
                    gpuData[i][j] = (history[i].gpu && history[i].gpu[j] !== undefined) ? history[i].gpu[j] : 0;
                    gpuMemoryData[i][j] = (history[i].gpu_memory && history[i].gpu_memory[j] !== undefined) ? history[i].gpu_memory[j] : 0;
                }
            }
            while (cpuData.length < dataLen) {
                cpuData.unshift(0);
                memoryData.unshift(0);
                timeData.unshift('');
                gpuData.unshift(Array(gpuCount).fill(0));
                gpuMemoryData.unshift(Array(gpuCount).fill(0));
            }
            cpuChart.setOption({ xAxis: { data: timeData }, series: [{ data: cpuData }] });
            memoryChart.setOption({ xAxis: { data: timeData }, series: [{ data: memoryData }] });
            // 动态生成多GPU曲线
            var gpuSeries = [];
            var gpuLegend = [];
            for (let i = 0; i < gpuCount; i++) {
                gpuSeries.push({ name: 'GPU'+i+'使用率(%)', type: 'line', data: gpuData.map(row => row[i]), smooth: true });
                gpuLegend.push('GPU'+i+'使用率(%)');
            }
            gpuChart.setOption({
                xAxis: { data: timeData },
                legend: { data: gpuLegend },
                series: gpuSeries
            });
            var gpuMemSeries = [];
            var gpuMemLegend = [];
            for (let i = 0; i < gpuCount; i++) {
                gpuMemSeries.push({ name: 'GPU'+i+'显存(GB)', type: 'line', data: gpuMemoryData.map(row => row[i]), smooth: true });
                gpuMemLegend.push('GPU'+i+'显存(GB)');
            }
            gpuMemoryChart.setOption({
                xAxis: { data: timeData },
                legend: { data: gpuMemLegend },
                series: gpuMemSeries
            });
        }
    });
    
    // 实时数据更新
    socket.on('usage', function(data) {
        timeData.push(data.time); timeData.shift();
        cpuData.push(data.cpu); cpuData.shift();
        memoryData.push(data.memory); memoryData.shift();
        // 动态处理多GPU
        if (Array.isArray(data.gpu)) {
            gpuCount = Math.max(gpuCount, data.gpu.length);
            // 补全
            let gpuArr = data.gpu.slice();
            while (gpuArr.length < gpuCount) gpuArr.push(0);
            gpuData.push(gpuArr); gpuData.shift();
        }
        if (Array.isArray(data.gpu_memory)) {
            let gpuMemArr = data.gpu_memory.slice();
            while (gpuMemArr.length < gpuCount) gpuMemArr.push(0);
            gpuMemoryData.push(gpuMemArr); gpuMemoryData.shift();
        }
        // 更新图表
        cpuChart.setOption({ xAxis: { data: timeData }, series: [{ data: cpuData }] });
        memoryChart.setOption({ xAxis: { data: timeData }, series: [{ data: memoryData }] });
        var gpuSeries = [];
        var gpuLegend = [];
        for (let i = 0; i < gpuCount; i++) {
            gpuSeries.push({ name: 'GPU'+i+'使用率(%)', type: 'line', data: gpuData.map(row => row[i]), smooth: true });
            gpuLegend.push('GPU'+i+'使用率(%)');
        }
        gpuChart.setOption({
            xAxis: { data: timeData },
            legend: { data: gpuLegend },
            series: gpuSeries
        });
        var gpuMemSeries = [];
        var gpuMemLegend = [];
        for (let i = 0; i < gpuCount; i++) {
            gpuMemSeries.push({ name: 'GPU'+i+'显存(GB)', type: 'line', data: gpuMemoryData.map(row => row[i]), smooth: true });
            gpuMemLegend.push('GPU'+i+'显存(GB)');
        }
        gpuMemoryChart.setOption({
            xAxis: { data: timeData },
            legend: { data: gpuMemLegend },
            series: gpuMemSeries
        });
        // 更新磁盘空间饼图
        if (typeof data.save_memory !== 'undefined') {
            var free = data.save_memory;
            var used = max_save_memory - free;
            if (used < 0) used = 0;
            diskChart.setOption({
                series: [{
                    data: [
                        { value: used, name: '已用' },
                        { value: free, name: '剩余' }
                    ]
                }]
            });
        }
    });
    
    // 监听磁盘空间数据
    socket.on('disk', function(data) {
        var used = data.used || 0;
        var free = data.free || 0;
        diskChart.setOption({
            series: [{
                data: [
                    { value: used, name: '已用' },
                    { value: free, name: '可用' }
                ]
            }]
        });
    });
}

function openTab(evt, tabName) {
    // 声明所有变量
    var i, tabcontent, tablinks;

    // 使用 class="tabcontent" 获取所有元素并隐藏它们
    tabcontent = document.getElementsByClassName("tabcontent");
    for (i = 0; i < tabcontent.length; i++) {
        // 暂停当前动画
        tabcontent[i].style.animation = 'none';
        tabcontent[i].style.display = "none";
        tabcontent[i].classList.remove("fade-in");
    }

    // 获取所有带有 class="tablinks" 的元素并删除类 "active"
    tablinks = document.getElementsByClassName("tablinks");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }

    // 显示当前选项卡，并添加"活动"选项卡 类到打开选项卡的按钮
    var currentTab = document.getElementById(tabName);
    currentTab.style.display = "block";
    // 强制重排以确保display设置生效
    currentTab.offsetHeight;
    currentTab.classList.add("fade-in");
    evt.currentTarget.className += " active";
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 获取系统配置信息
    fetch('/api/config')
        .then(response => response.json())
        .then(config => {
            max_memory = config.max_memory;
            max_gpu_memory = config.max_gpu_memory;
            max_save_memory = config.max_save_memory;
            
            // 初始化图表
            initCharts();
            
            // 初始化WebSocket连接
            initSocket();
        });
});
