# -*- coding: utf-8 -*-
"""
主要页面路由
"""

from flask import Blueprint, render_template
from app.config import Config
from app.auth import login_required, get_current_user

main_bp = Blueprint('main', __name__)

# 全局变量，用于跟踪配置状态
configured = False


@main_bp.route("/")
@login_required
def index():
    """主页路由"""
    # 如果未配置，则重定向到欢迎页
    if not configured:
        return render_template("welcome.html")
    return render_template("main.html")


@main_bp.route("/welcome")
def welcome():
    """欢迎页路由"""
    return render_template("welcome.html")


@main_bp.route("/log")
@login_required
def log():
    """日志页路由"""
    return render_template("log.html", OPEN_HISTORY_LOG=Config.OPEN_HISTORY_LOG)


@main_bp.route("/tree")
@login_required
def tree_page():
    """文件树页面路由"""
    return render_template("tree.html")


def set_configured(status):
    """设置配置状态"""
    global configured
    configured = status


def is_configured():
    """获取配置状态"""
    return configured
