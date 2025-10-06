# 训练工具 (Training Tools)

一个基于 Flask 的机器学习训练监控和管理工具，提供实时系统监控、命令执行、文件管理和 TensorBoard 集成功能。

## 项目结构

```
训练工具/
├── app/                          # 应用核心模块
│   ├── __init__.py              # 应用工厂函数
│   ├── config.py                # 配置管理
│   ├── socketio_events.py       # SocketIO 事件处理
│   ├── routes/                  # 路由模块
│   │   ├── __init__.py         # 路由包初始化
│   │   ├── main_routes.py      # 主要页面路由
│   │   ├── api_routes.py       # API 路由
│   │   ├── file_routes.py      # 文件操作路由
│   │   └── proxy_routes.py     # TensorBoard 代理路由
│   └── utils/                   # 工具模块
│       ├── __init__.py         # 工具包初始化
│       ├── system_monitor.py   # 系统监控
│       ├── command_executor.py # 命令执行器
│       ├── tensorboard_manager.py # TensorBoard 管理
│       └── file_manager.py     # 文件管理器
├── static/                      # 静态资源
│   ├── css/                    # 样式文件
│   └── js/                     # JavaScript 文件
├── templates/                   # HTML 模板
├── test/                       # 测试文件
├── main.py                     # 主应用入口
├── __main__.py                 # 原始主文件（已重构）
├── requirements.txt            # 依赖管理
├── .gitignore                  # Git 忽略文件
└── README.md                   # 项目说明
```

## 功能特性

### 🖥️ 系统监控
- 实时 CPU、内存、GPU 使用率监控
- 磁盘空间监控
- 历史数据记录和图表展示

### 🚀 命令执行
- 支持训练命令的实时执行
- 命令输出实时流式显示
- 支持中文编码处理

### 📊 TensorBoard 集成
- 一键启动/停止 TensorBoard
- 内置代理服务，无需额外端口
- 自动日志目录管理

### 📁 文件管理
- 文件树浏览
- 文件预览（文本、图片、视频）
- 文件上传/下载
- 文件夹压缩下载

### 🌐 Web 界面
- 响应式设计
- 实时数据更新
- 直观的用户界面

## 安装和使用

### 环境要求
- Python 3.7+
- pip

### 安装依赖
```bash
pip install -r requirements.txt
```

### 启动应用
```bash
# 开发模式
python main.py --config development --port 5000

# 生产模式
python main.py --config production --port 5000
```

### 访问应用
打开浏览器访问：`http://localhost:5000`

## 配置说明

### 环境配置
- `development`: 开发环境，启用调试模式
- `production`: 生产环境，关闭调试模式

### 端口配置
使用 `--port` 参数指定端口号，默认为 5000

## API 接口

### 系统配置
- `GET /api/config` - 获取系统配置信息

### 训练管理
- `POST /api/start-training` - 启动训练配置

### 文件操作
- `GET /api/tree` - 获取文件树
- `GET /api/preview` - 预览文件
- `GET /api/download` - 下载文件
- `GET /api/download_folder` - 下载文件夹
- `POST /api/upload` - 上传文件
- `POST /api/delete` - 删除文件/文件夹

### TensorBoard 代理
- `/proxy/*` - TensorBoard 代理路由

## 开发说明

### 模块化设计
项目采用模块化设计，各功能模块独立：
- `utils/` - 核心功能工具类
- `routes/` - Web 路由处理
- `config.py` - 配置管理
- `socketio_events.py` - 实时通信

### 扩展开发
1. 添加新功能：在 `utils/` 目录创建新的工具类
2. 添加新路由：在 `routes/` 目录创建新的路由文件
3. 修改配置：在 `config.py` 中添加新的配置项

## 许可证

本项目采用开源许可证，具体请查看 LICENSE 文件。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进项目。

## 更新日志

### v2.0.0 (当前版本)
- 重构项目结构，采用模块化设计
- 分离业务逻辑和路由处理
- 改进代码组织和可维护性
- 添加配置管理系统
- 优化错误处理和日志记录
