import math
import os
import shutil
import subprocess
import time
import logging
from flask import Flask, render_template, request, Response, send_file, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from threading import Thread
import argparse
import psutil
import GPUtil
import requests
import mimetypes
import base64
import zipfile
import tempfile
import urllib.parse


# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

# 系统配置
# 全局变量
command_text = ""
system_data_history = []
tb_process = None
TARGET_URL = ""

# 解析参数
parser = argparse.ArgumentParser(description="训练工具")
parser.add_argument("--port", type=str, help="端口号", default="5000")
parser.add_argument("--user_mt", type=str, help="用户权限系统开关", default="true")
args = parser.parse_args()

# 初始化 Flask 应用
app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # 添加会话密钥
socketio = SocketIO(app, cors_allowed_origins="*")

# 发送输出函数
def emit_output(data):
    global command_text
    socketio.emit('command_output', {'data': data})
    command_text += data

# 执行命令线程
# 保留ANSI转义序列输出
def run_command(command):
    try:
        process = subprocess.Popen(
            command.split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            # 不使用universal_newlines，直接字节流读取
        )
        logging.info(f"[开始执行命令] {command}")
        output_line = f"[开始执行命令] {command}\n"
        emit_output(output_line)

        for output in iter(process.stdout.readline, b''):
            if output:
                # 以utf-8解码，保留ANSI转义
                decoded = output.decode('utf-8', errors='replace')
                emit_output(decoded)
                logging.info(decoded.strip())

        process.stdout.close()
        return_code = process.wait()
        logging.info(f"Command finished with return code: {return_code}")
        # 新增：命令执行完毕后，主动推送一条状态日志
        emit_output(f"\n[命令执行完毕] 状态码: {return_code}\n")

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

print("是否启动TensorBoard？")
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
    tb_thread.start()


# SocketIO 事件处理
@socketio.on('connect')
def handle_connect():
    emit('history', {'data': command_text})


@socketio.on('usage')
def usage_connect():
    emit('usage_history', {'data': system_data_history})


# Flask 路由
@app.route("/")
def index():
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


# 文件树过滤常量
FILE_TREE_FILTER = True  # 如果为 choose，则过滤 conda 和 runtime 文件夹
env_dir_name = ".conda"  # 跳转目录名称

# 文件树递归获取函数
def get_file_tree(root_path, sort='default'):
    tree = []
    for entry in os.scandir(root_path):
        if FILE_TREE_FILTER and entry.name == env_dir_name:
            continue
        node = {
            'name': entry.name,
            'is_dir': entry.is_dir(),
        }
        if entry.is_dir():
            node['children'] = get_file_tree(entry.path, sort)
        tree.append(node)
    return tree

@app.route("/tree")
def tree_page():
    return render_template("tree.html")

@app.route("/api/tree")
def api_tree():
    root = request.args.get('root', '.')
    sort = request.args.get('sort', 'default')
    abs_root = os.path.abspath(root)
    tree = get_file_tree(abs_root, sort)
    return {"tree": tree}


@app.route("/api/preview")
def api_preview():
    path = request.args.get('path')
    if not path:
        return jsonify({'error': 'No path'}), 400
    abs_path = os.path.abspath(path)
    # 防止越权
    if not abs_path.startswith(os.path.abspath('.')):
        return jsonify({'error': 'Permission denied'}), 403
    if not os.path.isfile(abs_path):
        return jsonify({'error': 'Not a file'}), 404
    mime, _ = mimetypes.guess_type(abs_path)
    if not mime:
        mime = 'application/octet-stream'
    try:
        if mime.startswith('text') or abs_path.endswith(('.py', '.md', '.txt', '.log', '.json', '.csv')):
            with open(abs_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return jsonify({'type': 'text', 'content': content})
        elif mime.startswith('image'):
            with open(abs_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            return jsonify({'type': 'image', 'content': b64, 'mimetype': mime})
        elif mime.startswith('video'):
            with open(abs_path, 'rb') as f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
            return jsonify({'type': 'video', 'content': b64, 'mimetype': mime})
        else:
            return jsonify({'type': 'other'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download')
def api_download():
    path = request.args.get('path')
    if not path:
        return 'No path', 400
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(os.path.abspath('.')):
        return 'Permission denied', 403
    if not os.path.isfile(abs_path):
        return 'Not a file', 404
    dir_name = os.path.dirname(abs_path)
    file_name = os.path.basename(abs_path)
    return send_from_directory(dir_name, file_name, as_attachment=True)

@app.route('/api/download_folder')
def api_download_folder():
    path = request.args.get('path')
    if not path:
        return 'No path', 400
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(os.path.abspath('.')):
        return 'Permission denied', 403
    if not os.path.isdir(abs_path):
        return 'Not a folder', 404
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
    zip_path = tmp.name
    tmp.close()
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(abs_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, abs_path)
                zf.write(file_path, arcname)
    return send_file(zip_path, as_attachment=True, download_name=os.path.basename(abs_path)+'.zip')

@app.route('/api/upload', methods=['POST'])
def api_upload():
    path = request.args.get('path')
    if not path:
        return {'success': False, 'error': 'No path'}, 400
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(os.path.abspath('.')):
        return {'success': False, 'error': 'Permission denied'}, 403
    if not os.path.isdir(abs_path):
        return {'success': False, 'error': 'Not a folder'}, 404
    files = request.files.getlist('files')
    if not files:
        return {'success': False, 'error': 'No files'}, 400
    try:
        for f in files:
            save_path = os.path.join(abs_path, f.filename)
            f.save(save_path)
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}, 500

@app.route('/api/delete', methods=['POST'])
def api_delete():
    data = request.get_json()
    path = data.get('path')
    type_ = data.get('type')
    if not path:
        return jsonify(success=False, error='缺少路径')
    # 路径解码
    path  = urllib.parse.unquote(path)
    print(f"Attempting to delete: {path}, type: {type_}")
    try:
        if type_ == 'folder':
            if os.path.exists(path):
                shutil.rmtree(path)
            else:
                return jsonify(success=False, error='文件夹不存在')
        else:
            if os.path.exists(path):
                os.remove(path)
            else:
                return jsonify(success=False, error='文件不存在')
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, error=str(e))


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
