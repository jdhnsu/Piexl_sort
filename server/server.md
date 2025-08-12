# Server 端的开发

📂 Server 端基础框架
```
# server.py
from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

# ==== 文件路径 ====
DATA_DIR = "data"
TOKEN_FILE = os.path.join(DATA_DIR, "token.txt")
TASK_LIST_FILE = os.path.join(DATA_DIR, "task_list.json")
SERVER_PROGRESS_FILE = os.path.join(DATA_DIR, "server_progress.json")
SERVER_CLASSIFIED_FILE = os.path.join(DATA_DIR, "server_classified.json")

# ==== 工具函数 ====
def read_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def read_tokens():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines()]
    return []

# ==== 路由 ====

@app.route("/")
def index():
    return jsonify({"message": "Server is running"}), 200

@app.route("/auth", methods=["POST"])
def auth():
    """验证 Token"""
    token = request.json.get("token")
    if token in read_tokens():
        return jsonify({"status": "ok", "task_list": read_json(TASK_LIST_FILE)})
    return jsonify({"status": "error", "message": "Invalid Token"}), 403

@app.route("/upload_progress", methods=["POST"])
def upload_progress():
    """接收客户端的 progress 增量"""
    data = request.json
    # TODO: 合并到 SERVER_PROGRESS_FILE
    return jsonify({"status": "ok"})

@app.route("/upload_classified", methods=["POST"])
def upload_classified():
    """接收客户端的分类结果"""
    data = request.json
    # TODO: 合并到 SERVER_CLASSIFIED_FILE
    return jsonify({"status": "ok"})

@app.route("/get_image", methods=["GET"])
def get_image():
    """返回一张图片（远程模式用）"""
    filename = request.args.get("filename")
    # TODO: 读取图片并返回二进制数据
    return jsonify({"status": "todo"})

if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(host="0.0.0.0", port=5000, debug=True)

```
---

📄 JSON 文件格式示例

1. task_list.json（任务文件列表）

用于分发给客户端的任务列表，按文件顺序存放。
客户端第一次连接远程模式时会下载这个文件。

{
  "files": [
    "img001.jpg",
    "img002.jpg",
    "img003.jpg",
    "img004.jpg"
  ]
}


---

2. progress.json（客户端 & 服务端统一格式）

本地：记录当前用户处理进度（撤销功能依赖）
服务端：保存所有用户的进度汇总

{
  "token": "001_001_abc",
  "processed": [
    {
      "filename": "img001.jpg",
      "status": "processed",
      "category": "清洗",
      "timestamp": "2025-08-08T12:30:00"
    },
    {
      "filename": "img002.jpg",
      "status": "processed",
      "category": "遮挡",
      "timestamp": "2025-08-08T12:32:15"
    }
  ],
  "current_index": 2
}


---

3. server_progress.json（服务端）

存储所有用户的进度，用 Token 作为键。

{
  "001_001_abc": {
    "processed_count": 20,
    "total": 100,
    "last_update": "2025-08-08T12:32:15"
  },
  "001_002_xyz": {
    "processed_count": 15,
    "total": 100,
    "last_update": "2025-08-08T12:28:40"
  }
}


---

4. classified.json（客户端本地）

记录用户本地的分类结果，任务完成后上传到服务端。

{
  "img001.jpg": {
    "category": "清洗",
    "user_id": "001_001_abc",
    "timestamp": "2025-08-08T12:30:00"
  },
  "img002.jpg": {
    "category": "遮挡",
    "user_id": "001_001_abc",
    "timestamp": "2025-08-08T12:32:15"
  }
}


---

5. server_classified.json（服务端）

服务端合并所有用户的分类结果，可能存在冲突。

{
  "img001.jpg": [
    {
      "category": "清洗",
      "user_id": "001_001_abc"
    },
    {
      "category": "保留",
      "user_id": "001_002_xyz"
    }
  ],
  "img002.jpg": [
    {
      "category": "遮挡",
      "user_id": "001_001_abc"
    }
  ]
}


---

6. token.txt

服务端启动时生成，用于下发给客户端。

001_001_abc
001_002_xyz
002_001_qwe
002_002_rty


---

这样，我们的 server.py 框架已经具备：

基本目录结构

API 路由占位

JSON 文件格式全部对齐到之前的设定
