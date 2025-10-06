# -*- coding: utf-8 -*-
"""
API 路由
"""

from flask import Blueprint, request, jsonify
from app.utils import SystemMonitor, CommandExecutor, TensorBoardManager
from app.routes.main_routes import set_configured
from app.auth import login_required
import logging
import os

api_bp = Blueprint('api', __name__, url_prefix='/api')

# 全局实例（将在应用初始化时设置）
system_monitor = None
command_executor = None
tensorboard_manager = None


def init_api_services(socketio):
    """初始化API服务"""
    global system_monitor, command_executor, tensorboard_manager
    system_monitor = SystemMonitor(socketio)
    command_executor = CommandExecutor(socketio)
    tensorboard_manager = TensorBoardManager()
    
    # 启动系统监控
    system_monitor.start_monitoring()


@api_bp.route("/config")
@login_required
def api_config():
    """获取系统配置信息"""
    try:
        config_data = system_monitor.get_system_config()
        config_data.update({
            "tb": tensorboard_manager.is_running if tensorboard_manager else False,
            "OPEN_HISTORY_LOG": True
        })
        return jsonify(config_data)
    except Exception as e:
        logging.error(f"获取系统配置失败: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@api_bp.route("/start-training", methods=["POST"])
@login_required
def start_training():
    """启动训练配置"""
    try:
        # 获取JSON数据
        data = request.get_json()
        
        command = data.get("command", "")
        enable_panel = data.get("enablePanel", False)
        panel_path = data.get("panelPath", "logs")
        
        # 启动TensorBoard（如果启用）
        if enable_panel:
            success = tensorboard_manager.start_tensorboard(
                log_path=panel_path,
                port="6006",
                host="0.0.0.0"
            )
            if not success:
                return jsonify({"success": False, "error": "TensorBoard启动失败"}), 500
        else:
            # 如果之前启用了TensorBoard，现在关闭它
            tensorboard_manager.stop_tensorboard()
        
        # 启动命令执行
        if command:
            success = command_executor.execute_command(command)
            if not success:
                return jsonify({"success": False, "error": "命令执行失败，已有命令在运行"}), 400
        
        # 标记为已配置
        set_configured(True)
        
        return jsonify({"success": True, "message": "配置已保存"})
        
    except Exception as e:
        logging.error(f"启动训练配置失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/tree")
@login_required
def api_tree():
    """获取文件树（兼容性保留）"""
    try:
        from app.utils import FileManager
        
        root = request.args.get('root', '.')
        sort = request.args.get('sort', 'default')
        
        file_manager = FileManager()
        items = file_manager.get_directory_listing(root, sort)
        
        return jsonify({"tree": items})
        
    except Exception as e:
        logging.error(f"获取文件树失败: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@api_bp.route("/directory")
@login_required
def api_directory():
    """获取目录列表 - 平铺展示"""
    try:
        from app.utils import FileManager
        
        path = request.args.get('path', '.')
        sort = request.args.get('sort', 'default')
        
        file_manager = FileManager()
        items = file_manager.get_directory_listing(path, sort)
        
        return jsonify({
            "items": items,
            "current_path": os.path.abspath(path),
            "relative_path": os.path.relpath(path, '.') if path != '.' else ''
        })
        
    except Exception as e:
        logging.error(f"获取目录列表失败: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@api_bp.route("/preview")
@login_required
def api_preview():
    """预览文件 - 优化版本"""
    try:
        from app.utils import FileManager
        
        path = request.args.get('path')
        if not path:
            return jsonify({'error': 'No path'}), 400
        
        file_manager = FileManager()
        result, status_code = file_manager.preview_file(path)
        
        return jsonify(result), status_code
        
    except Exception as e:
        logging.error(f"文件预览失败: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route("/file_content")
@login_required
def api_file_content():
    """获取文件内容（用于大文件流式传输）"""
    try:
        from app.utils import FileManager
        
        path = request.args.get('path')
        if not path:
            return 'No path', 400
        
        file_manager = FileManager()
        result, error, status_code = file_manager.get_file_content(path)
        
        if error:
            return error, status_code
        
        return result
        
    except Exception as e:
        logging.error(f"获取文件内容失败: {str(e)}", exc_info=True)
        return str(e), 500


@api_bp.route("/tree_lazy")
@login_required
def api_tree_lazy():
    """延迟加载文件树"""
    try:
        from app.utils import FileManager
        
        root = request.args.get('root', '.')
        sort = request.args.get('sort', 'default')
        
        file_manager = FileManager()
        tree = file_manager.get_file_tree(root, 'lazy')
        
        return jsonify({"tree": tree})
        
    except Exception as e:
        logging.error(f"获取文件树失败: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@api_bp.route("/cache_stats")
@login_required
def api_cache_stats():
    """获取缓存统计信息"""
    try:
        from app.utils import FileManager
        
        file_manager = FileManager()
        stats = file_manager.get_cache_stats()
        
        return jsonify(stats)
        
    except Exception as e:
        logging.error(f"获取缓存统计失败: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@api_bp.route("/clear_cache", methods=["POST"])
@login_required
def api_clear_cache():
    """清理文件预览缓存"""
    try:
        from app.utils import FileManager
        
        file_manager = FileManager()
        file_manager.clear_cache()
        
        return jsonify({"success": True, "message": "缓存已清理"})
        
    except Exception as e:
        logging.error(f"清理缓存失败: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/edit_file")
@login_required
def api_edit_file():
    """获取文件内容用于编辑"""
    try:
        from app.utils import FileManager
        
        path = request.args.get('path')
        if not path:
            return jsonify({'error': 'No path'}), 400
        
        file_manager = FileManager()
        result, status_code = file_manager.edit_file(path)
        
        return jsonify(result), status_code
        
    except Exception as e:
        logging.error(f"获取编辑文件失败: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route("/save_file", methods=["POST"])
@login_required
def api_save_file():
    """保存文件内容"""
    try:
        from app.utils import FileManager
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data'}), 400
        
        path = data.get('path')
        content = data.get('content', '')
        encoding = data.get('encoding', 'utf-8')
        
        if not path:
            return jsonify({'error': 'No path'}), 400
        
        file_manager = FileManager()
        result, status_code = file_manager.save_file(path, content, encoding)
        
        return jsonify(result), status_code
        
    except Exception as e:
        logging.error(f"保存文件失败: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route("/create_file", methods=["POST"])
@login_required
def api_create_file():
    """创建新文件"""
    try:
        from app.utils import FileManager
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data'}), 400
        
        path = data.get('path')
        content = data.get('content', '')
        encoding = data.get('encoding', 'utf-8')
        
        if not path:
            return jsonify({'error': 'No path'}), 400
        
        file_manager = FileManager()
        result, status_code = file_manager.create_file(path, content, encoding)
        
        return jsonify(result), status_code
        
    except Exception as e:
        logging.error(f"创建文件失败: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@api_bp.route("/command_history")
@login_required
def api_command_history():
    """获取命令历史日志"""
    try:
        if command_executor:
            history = command_executor.get_command_history()
            return jsonify({
                'success': True,
                'history': history,
                'length': len(history)
            })
        else:
            return jsonify({'success': False, 'error': '命令执行器未初始化'}), 500
        
    except Exception as e:
        logging.error(f"获取命令历史失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route("/clear_command_history", methods=["POST"])
@login_required
def api_clear_command_history():
    """清空命令历史日志"""
    try:
        if command_executor:
            success = command_executor.clear_history()
            if success:
                return jsonify({
                    'success': True,
                    'message': '命令历史已清空'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '清空命令历史失败'
                }), 500
        else:
            return jsonify({'success': False, 'error': '命令执行器未初始化'}), 500
        
    except Exception as e:
        logging.error(f"清空命令历史失败: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
