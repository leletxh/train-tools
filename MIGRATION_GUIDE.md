# 项目结构迁移指南

本指南帮助您从旧的单文件结构迁移到新的模块化结构。

## 迁移概述

### 旧结构 → 新结构对比

| 旧文件 | 新位置 | 说明 |
|--------|--------|------|
| `__main__.py` | `main.py` + `app/` 模块 | 主文件重构为模块化结构 |
| 所有功能在一个文件 | 分散到多个模块 | 按功能分离到不同模块 |

### 新的模块化结构

```
app/
├── __init__.py              # 应用工厂
├── config.py                # 配置管理
├── socketio_events.py       # SocketIO 事件
├── routes/                  # 路由模块
│   ├── main_routes.py      # 页面路由
│   ├── api_routes.py       # API 路由
│   ├── file_routes.py      # 文件操作
│   └── proxy_routes.py     # 代理路由
└── utils/                   # 工具模块
    ├── system_monitor.py   # 系统监控
    ├── command_executor.py # 命令执行
    ├── tensorboard_manager.py # TensorBoard
    └── file_manager.py     # 文件管理
```

## 功能迁移对照

### 1. 系统监控功能
**旧代码位置**: `__main__.py` 中的 `get_usage()` 函数
**新位置**: `app/utils/system_monitor.py` 中的 `SystemMonitor` 类

### 2. 命令执行功能
**旧代码位置**: `__main__.py` 中的 `run_command()` 和 `emit_output()` 函数
**新位置**: `app/utils/command_executor.py` 中的 `CommandExecutor` 类

### 3. TensorBoard 管理
**旧代码位置**: `__main__.py` 中的 TensorBoard 相关代码
**新位置**: `app/utils/tensorboard_manager.py` 中的 `TensorBoardManager` 类

### 4. 文件管理功能
**旧代码位置**: `__main__.py` 中的文件操作函数
**新位置**: `app/utils/file_manager.py` 中的 `FileManager` 类

### 5. 路由处理
**旧代码位置**: `__main__.py` 中的 Flask 路由装饰器
**新位置**: `app/routes/` 目录下的各个路由文件

## 启动方式变更

### 旧启动方式
```bash
python __main__.py --port 5000
```

### 新启动方式
```bash
# 开发模式
python main.py --config development --port 5000

# 生产模式  
python main.py --config production --port 5000
```

## 配置管理变更

### 旧配置方式
配置直接写在 `__main__.py` 文件中的全局变量

### 新配置方式
统一在 `app/config.py` 中管理：
- `DevelopmentConfig` - 开发环境配置
- `ProductionConfig` - 生产环境配置

## 依赖管理

### 新增文件
- `requirements.txt` - 依赖包管理
- `README.md` - 项目说明文档
- `MIGRATION_GUIDE.md` - 本迁移指南

## 兼容性说明

### 保持兼容的部分
- 所有 API 接口保持不变
- 前端页面和功能完全兼容
- 数据格式和通信协议不变

### 改进的部分
- 更好的错误处理和日志记录
- 模块化设计，便于维护和扩展
- 配置管理更加灵活
- 代码结构更清晰

## 开发建议

### 1. 添加新功能
- 在 `app/utils/` 中创建新的工具类
- 在 `app/routes/` 中添加新的路由处理

### 2. 修改现有功能
- 找到对应的模块文件进行修改
- 避免在多个文件中重复代码

### 3. 配置修改
- 在 `app/config.py` 中添加新的配置项
- 使用环境变量管理敏感配置

## 故障排除

### 常见问题

1. **导入错误**
   - 确保所有 `__init__.py` 文件存在
   - 检查模块导入路径是否正确

2. **配置问题**
   - 检查 `app/config.py` 中的配置是否正确
   - 确认启动时指定了正确的配置环境

3. **依赖问题**
   - 运行 `pip install -r requirements.txt` 安装依赖
   - 检查 Python 版本是否符合要求

### 回滚方案
如果新结构出现问题，可以临时使用原始的 `__main__.py` 文件：
```bash
python __main__.py --port 5000
```

## 总结

新的模块化结构带来以下优势：
- ✅ 代码组织更清晰
- ✅ 功能模块独立，便于测试
- ✅ 配置管理更灵活
- ✅ 便于团队协作开发
- ✅ 更好的可维护性和扩展性

建议在充分测试后完全迁移到新结构，并删除旧的 `__main__.py` 文件。
