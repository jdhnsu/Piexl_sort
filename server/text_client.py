#!/usr/bin/env python3
# client_test.py
"""
测试脚本：模拟客户端处理任务并上传进度 & 分类结果

用法示例：
python client_test.py --server http://127.0.0.1:5000 --token 001_001_exl --batch 3 --sleep 0.5

参数：
--server   服务端地址（默认 http://127.0.0.1:5000）
--token    你的 token（必需）
--batch    每次上传进度的批量大小（默认 3）
--sleep    模拟处理每张图片的时间（秒，默认 0.3）
--no-auth  跳过 auth 步骤（若你不需要）
--seed     随机种子（用于可重复的分类结果）
--categories 用逗号分隔的分类列表（默认: 清洗,保留,阴影,遮挡）
"""
import argparse
import requests
import time
import random
from datetime import datetime
import sys
import json

DEFAULT_CATEGORIES = ["清洗", "保留", "阴影", "遮挡"]

def do_auth(server, token, timeout=5):
    url = server.rstrip("/") + "/auth"
    try:
        r = requests.post(url, json={"token": token}, timeout=timeout)
        return r.status_code == 200 and r.json().get("status") == "ok"
    except Exception as e:
        print(f"[auth] Exception: {e}")
        return False

def get_task(server, token, timeout=5):
    url = server.rstrip("/") + "/get_task"
    try:
        r = requests.get(url, params={"token": token}, timeout=timeout)
        if r.status_code == 200:
            j = r.json()
            task = j.get("task")
            # task might be {"files": [...]}, or a list, or {"files": {...}}
            if isinstance(task, dict) and "files" in task and isinstance(task["files"], list):
                return task["files"]
            if isinstance(task, list):
                return task
            # if dict mapping token->list
            if isinstance(task, dict):
                # find first list inside
                for v in task.values():
                    if isinstance(v, list):
                        return v
            # unknown format: return as is if list-like
            return []
        else:
            print(f"[get_task] status {r.status_code} -> {r.text}")
            return None
    except Exception as e:
        print(f"[get_task] Exception: {e}")
        return None

def get_images_paged(server, token, limit=50, timeout=5):
    """Fallback: use /get_images pagination to collect all images"""
    images = []
    offset = 0
    while True:
        url = server.rstrip("/") + "/get_images"
        try:
            r = requests.get(url, params={"token": token, "offset": offset, "limit": limit}, timeout=timeout)
            if r.status_code != 200:
                print(f"[get_images] status {r.status_code}: {r.text}")
                return None
            j = r.json()
            page = j.get("images", [])
            images.extend(page)
            offset += len(page)
            total = j.get("total")
            if len(page) < limit:
                break
            # safety: if total provided and we've fetched all
            if total is not None and offset >= total:
                break
        except Exception as e:
            print(f"[get_images] Exception: {e}")
            return None
    return images

def upload_progress(server, token, total, processed, timeout=5):
    url = server.rstrip("/") + "/upload_progress"
    payload = {
        "user_id": token,
        "total_images": total,
        "processed_images": processed,
        "last_update": datetime.now().isoformat(timespec='seconds')
    }
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        return r.status_code == 200
    except Exception as e:
        print(f"[upload_progress] Exception: {e}")
        return False

def upload_classified(server, token, classified_dict, timeout=10):
    url = server.rstrip("/") + "/upload_classified"
    payload = {
        "user_id": token,
        "classified": classified_dict
    }
    try:
        r = requests.post(url, json=payload, timeout=timeout)
        if r.status_code == 200:
            return True
        else:
            print(f"[upload_classified] status {r.status_code}: {r.text}")
            return False
    except Exception as e:
        print(f"[upload_classified] Exception: {e}")
        return False

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--server", "-s", default="http://127.0.0.1:5000", help="Server base URL")
    p.add_argument("--token", "-t", required=True, help="Token / user_id")
    p.add_argument("--batch", "-b", type=int, default=3, help="Upload batch size")
    p.add_argument("--sleep", type=float, default=0.3, help="Simulated process time per image (seconds)")
    p.add_argument("--no-auth", action="store_true", help="Skip auth step")
    p.add_argument("--seed", type=int, default=None, help="Random seed for deterministic categories")
    p.add_argument("--categories", type=str, default=",".join(DEFAULT_CATEGORIES), help="Comma-separated categories")
    args = p.parse_args()

    server = args.server.rstrip("/")
    token = args.token
    batch = max(1, args.batch)
    sleep_sec = max(0.0, args.sleep)
    categories = [c.strip() for c in args.categories.split(",") if c.strip()]
    if args.seed is not None:
        random.seed(args.seed)

    print(f"Server: {server}")
    print(f"Token: {token}")
    if not args.no_auth:
        ok = do_auth(server, token)
        print("[auth] result:", ok)
        if not ok:
            print("Auth failed — continuing anyway (use --no-auth to skip), or check token.txt on server.")
            # optionally: exit(1)

    # try get_task first
    files = get_task(server, token)
    if files is None:
        print("get_task returned None, trying paged get_images fallback")
        files = get_images_paged(server, token, limit=20)
    if files is None:
        print("Failed to obtain task from server.")
        sys.exit(1)

    # if task returned object {"files": [...]}
    if isinstance(files, dict) and "files" in files:
        files = files["files"]
    if not isinstance(files, list):
        print("Unexpected task format:", type(files))
        sys.exit(1)

    total = len(files)
    print(f"Total files for token {token}: {total}")

    if total == 0:
        print("No files to process. Exiting.")
        sys.exit(0)

    processed = 0
    classified = {}  # image -> {"category": "..."}
    step = batch

    # Process images in batches
    for i in range(0, total, step):
        batch_files = files[i:i+step]
        for fname in batch_files:
            # Simulate processing (you could fetch the image from a shared storage if needed)
            # Here we only sleep to simulate time consumption and pick a category
            time.sleep(sleep_sec)
            cat = random.choice(categories)
            classified[fname] = {"category": cat}
            processed += 1
            print(f"[process] {processed}/{total}: {fname} -> {cat}")

        # upload progress after each batch
        success = upload_progress(server, token, total, processed)
        print(f"[upload_progress] uploaded {processed}/{total} -> {'OK' if success else 'FAIL'}")

    # final upload classified
    print("[upload_classified] uploading classified results (may be large)...")
    ok = upload_classified(server, token, classified)
    print("[upload_classified] result:", ok)

    # final progress push (ensure 100%)
    upload_progress(server, token, total, processed)
    print("Done.")

if __name__ == "__main__":
    main()
