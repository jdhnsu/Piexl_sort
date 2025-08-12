import os
import json


def get_image_files(folder):
    exts = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
    return [f for f in os.listdir(folder) if f.lower().endswith(exts)]

def get_img_path():
    path_file = "img_path.txt"
    img_path = None
    if os.path.exists(path_file):
        with open(path_file, "r", encoding="utf-8") as f:
            old_path = f.read().strip()
        print(f"检测到已有图片路径: {old_path}")
        update = input("是否更新图片路径？(y/n): ").strip().lower()
        if update == "y":
            img_path = input("请输入待处理图片文件夹路径: ").strip()
            with open(path_file, "w", encoding="utf-8") as f:
                f.write(img_path)
        else:
            img_path = old_path
    else:
        img_path = input("请输入待处理图片文件夹路径: ").strip()
        with open(path_file, "w", encoding="utf-8") as f:
            f.write(img_path)
    return img_path

def read_tokens(token_path):
    with open(token_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # 只保留格式为 组号_成员号_随机字母 的 token
    return [line.strip() for line in lines if line.strip().count('_') == 2 and len(line.strip().split('_')[-1]) == 3]

def save_task_list(files, out_path):
    data = {"files": files}
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_client_task_lists(tokens, files, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    total = len(files)
    n = len(tokens)
    avg = total // n
    extra = total % n
    start = 0
    for i, token in enumerate(tokens):
        count = avg + (1 if i < extra else 0)
        user_files = files[start:start+count]
        start += count
        out_path = os.path.join(out_dir, f"task_{token}.json")
        save_task_list(user_files, out_path)

if __name__ == "__main__":
    folder = get_img_path()
    files = get_image_files(folder)
    save_task_list(files, "./json_data/task_list.json")
    tokens = read_tokens("token.txt")
    save_client_task_lists(tokens, files, "./client_task_list")
    print(f"已生成 {len(files)} 个图片任务，分发给 {len(tokens)} 个用户。图片目录: {folder}")