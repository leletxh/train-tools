# -*- coding: utf-8 -*-
"""
文件操作路由
"""

from flask import Blueprint, request, jsonify
from app.utils import FileManager
from app.auth import login_required
import logging

file_bp = Blueprint('file', __name__, url_prefix='/api')

# 文件管理器实例
file_manager = FileManager()


@file_bp.route('/download')
@login_required
def api_download():
    """下载文件"""
    try:
        path = request.args.get('path')
        if not path:
            return 'No path', 400
        
        result, error, status_code = file_manager.download_file(path)
        
        if error:
            return error, status_code
        
        return result
        
    except Exception as e:
        logging.error(f"文件下载失败: {str(e)}", exc_info=True)
        return str(e), 500


@file_bp.route('/download_folder')
@login_required
def api_download_folder():
    """下载文件夹"""
    try:
        path = request.args.get('path')
        if not path:
            return 'No path', 400
        
        result, error, status_code = file_manager.download_folder(path)
        
        if error:
            return error, status_code
        
        return result
        
    except Exception as e:
        logging.error(f"文件夹下载失败: {str(e)}", exc_info=True)
        return str(e), 500


@file_bp.route('/upload', methods=['POST'])
@login_required
def api_upload():
    """上传文件"""
    try:
        path = request.args.get('path', '.')  # 默认为当前目录
        files = request.files.getlist('files')
        
        result = file_manager.upload_files(files, path)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logging.error(f"文件上传失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@file_bp.route('/delete', methods=['POST'])
@login_required
def api_delete():
    """删除文件或文件夹"""
    try:
        data = request.get_json()
        path = data.get('path')
        file_type = data.get('type')
        
        if not path:
            return jsonify(success=False, error='缺少路径'), 400
        
        result = file_manager.delete_file_or_folder(path, file_type)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logging.error(f"删除操作失败: {str(e)}", exc_info=True)
        return jsonify(success=False, error=str(e)), 500
