# -*- coding: utf-8 -*-
"""
训练工具主应用程序
"""

import os
import sys
import signal
import logging
import argparse
from threading import Thread

from flask_socketio import SocketIO
from app import create_app
from app.config import config
from app.routes import main_bp, api_bp, file_bp, proxy_bp, auth_bp
from app.routes.api_routes import init_api_services
from app.routes.proxy_routes import init_proxy_services
from app.socketio_events import init_socketio_events
from app.utils import SystemMonitor, CommandExecutor, TensorBoardManager


def setup_logging():
    """配置日志系统"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="训练工具")
    parser.add_argument("--port", type=str, help="端口号", default="5000")
    parser.add_argument("--user_mt", type=str, help="用户权限系统开关", default="true")
    parser.add_argument("--config", type=str, help="配置环境", 
                       choices=['development', 'production'], default='development')
    return parser.parse_args()


def create_application(config_name='development'):
    """创建并配置应用"""
    # 创建Flask应用和SocketIO
    app, socketio = create_app()
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 注册蓝图
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(file_bp)
    app.register_blueprint(proxy_bp)
    app.register_blueprint(auth_bp)
    
    return app, socketio


def initialize_services(socketio):
    """初始化各种服务"""
    # 初始化认证系统
    from app.auth import init_auth
    user_manager = init_auth()
    
    # 初始化API服务
    init_api_services(socketio)
    
    # 获取服务实例
    from app.routes.api_routes import system_monitor, command_executor, tensorboard_manager
    
    # 初始化代理服务
    init_proxy_services(tensorboard_manager)
    
    # 初始化SocketIO事件
    init_socketio_events(socketio, command_executor, system_monitor)
    
    return system_monitor, command_executor, tensorboard_manager


def setup_signal_handlers(system_monitor, tensorboard_manager):
    """设置信号处理器"""
    def handle_exit(signum, frame):
        logging.info("正在优雅关闭应用...")
        
        # 停止系统监控
        if system_monitor:
            system_monitor.stop_monitoring()
        
        # 停止TensorBoard
        if tensorboard_manager:
            tensorboard_manager.stop_tensorboard()
        
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)


def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    # 解析参数
    args = parse_arguments()
    
    # 创建应用
    app, socketio = create_application(args.config)
    
    # 初始化服务
    system_monitor, command_executor, tensorboard_manager = initialize_services(socketio)
    
    # 设置信号处理器
    setup_signal_handlers(system_monitor, tensorboard_manager)
    
    # 启动应用
    logging.info("训练工具应用启动中...")
    try:
        socketio.run(app, port=int(args.port), debug=(args.config == 'development'))
    except Exception as e:
        logging.error(f"应用启动失败: {str(e)}", exc_info=True)
    finally:
        # 清理资源
        if system_monitor:
            system_monitor.stop_monitoring()
        if tensorboard_manager:
            tensorboard_manager.stop_tensorboard()


if __name__ == "__main__":
    main()
