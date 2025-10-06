# -*- coding: utf-8 -*-
"""
错误处理工具模块
"""

import logging
import traceback
from functools import wraps
from flask import jsonify, request


class FilePreviewError(Exception):
    """文件预览相关错误"""
    pass


class FileSizeError(FilePreviewError):
    """文件大小超限错误"""
    pass


class FileAccessError(FilePreviewError):
    """文件访问权限错误"""
    pass


class FileEncodingError(FilePreviewError):
    """文件编码错误"""
    pass


def handle_api_errors(f):
    """API错误处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except FileSizeError as e:
            logging.warning(f"文件大小超限: {str(e)}")
            return jsonify({
                'error': '文件太大，无法预览',
                'type': 'size_error',
                'message': str(e)
            }), 413
        except FileAccessError as e:
            logging.warning(f"文件访问权限错误: {str(e)}")
            return jsonify({
                'error': '没有访问权限',
                'type': 'access_error',
                'message': str(e)
            }), 403
        except FileEncodingError as e:
            logging.warning(f"文件编码错误: {str(e)}")
            return jsonify({
                'error': '文件编码不支持',
                'type': 'encoding_error',
                'message': str(e)
            }), 422
        except FileNotFoundError as e:
            logging.warning(f"文件未找到: {str(e)}")
            return jsonify({
                'error': '文件不存在',
                'type': 'not_found',
                'message': str(e)
            }), 404
        except PermissionError as e:
            logging.warning(f"权限错误: {str(e)}")
            return jsonify({
                'error': '权限不足',
                'type': 'permission_error',
                'message': str(e)
            }), 403
        except Exception as e:
            logging.error(f"API错误 - {request.endpoint}: {str(e)}", exc_info=True)
            return jsonify({
                'error': '服务器内部错误',
                'type': 'internal_error',
                'message': str(e) if logging.getLogger().isEnabledFor(logging.DEBUG) else '请联系管理员'
            }), 500
    return decorated_function


def log_performance(f):
    """性能监控装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import time
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > 1.0:  # 超过1秒记录警告
                logging.warning(f"慢查询 - {f.__name__}: {execution_time:.2f}s")
            elif execution_time > 0.5:  # 超过0.5秒记录信息
                logging.info(f"性能监控 - {f.__name__}: {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"错误 - {f.__name__} ({execution_time:.2f}s): {str(e)}")
            raise
            
    return decorated_function


def validate_file_path(file_path):
    """验证文件路径安全性"""
    import os
    
    if not file_path:
        raise FileAccessError("文件路径不能为空")
    
    # 解码路径
    if isinstance(file_path, str):
        try:
            file_path = file_path.encode('utf-8').decode('utf-8')
        except UnicodeError:
            raise FileEncodingError("文件路径编码错误")
    
    # 规范化路径
    abs_path = os.path.abspath(file_path)
    base_path = os.path.abspath('.')
    
    # 检查路径是否在允许的目录内
    if not abs_path.startswith(base_path):
        raise FileAccessError("不允许访问此路径")
    
    # 检查路径遍历攻击
    if '..' in file_path or file_path.startswith('/'):
        raise FileAccessError("路径包含非法字符")
    
    return abs_path


def validate_file_size(file_path, max_size=10*1024*1024):
    """验证文件大小"""
    import os
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件不存在: {file_path}")
    
    if not os.path.isfile(file_path):
        raise FileAccessError(f"不是文件: {file_path}")
    
    file_size = os.path.getsize(file_path)
    if file_size > max_size:
        raise FileSizeError(f"文件大小 {file_size} 超过限制 {max_size}")
    
    return file_size


def safe_file_operation(operation):
    """安全文件操作装饰器"""
    @wraps(operation)
    def wrapper(file_path, *args, **kwargs):
        try:
            # 验证路径
            safe_path = validate_file_path(file_path)
            
            # 执行操作
            return operation(safe_path, *args, **kwargs)
            
        except (FilePreviewError, FileNotFoundError, PermissionError):
            raise
        except Exception as e:
            logging.error(f"文件操作错误 - {operation.__name__}: {str(e)}")
            raise FilePreviewError(f"文件操作失败: {str(e)}")
    
    return wrapper


class ErrorLogger:
    """错误日志记录器"""
    
    @staticmethod
    def log_file_access(file_path, operation, success=True, error=None):
        """记录文件访问日志"""
        if success:
            logging.info(f"文件访问成功 - {operation}: {file_path}")
        else:
            logging.warning(f"文件访问失败 - {operation}: {file_path}, 错误: {error}")
    
    @staticmethod
    def log_cache_operation(operation, details=None):
        """记录缓存操作日志"""
        message = f"缓存操作 - {operation}"
        if details:
            message += f": {details}"
        logging.info(message)
    
    @staticmethod
    def log_performance_issue(operation, duration, threshold=1.0):
        """记录性能问题"""
        if duration > threshold:
            logging.warning(f"性能问题 - {operation}: {duration:.2f}s (阈值: {threshold}s)")


def create_error_response(error_type, message, status_code=500, details=None):
    """创建标准错误响应"""
    response_data = {
        'error': message,
        'type': error_type,
        'success': False
    }
    
    if details:
        response_data['details'] = details
    
    return jsonify(response_data), status_code


def handle_upload_errors(f):
    """上传错误处理装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logging.error(f"上传错误: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'error': '上传失败',
                'message': str(e)
            }), 500
    return decorated_function
