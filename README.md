# 训练工具

本项目是一个基于 Web 的文件树管理工具，支持GPU、CPU使用查看文件/文件夹的浏览、预览、上传、下载、删除等常用操作，日志显示，TB映射

## 功能特性
- 通过可视化图标展示GPU、CPU使用情况
- 快速查看日志
- 文件类型智能预览（文本、图片、视频等）
- 右键菜单支持文件/文件夹的下载、上传、删除
- TB映射，只需映射一个端口

## 使用方法
1. 启动后端服务
2. 访问 `http://<host>:<post>/` 

## 主要文件说明
- `templates/main.html`：前端主页面，GPU、CPU使用情况以及其他服务
- `templates/log.html`：日志页面，显示日志
- `templates/tree.html`：文件查看下载
- `__main__.py`：后端服务入口

## 运行环境
- Python 3.8 以上
- 需要安装flask、flask_socketio、psutil、GPUtil、requests

## 许可协议
MIT License
