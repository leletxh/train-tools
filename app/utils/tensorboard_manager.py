# -*- coding: utf-8 -*-
"""
TensorBoard 管理工具模块
"""

import os
import subprocess
import logging
from threading import Thread


class TensorBoardManager:
    """TensorBoard 管理器类"""
    
    def __init__(self):
        self.tb_process = None
        self.tb_thread = None
        self.is_running = False
        self.log_path = "logs"
        self.port = "6006"
        self.host = "0.0.0.0"
    
    def start_tensorboard(self, log_path="logs", port="6006", host="0.0.0.0"):
        """启动 TensorBoard"""
        if self.is_running:
            logging.warning("TensorBoard 已在运行中")
            return False
        
        self.log_path = log_path
        self.port = port
        self.host = host
        
        # 确保日志目录存在
        if not os.path.exists(log_path):
            os.makedirs(log_path)
        
        # 启动 TensorBoard 线程
        self.tb_thread = Thread(target=self._run_tensorboard)
        self.tb_thread.daemon = True
        self.tb_thread.start()
        
        self.is_running = True
        logging.info(f"TensorBoard 已启动，日志路径: {log_path}, 端口: {port}")
        return True
    
    def stop_tensorboard(self):
        """停止 TensorBoard"""
        if not self.is_running:
            return False
        
        if self.tb_process:
            self.tb_process.terminate()
            self.tb_process.wait()
            self.tb_process = None
        
        self.is_running = False
        logging.info("TensorBoard 已停止")
        return True
    
    def restart_tensorboard(self, log_path=None, port=None, host=None):
        """重启 TensorBoard"""
        self.stop_tensorboard()
        
        # 使用新参数或保持原有参数
        new_log_path = log_path or self.log_path
        new_port = port or self.port
        new_host = host or self.host
        
        return self.start_tensorboard(new_log_path, new_port, new_host)
    
    def _run_tensorboard(self):
        """运行 TensorBoard 的内部方法"""
        try:
            tb_command = [
                "tensorboard",
                "--logdir", self.log_path,
                "--host", self.host,
                "--port", self.port
            ]
            
            self.tb_process = subprocess.Popen(tb_command)
            self.tb_process.wait()
            
        except Exception as e:
            logging.error(f"TensorBoard 启动失败: {str(e)}", exc_info=True)
        finally:
            self.is_running = False
    
    def get_url(self):
        """获取 TensorBoard URL"""
        if self.is_running:
            return f"http://localhost:{self.port}"
        return None
    
    def get_status(self):
        """获取 TensorBoard 状态"""
        return {
            "is_running": self.is_running,
            "log_path": self.log_path,
            "port": self.port,
            "host": self.host,
            "url": self.get_url()
        }
