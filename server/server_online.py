# server.py (带 /get_image)
from flask import Flask, request, jsonify, send_file
import os
import json
import threading
import time
import logging

app = Flask(__name__)

# ================= 配置 =================
DATA_DIR = "./json_data"
CLASSIFIED_DIR = "./client_classified"
TASK_DIR = "./client_task_list"
IMG_PATH_FILE = "img_path.txt"
TOKEN_FILE = "token.txt"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CLASSIFIED_DIR, exist_ok=True)
os.makedirs(TASK_DIR, exist_ok=True)

SERVER_PROGRESS_FILE = os.path.join(DATA_DIR, "server_progress.json")
TASK_LIST_FILE = os.path.join(DATA_DIR, "task_list.json")

progress_data = {}

# ================ 工具函数 ================
def read_tokens():
    """读取 token 列表"""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    return []

def save_server_progress():
    with open(SERVER_PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress_data, f, ensure_ascii=False, indent=2)

def load_server_progress():
    global progress_data
    if os.path.exists(SERVER_PROGRESS_FILE):
        with open(SERVER_PROGRESS_FILE, "r", encoding="utf-8") as f:
            progress_data = json.load(f)

def read_task_list():
    if os.path.exists(TASK_LIST_FILE):
        with open(TASK_LIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_task_list(data):
    with open(TASK_LIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_image_files(folder):
    exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
    try:
        return [f for f in os.listdir(folder) if f.lower().endswith(exts)]
    except Exception:
        return []

# ================ 进度打印 ================
def print_progress():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=========== 当前进度 ===========")
    if not progress_data:
        print("暂无进度数据")
        return

    total_tasks = sum(info.get("total_images", 0) for info in progress_data.values())
    processed_all = sum(info.get("processed_images", 0) for info in progress_data.values())
    percent = (processed_all / total_tasks * 100) if total_tasks else 0
    print(f"总进度: {processed_all}/{total_tasks} ({percent:.2f}%)\n")

    for user, info in progress_data.items():
        total = info.get("total_images", 0)
        processed = info.get("processed_images", 0)
        user_percent = (processed / total * 100) if total else 0
        classified_file = os.path.join(CLASSIFIED_DIR, f"classified_{user}.json")
        status = "✅" if os.path.exists(classified_file) else "❌"
        print(f"{user}: {processed}/{total} ({user_percent:.2f}%) 更新时间: {info.get('last_update', '')} {status}")

def auto_print_progress():
    while True:
        print_progress()
        time.sleep(2)

# ================ 路由 ================
@app.route("/auth", methods=["POST"])
def auth():
    token = request.json.get("token")
    if token in read_tokens():
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "Invalid Token"}), 403

@app.route("/get_task", methods=["GET"])
def get_task():
    token = request.args.get("token")
    if not token:
        return jsonify({"status": "error", "message": "Missing token"}), 400

    # 客户端任务文件路径
    task_file = os.path.join(TASK_DIR, f"task_{token}.json")
    if not os.path.exists(task_file):
        return jsonify({"status": "error", "message": "Task file not found for this token"}), 404

    with open(task_file, "r", encoding="utf-8") as f:
        task_data = json.load(f)
    return jsonify({"status": "ok", "task": task_data})

@app.route("/get_images", methods=["GET"])
def get_images():
    token = request.args.get("token")
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 10))

    task_list = read_task_list()
    if token not in task_list:
        return jsonify({"status": "error", "message": "No task for this token"}), 404

    task_files = task_list[token]
    paged_files = task_files[offset:offset + limit]
    return jsonify({"status": "ok", "images": paged_files})

@app.route("/upload_progress", methods=["POST"])
def upload_progress():
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "Missing user_id"}), 400

    progress_data[user_id] = {
        "total_images": data.get("total_images", 0),
        "processed_images": data.get("processed_images", 0),
        "last_update": data.get("last_update", "")
    }
    save_server_progress()
    return jsonify({"status": "ok"})

