# -*- coding: utf-8 -*-
"""
认证中间件和装饰器
"""

from functools import wraps
from flask import request, redirect, url_for, jsonify, g
from app.models import UserManager

# 全局用户管理器实例
user_manager = UserManager()


def init_auth():
    """初始化认证系统"""
    # 清理过期会话
    user_manager.cleanup_expired_sessions()
    return user_manager


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 从cookie中获取session_id
        session_id = request.cookies.get('session_id')
        
        if not session_id:
            # 如果是API请求，返回JSON错误
            if request.path.startswith('/api/'):
                return jsonify({'error': '未登录', 'code': 401}), 401
            # 否则重定向到登录页
            return redirect(url_for('auth.login'))
        
        # 验证会话
        user = user_manager.get_user_by_session(session_id)
        if not user:
            # 如果是API请求，返回JSON错误
            if request.path.startswith('/api/'):
                return jsonify({'error': '会话已过期', 'code': 401}), 401
            # 否则重定向到登录页
            return redirect(url_for('auth.login'))
        
        # 将用户信息存储到g对象中
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 首先检查是否已登录
        session_id = request.cookies.get('session_id')
        if not session_id:
            if request.path.startswith('/api/'):
                return jsonify({'error': '未登录', 'code': 401}), 401
            return redirect(url_for('auth.login'))
        
        user = user_manager.get_user_by_session(session_id)
        if not user:
            if request.path.startswith('/api/'):
                return jsonify({'error': '会话已过期', 'code': 401}), 401
            return redirect(url_for('auth.login'))
        
        # 检查是否为管理员
        if not user.is_admin:
            if request.path.startswith('/api/'):
                return jsonify({'error': '权限不足', 'code': 403}), 403
            return jsonify({'error': '权限不足'}), 403
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user():
    """获取当前登录用户"""
    session_id = request.cookies.get('session_id')
    if session_id:
        return user_manager.get_user_by_session(session_id)
    return None


def is_authenticated():
    """检查是否已认证"""
    return get_current_user() is not None


def is_admin():
    """检查是否为管理员"""
    user = get_current_user()
    return user and user.is_admin
