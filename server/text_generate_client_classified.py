import os
import json
import random
# 测试脚本
def read_tokens(token_path):
    with open(token_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return [line.strip() for line in lines if line.strip().count('_') == 2 and len(line.strip().split('_')[-1]) == 3]

def read_task_list(task_list_path):
    with open(task_list_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('files', [])

# 测试分类标签
CATEGORIES = ['清洗', '遮挡', '保留']

def generate_classified(token, files):
    result = {}
    for fname in files:
        # 随机生成1~2个分类结果，模拟冲突
        n = random.choice([1, 2])
        result[fname] = [
            {
                'category': random.choice(CATEGORIES),
                'user_id': token
            } for _ in range(n)
        ]
    return result

def save_classified(token, classified, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'classified_{token}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(classified, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    token_path = './token.txt'
    task_list_path = './json_data/task_list.json'
    out_dir = './client_classified'
    tokens = read_tokens(token_path)
    files = read_task_list(task_list_path)
    # 生成所有用户分类文件
    all_classified = {}
    for token in tokens:
        classified = generate_classified(token, files)
        save_classified(token, classified, out_dir)
        for img, results in classified.items():
            if img not in all_classified:
                all_classified[img] = []
            all_classified[img].extend(results)
    # 合并后统计冲突（与 server_classified.py 逻辑一致）
    conflict_imgs = set()
    for img, items in all_classified.items():
        cats = set([x['category'] for x in items])
        if len(cats) > 1:
            conflict_imgs.add(img)
    print(f'已为 {len(tokens)} 个用户生成测试分类文件。')
    print(f'合并后全体用户分类文件共包含 {len(conflict_imgs)} 个冲突图片（同一图片有多个不同分类）。')
