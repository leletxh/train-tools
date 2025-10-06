# -*- coding: utf-8 -*-
"""
系统监控工具模块
"""

import time
import logging
import psutil
import GPUtil
from threading import Thread


class SystemMonitor:
    """系统资源监控类"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.system_data_history = []
        self.is_running = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """启动系统监控"""
        if not self.is_running:
            self.is_running = True
            self.monitor_thread = Thread(target=self._monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
            logging.info("系统监控已启动")
    
    def stop_monitoring(self):
        """停止系统监控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logging.info("系统监控已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                data_point = self._collect_system_data()
                self.system_data_history.append(data_point)
                
                # 保持历史数据在合理范围内
                if len(self.system_data_history) > 21:
                    self.system_data_history.pop(0)
                
                # 发送数据到前端
                self.socketio.emit('usage', data_point)
                
            except Exception as e:
                logging.error("系统监控数据收集失败", exc_info=True)
            
            time.sleep(1)
    
    def _collect_system_data(self):
        """收集系统数据"""
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = round(psutil.virtual_memory().used / (1024 ** 3), 2)
        
        # GPU 信息
        gpus = GPUtil.getGPUs()
        gpu_usages = []
        gpu_memory_usages = []
        
        if gpus:
            gpu_usages = [round(gpu.load * 100, 2) for gpu in gpus]
            gpu_memory_usages = [round(gpu.memoryUsed / 1024, 2) for gpu in gpus]
        
        # 磁盘剩余空间
        save_memory = round(psutil.disk_usage('/').free / (1024 ** 3), 2)
        
        return {
            'cpu': cpu_usage,
            'memory': memory_usage,
            'gpu': gpu_usages,
            'gpu_memory': gpu_memory_usages,
            'save_memory': save_memory,
            'time': time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def get_system_config(self):
        """获取系统配置信息"""
        import math
        
        memory = math.ceil(psutil.virtual_memory().total / (1024 ** 3))  # GB
        gpus = GPUtil.getGPUs()
        max_gpu_memory = gpus[0].memoryTotal / 1024 if gpus else 0  # GB
        max_save_memory = round(psutil.disk_usage('/').total / (1024 ** 3), 2)  # GB
        
        return {
            "max_memory": memory,
            "max_gpu_memory": max_gpu_memory,
            "max_save_memory": max_save_memory
        }
    
    def get_history(self):
        """获取历史数据"""
        return self.system_data_history