@app.route("/upload_classified", methods=["POST"])
def upload_classified():
    data = request.json
    user_id = data.get("user_id")
    classified = data.get("classified")
    if not user_id or not classified:
        return jsonify({"status": "error", "message": "Missing user_id or classified"}), 400

    out_path = os.path.join(CLASSIFIED_DIR, f"classified_{user_id}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(classified, f, ensure_ascii=False, indent=2)
    return jsonify({"status": "ok"})

# ================ 新增: 提供图片下载接口 /get_image ================
@app.route("/get_image", methods=["GET"])
def get_image():
    """
    GET /get_image?filename=xxx.jpg&token=...
    - filename: required, just the filename (no directories)
    - token: optional. If token.txt exists and contains tokens, token is required and validated.
    """
    filename = request.args.get("filename")
    token = request.args.get("token", None)

    # basic param check
    if not filename:
        return jsonify({"status": "error", "message": "Missing filename parameter"}), 400

    # read image dir
    if not os.path.exists(IMG_PATH_FILE):
        return jsonify({"status": "error", "message": f"{IMG_PATH_FILE} not configured on server"}), 500
    with open(IMG_PATH_FILE, "r", encoding="utf-8") as f:
        img_dir = f.read().strip()
    if not img_dir or not os.path.isdir(img_dir):
        return jsonify({"status": "error", "message": "Invalid image directory configured on server"}), 500

    # if server has tokens, require valid token
    tokens = read_tokens()
    if tokens:
        if not token:
            return jsonify({"status": "error", "message": "Missing token (server requires authentication)"}), 403
        if token not in tokens:
            return jsonify({"status": "error", "message": "Invalid token"}), 403

    # prevent path traversal: only allow simple filenames
    if os.path.isabs(filename) or ".." in filename or "/" in filename or "\\" in filename:
        return jsonify({"status": "error", "message": "Invalid filename"}), 400

    # build absolute path and check it is under img_dir
    abs_img_dir = os.path.abspath(img_dir)
    abs_path = os.path.abspath(os.path.join(abs_img_dir, filename))
    if not abs_path.startswith(abs_img_dir + os.sep) and abs_path != abs_img_dir:
        return jsonify({"status": "error", "message": "Invalid filename or path traversal detected"}), 400

    if not os.path.exists(abs_path):
        return jsonify({"status": "error", "message": "Image not found"}), 404

    # send file
    try:
        return send_file(abs_path, as_attachment=False)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to send image: {e}"}), 500

@app.route("/undo_last_classification", methods=["POST"])
def undo_last_classification():
    data = request.json
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"status": "error", "message": "Missing user_id"}), 400

    classified_file = os.path.join(CLASSIFIED_DIR, f"classified_{user_id}.json")
    
    # 检查分类文件是否存在
    if not os.path.exists(classified_file):
        return jsonify({"status": "error", "message": "No classified data found"}), 404

    try:
        # 读取当前分类数据
        with open(classified_file, "r", encoding="utf-8") as f:
            classified_data = json.load(f)
        
        # 如果有分类数据，移除最后一个分类项
        if classified_data:
            # 获取所有图片名
            image_names = list(classified_data.keys())
            if image_names:
                # 移除最后一个图片的分类记录
                last_image = image_names[-1]
                del classified_data[last_image]
                
                # 保存更新后的分类数据
                with open(classified_file, "w", encoding="utf-8") as f:
                    json.dump(classified_data, f, ensure_ascii=False, indent=2)
                
                # 更新进度数据
                if user_id in progress_data:
                    progress_data[user_id]["processed_images"] = max(0, progress_data[user_id]["processed_images"] - 1)
                    progress_data[user_id]["last_update"] = time.strftime('%Y-%m-%d %H:%M:%S')
                    save_server_progress()
                
                return jsonify({
                    "status": "ok", 
                    "new_index": progress_data[user_id]["processed_images"] if user_id in progress_data else 0,
                    "classified_data": classified_data
                })
        
        return jsonify({"status": "error", "message": "No classification records to undo"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to undo classification: {str(e)}"}), 500

# ================ 菜单功能 ================
def run_server():
    load_server_progress()
    threading.Thread(target=auto_print_progress, daemon=True).start()
    app.run(host="0.0.0.0", port=4555, debug=False)

if __name__ == "__main__":
    run_server()
