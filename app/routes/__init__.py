# -*- coding: utf-8 -*-
"""
路由模块包
"""

from .main_routes import main_bp
from .api_routes import api_bp
from .file_routes import file_bp
from .proxy_routes import proxy_bp
from .auth_routes import auth_bp

__all__ = [
    'main_bp',
    'api_bp', 
    'file_bp',
    'proxy_bp',
    'auth_bp'
]
