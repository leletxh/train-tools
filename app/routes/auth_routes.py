# -*- coding: utf-8 -*-
"""
认证相关路由
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, make_response
from app.auth import user_manager, login_required, admin_required, get_current_user

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面和处理"""
    if request.method == 'GET':
        # 如果已经登录，重定向到主页
        if get_current_user():
            return redirect(url_for('main.index'))
        return render_template('login.html')
    
    # POST请求处理登录
    username = request.form.get('username')
    password = request.form.get('password')
    
    if not username or not password:
        return render_template('login.html', error='请输入用户名和密码')
    
    # 验证用户
    user = user_manager.authenticate(username, password)
    if not user:
        return render_template('login.html', error='用户名或密码错误')
    
    # 创建会话
    session_id = user_manager.create_session(username)
    
    # 设置cookie并重定向
    response = make_response(redirect(url_for('main.index')))
    response.set_cookie('session_id', session_id, max_age=24*60*60, httponly=True)  # 24小时
    
    return response


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """登出"""
    session_id = request.cookies.get('session_id')
    if session_id:
        user_manager.logout(session_id)
    
    response = make_response(redirect(url_for('auth.login')))
    response.set_cookie('session_id', '', expires=0)
    return response


@auth_bp.route('/api/user/info')
@login_required
def user_info():
    """获取当前用户信息"""
    user = get_current_user()
    return jsonify({
        'username': user.username,
        'is_admin': user.is_admin,
        'created_at': user.created_at,
        'last_login': user.last_login
    })


@auth_bp.route('/api/users')
@admin_required
def list_users():
    """列出所有用户（仅管理员）"""
    user = get_current_user()
    users = user_manager.list_users(user.username)
    return jsonify({'users': users})


@auth_bp.route('/api/users', methods=['POST'])
@admin_required
def create_user():
    """创建新用户（仅管理员）"""
    user = get_current_user()
    new_user = user_manager.create_user(user.username)
    
    if new_user:
        return jsonify({
            'success': True,
            'user': new_user,
            'message': '用户创建成功'
        })
    else:
        return jsonify({
            'success': False,
            'message': '用户创建失败'
        }), 400


@auth_bp.route('/api/users/<username>', methods=['DELETE'])
@admin_required
def delete_user(username):
    """删除用户（仅管理员）"""
    user = get_current_user()
    success = user_manager.delete_user(user.username, username)
    
    if success:
        return jsonify({
            'success': True,
            'message': '用户删除成功'
        })
    else:
        return jsonify({
            'success': False,
            'message': '用户删除失败'
        }), 400


@auth_bp.route('/admin')
@admin_required
def admin_panel():
    """管理员面板"""
    return render_template('admin.html')
