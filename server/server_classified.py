import os
import json

def merge_classified(client_dir, server_path, conflict_path):
    merged = {}
    # 遍历所有客户端分类文件
    for fname in os.listdir(client_dir):
        if fname.startswith("classified_") and fname.endswith(".json"):
            path = os.path.join(client_dir, fname)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for img, results in data.items():
                if img not in merged:
                    merged[img] = []
                # 结果可能是列表或单个对象
                if isinstance(results, list):
                    merged[img].extend(results)
                else:
                    merged[img].append(results)
    # 写入合并结果
    with open(server_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    # 检查冲突和不冲突
    conflict = {}
    no_conflict = {}
    for img, items in merged.items():
        cats = set([x['category'] for x in items])
        if len(cats) > 1:
            conflict[img] = items
        else:
            no_conflict[img] = items
    if conflict:
        with open(conflict_path, "w", encoding="utf-8") as f:
            json.dump(conflict, f, ensure_ascii=False, indent=2)
    # 写入不冲突文件
    no_conflict_path = server_path.replace('server_classified.json', 'no_conflict_classified.json')
    with open(no_conflict_path, "w", encoding="utf-8") as f:
        json.dump(no_conflict, f, ensure_ascii=False, indent=2)
    print(f"合并完成，分类冲突 {len(conflict)} 项，已写入 {conflict_path}，不冲突 {len(no_conflict)} 项，已写入 {no_conflict_path}")

if __name__ == "__main__":
    client_dir = "./client_classified" # 客户端分类结果目录
    server_path = "./json_data/server_classified.json"
    conflict_path = "./json_data/conflict_classified.json"
    merge_classified(client_dir, server_path, conflict_path)
