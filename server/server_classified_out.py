import os
import json
import shutil

# 源图片目录自动读取
img_path_file = "img_path.txt"
if os.path.exists(img_path_file):
    with open(img_path_file, "r", encoding="utf-8") as f:
        src_dir = f.read().strip()
else:
    src_dir = input("请输入图片目录路径: ").strip()
# 分类结果文件
classified_path = "./json_data/no_conflict_classified.json"
# 输出目录
out_root = "./out"

with open(classified_path, "r", encoding="utf-8") as f:
    data = json.load(f)

for img, items in data.items():
    if not items:
        continue
    category = items[0]["category"]
    out_dir = os.path.join(out_root, category)
    os.makedirs(out_dir, exist_ok=True)
    src_path = os.path.join(src_dir, img)
    dst_path = os.path.join(out_dir, img)
    if os.path.exists(src_path):
        shutil.copy2(src_path, dst_path)
        print(f"{img} -> {category}")
    else:
        print(f"图片不存在: {src_path}")

print("分类完成。")