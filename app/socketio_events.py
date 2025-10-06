# -*- coding: utf-8 -*-
"""
SocketIO 事件处理模块
"""

from flask_socketio import emit
import logging

# 全局实例（将在应用初始化时设置）
command_executor = None
system_monitor = None


def init_socketio_events(socketio, cmd_executor, sys_monitor):
    """初始化SocketIO事件处理"""
    global command_executor, system_monitor
    command_executor = cmd_executor
    system_monitor = sys_monitor
    
    # 注册事件处理器
    socketio.on_event('connect', handle_connect)
    socketio.on_event('usage', usage_connect)


def handle_connect():
    """处理客户端连接事件"""
    try:
        if command_executor:
            history = command_executor.get_command_history()
            emit('history_log', {'data': history})
        logging.info("客户端已连接")
    except Exception as e:
        logging.error(f"处理连接事件失败: {str(e)}", exc_info=True)


def usage_connect():
    """处理系统使用情况连接事件"""
    try:
        if system_monitor:
            history = system_monitor.get_history()
            emit('usage_history', {'data': history})
        logging.info("系统监控数据已发送")
    except Exception as e:
        logging.error(f"处理使用情况连接事件失败: {str(e)}", exc_info=True)
