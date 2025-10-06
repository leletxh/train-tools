# -*- coding: utf-8 -*-
"""
代理路由（TensorBoard代理）
"""

from flask import Blueprint, request, Response
from app.auth import login_required
import requests
import logging

proxy_bp = Blueprint('proxy', __name__, url_prefix='/proxy')

# TensorBoard管理器实例（将在初始化时设置）
tensorboard_manager = None


def init_proxy_services(tb_manager):
    """初始化代理服务"""
    global tensorboard_manager
    tensorboard_manager = tb_manager


@proxy_bp.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
@proxy_bp.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
@login_required
def proxy(path):
    """TensorBoard代理路由"""
    try:
        if not tensorboard_manager or not tensorboard_manager.is_running:
            return "TensorBoard is not running.", 404

        # 获取TensorBoard URL
        target_url = tensorboard_manager.get_url()
        if not target_url:
            return "TensorBoard URL not available.", 404

        # 完整构建目标 URL，保留原始查询参数
        full_target_url = f"{target_url}/{path}"
        if request.query_string:
            full_target_url += f"?{request.query_string.decode('utf-8')}"

        # 准备请求参数
        headers = {
            key: value for (key, value) in request.headers if key.lower() != 'host'
        }

        data = request.get_data()
        cookies = request.cookies

        # 发送请求
        resp = requests.request(
            method=request.method,
            url=full_target_url,
            headers=headers,
            data=data,
            cookies=cookies,
            allow_redirects=False,
            timeout=30  # 防止超时挂起
        )

        # 构造响应头
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        response_headers = [
            (name, value) for (name, value) in resp.raw.headers.items()
            if name.lower() not in excluded_headers
        ]

        return Response(resp.content, status=resp.status_code, headers=response_headers)

    except requests.exceptions.RequestException as e:
        logging.error(f"代理请求失败: {str(e)}", exc_info=True)
        return f"Proxy request failed: {str(e)}", 502
    
    except Exception as e:
        logging.error(f"代理服务错误: {str(e)}", exc_info=True)
        return f"Proxy service error: {str(e)}", 500
