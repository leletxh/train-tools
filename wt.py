import math
import os
import subprocess
import time
import logging
from flask import Flask, render_template, request, Response
from flask_socketio import SocketIO, emit
from threading import Thread
import argparse
import psutil
import GPUtil
import requests


# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# 全局变量
command_text = ""
system_data_history = []
tb_process = None
TARGET_URL = ""

# 解析参数
parser = argparse.ArgumentParser(description="训练工具")
parser.add_argument("--port", type=str, help="端口号", default="5000")
args = parser.parse_args()

# 初始化 Flask 应用
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 发送输出函数
def emit_output(data):
    global command_text
    socketio.emit('command_output', {'data': data})
    command_text += data

# 执行命令线程
def run_command(command):
    try:
        process = subprocess.Popen(
            command.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        logging.info(f"Running command: {command}")
        output_line = f"Running command: {command}\n"
        emit_output(output_line)

        for output in iter(process.stdout.readline, ''):
            if output:
                emit_output(output)
                logging.info(output.strip())

        process.stdout.close()
        return_code = process.wait()
        logging.info(f"Command finished with return code: {return_code}")

    except Exception as e:
        error_msg = f"[Error] Failed to execute command: {e}\n"
        emit_output(error_msg)
        logging.error(error_msg, exc_info=True)


# 系统资源采集线程
def get_usage():
    global system_data_history
    while True:
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = round(psutil.virtual_memory().used / (1024 ** 3), 2)
            gpus = GPUtil.getGPUs()
            gpu_usages = []
            gpu_memory_usages = []

            if gpus:
                gpu_usages = [round(gpu.load * 100, 2) for gpu in gpus]
                gpu_memory_usages = [round(gpu.memoryUsed / 1024, 2) for gpu in gpus]
            #获得磁盘剩余空间
            save_memory = round(psutil.disk_usage('/').free / (1024 ** 3), 2)

            data_point = {
                'cpu': cpu_usage,
                'memory': memory_usage,
                'gpu': gpu_usages,
                'gpu_memory': gpu_memory_usages,
                'save_memory': save_memory,
                'time': time.strftime("%Y-%m-%d %H:%M:%S")
            }

            system_data_history.append(data_point)
            if len(system_data_history) > 21:
                system_data_history.pop(0)

            socketio.emit('usage', data_point)

        except Exception as e:
            logging.error("Failed to collect system usage.", exc_info=True)

        time.sleep(1)


# 获取用户输入
print("欢迎使用训练工具，请进行配置：")
command = input("请输入运行命令（例如：python train.py）: ").strip()

print("是否启动TensorBoard？(y/n)")
start_tb = input("请输入(y/n): ").strip().lower() == 'y'

log_path = "logs"
if start_tb:
    log_path = input("请输入TensorBoard日志路径（默认 logs）: ").strip() or "logs"
    if not os.path.exists(log_path):
        os.makedirs(log_path)
    TARGET_URL = "http://localhost:6006"


# 启动 TensorBoard 子进程
tb_thread = None
if start_tb:
    tb_command = ["tensorboard", "--logdir", log_path, "--host", "0.0.0.0", "--port", "6006"]

    def run_tensorboard():
        global tb_process
        tb_process = subprocess.Popen(tb_command)
        tb_process.wait()

    tb_thread = Thread(target=run_tensorboard)
    tb_thread.daemon = True
    #tb_thread.start()


# SocketIO 事件处理
@socketio.on('connect')
def handle_connect():
    emit('history', {'data': command_text})


@socketio.on('usage')
def usage_connect():
    emit('usage_history', {'data': system_data_history})


# Flask 路由
@app.route("/")
def main():
    memory = math.ceil(psutil.virtual_memory().total / (1024 ** 3))  # GB
    gpus = GPUtil.getGPUs()
    max_gpu_memory = gpus[0].memoryTotal / 1024 if gpus else 0  # GB
    tb = start_tb
    #获得当前硬盘的大小
    max_save_memory = round(psutil.disk_usage('/').total / (1024 ** 3), 2)  # GB
    print(f"Total Memory: {memory} GB, Max GPU Memory: {max_gpu_memory} GB, Max Save Memory: {max_save_memory} GB")
    return render_template("main.html", max_memory=memory, max_gpu_memory=max_gpu_memory, tb=tb, max_save_memory=max_save_memory)


@app.route("/log")
def log():
    return render_template("log.html")


# TensorBoard 代理路由（如果启用）

@app.route('/proxy/', defaults={'path': ''})
@app.route('/proxy/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'])
def proxy(path):
    global start_tb, TARGET_URL
    if not start_tb:
        return "TensorBoard is not running.", 404

    # 完整构建目标 URL，保留原始查询参数
    target_url = f"{TARGET_URL}/{path}"
    if request.query_string:
        target_url += f"?{request.query_string.decode('utf-8')}"

    # 准备请求参数
    headers = {
        key: value for (key, value) in request.headers if key.lower() != 'host'
    }

    data = request.get_data()
    cookies = request.cookies

    # 发送请求
    resp = requests.request(
        method=request.method,
        url=target_url,
        headers=headers,
        data=data,
        cookies=cookies,
        allow_redirects=False,
        timeout=30  # 可选：防止超时挂起
    )

    # 构造响应头
    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [
        (name, value) for (name, value) in resp.raw.headers.items()
        if name.lower() not in excluded_headers
    ]

    return Response(resp.content, status=resp.status_code, headers=headers)


# 命令执行线程
command_thread = Thread(target=run_command, args=(command,))
command_thread.start()

# 系统监控线程
get_usage_thread = Thread(target=get_usage)
get_usage_thread.daemon = True
get_usage_thread.start()


# 优雅退出
def handle_exit(signum, frame):
    logging.info("Shutting down gracefully...")
    if tb_process:
        tb_process.terminate()
        tb_process.wait()
    sys.exit(0)


import signal
import sys

signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)


# 启动主应用
if __name__ == "__main__":
    logging.info("Application started.")
    try:
        socketio.run(app, port=args.port)
    finally:
        handle_exit(None, None)