import os
import cv2
import numpy as np
import sys

def analyze_mask(mask_img):
    gray = cv2.cvtColor(mask_img, cv2.COLOR_BGR2GRAY)
    foreground = np.count_nonzero(gray > 0)
    total = gray.size
    return foreground / total

def analyze_image(img_path):
    img = cv2.imread(img_path)
    if img is None:
        print(f"无法读取图片: {img_path}")
        return
    h, w, c = img.shape
    part_w = w // 3
    if part_w == 0:
        print("图片宽度异常，无法等分三份")
        return
    mask_img = img[:, part_w:2*part_w]
    ratio = analyze_mask(mask_img)
    print(f"{os.path.basename(img_path)} 前景占比: {ratio:.2%}")

if __name__ == "__main__":
    while True:
        img_path = input("请输入图片路径（或输入 q 退出）：").strip()
        if img_path.lower() == 'q':
            print("程序已退出。"); break
        if not os.path.isfile(img_path):
            print("文件不存在，请重新输入。"); continue
        analyze_image(img_path)
