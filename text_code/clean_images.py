import os
import cv2
import numpy as np
import shutil

# 文件夹路径 当前文件夹路径
dir_path = r"c:/Users/ASUS/Desktop/8-8"
output_dir = os.path.join(dir_path, "清洗-1")
os.makedirs(output_dir, exist_ok=True)

# 支持的图片格式
img_exts = [".png", ".jpg", ".jpeg"]

def is_img(filename):
    return any(filename.lower().endswith(ext) for ext in img_exts)

def analyze_mask(mask_img):
    # 假设前景为非黑色像素
    gray = cv2.cvtColor(mask_img, cv2.COLOR_BGR2GRAY)
    # 设定阈值，非0即为前景
    foreground = np.count_nonzero(gray > 0)
    total = gray.size
    return foreground / total

for fname in os.listdir(dir_path):
    if not is_img(fname):
        continue
    img_path = os.path.join(dir_path, fname)
    img = cv2.imread(img_path)
    if img is None:
        continue
    h, w, c = img.shape
    # 等分为三份
    part_w = w // 3
    if part_w == 0:
        continue
    # mask图在中间
    mask_img = img[:, part_w:2*part_w]
    ratio = analyze_mask(mask_img)
    if ratio > 0.15 or ratio < 0.01:
        shutil.move(img_path, os.path.join(output_dir, fname))
        print(f"{fname} 已移动，前景占比: {ratio:.2%}")
print("处理完成！")
