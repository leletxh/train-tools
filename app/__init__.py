# -*- coding: utf-8 -*-
"""
训练工具 Flask 应用初始化模块
"""

from flask import Flask
from flask_socketio import SocketIO

def create_app():
    """创建并配置 Flask 应用"""
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    app.secret_key = 'your_secret_key_here'
    app.config['JSON_AS_ASCII'] = False
    
    # 初始化 SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
    
    return app, socketio
