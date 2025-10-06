# -*- coding: utf-8 -*-
"""
命令执行工具模块
"""

import os
import re
import subprocess
import logging
from threading import Thread
from datetime import datetime


class CommandExecutor:
    """命令执行器类"""
    
    def __init__(self, socketio):
        self.socketio = socketio
        self.command_text = ""
        self.command_thread = None
        self.log_file = "command_history.log"
        self._load_history()
    
    def execute_command(self, command):
        """执行命令"""
        if self.command_thread and self.command_thread.is_alive():
            logging.warning("已有命令正在执行中")
            return False
        
        # 开始新的命令会话
        self.start_new_session(command)
        
        self.command_thread = Thread(target=self._run_command, args=(command,))
        self.command_thread.start()
        return True
    
    def _emit_output(self, line):
        """发送输出到前端"""
        self.command_text += line + '\n'
        self._save_to_file(line)
        
        if line.strip() == '':  # 忽略空行
            return
        
        try:
            # 尝试保持原始字符串
            self.socketio.emit('command_output', {'data': line})
        except:
            # 如果有编码问题，使用错误处理
            self.socketio.emit('command_output', {'data': line.encode('utf-8', errors='replace').decode('utf-8')})
    
    def _run_command(self, command):
        """执行命令的内部方法"""
        try:
            # 设置环境变量确保正确的编码
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['LANG'] = 'zh_CN.UTF-8'
            env['LC_ALL'] = 'zh_CN.UTF-8'
            
            process = subprocess.Popen(
                command.split(),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                universal_newlines=False,  # 保持字节模式
                env=env
            )

            buffer = b''  # 使用字节缓冲区
            while True:
                char = process.stdout.read(1)
                if not char:
                    break
                buffer += char

                # 检查是否有完整行
                if b'\n' in buffer or b'\r' in buffer:
                    # 使用utf-8解码，如果失败则使用错误处理
                    try:
                        text = buffer.decode('utf-8')
                    except UnicodeDecodeError:
                        text = buffer.decode('utf-8', errors='replace')
                    
                    lines = re.split(r'\r\n|\n|\r', text)
                    complete_lines = lines[:-1]
                    buffer = lines[-1].encode('utf-8')  # 保持字节格式

                    for line in complete_lines:
                        self._emit_output(line)

            # 处理缓冲区中剩余内容
            if buffer.strip():
                try:
                    remaining_text = buffer.decode('utf-8').strip()
                except UnicodeDecodeError:
                    remaining_text = buffer.decode('utf-8', errors='replace').strip()
                
                if '\r' not in remaining_text:
                    self._emit_output(remaining_text + '\n')

            process.stdout.close()
            return_code = process.wait()
            self._emit_output(f"[命令执行完毕] 状态码: {return_code}\n")

        except Exception as e:
            self._emit_output(f"[错误] {str(e)}\n")
            logging.error(f"命令执行失败: {str(e)}", exc_info=True)
    
    def _load_history(self):
        """从文件加载历史日志"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    self.command_text = f.read()
                logging.info(f"已加载历史日志，共 {len(self.command_text)} 字符")
            else:
                self.command_text = ""
                logging.info("未找到历史日志文件，从空开始")
        except Exception as e:
            logging.error(f"加载历史日志失败: {str(e)}")
            self.command_text = ""
    
    def _save_to_file(self, line):
        """将日志行保存到文件"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
                f.flush()  # 立即刷新到磁盘
        except Exception as e:
            logging.error(f"保存日志到文件失败: {str(e)}")
    
    def get_command_history(self):
        """获取命令历史"""
        # 重新从文件加载最新的历史记录
        self._load_history()
        return self.command_text
    
    def clear_history(self):
        """清空历史日志"""
        try:
            self.command_text = ""
            if os.path.exists(self.log_file):
                os.remove(self.log_file)
            logging.info("历史日志已清空")
            return True
        except Exception as e:
            logging.error(f"清空历史日志失败: {str(e)}")
            return False
    
    def start_new_session(self, command):
        """开始新的命令会话"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        session_header = f"\n{'='*60}\n[{timestamp}] 开始执行命令: {command}\n{'='*60}\n"
        self.command_text += session_header
        self._save_to_file(session_header.strip())
