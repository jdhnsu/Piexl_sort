import requests
import time
from datetime import datetime

# ===== 配置 =====
SERVER_URL = "http://127.0.0.1:5000"  # 改成你的服务端地址
TOKENS = ["001_001_exl", "001_002_bnv", "002_002_jfm"]  # 改成你的测试 token 列表
TOTAL_IMAGES = 50                      # 模拟任务总数
STEP = 3                               # 每次处理的数量（模拟每3张上传一次）

def upload_progress(user_id, processed):
    url = f"{SERVER_URL}/upload_progress"
    payload = {
        "user_id": user_id,
        "processed_images": processed,
        "total_images": TOTAL_IMAGES,
        "last_update": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }
    try:
        resp = requests.post(url, json=payload)
        print(f"[上传进度] {user_id}: {processed}/{TOTAL_IMAGES} -> {resp.json()}")
    except Exception as e:
        print(f"[错误] {user_id}: 无法连接服务器: {e}")

if __name__ == "__main__":
    for token in TOKENS:
        processed = 0
        while processed < TOTAL_IMAGES:
            processed = min(processed + STEP, TOTAL_IMAGES)
            upload_progress(token, processed)
            time.sleep(0.5)  # 模拟处理时间

    print("[完成] 全部进度已上传。")

