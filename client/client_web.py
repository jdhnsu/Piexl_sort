from flask import Flask, render_template, request, jsonify
import os
import json
import requests
from PIL import Image, ImageDraw, ImageFont
import io
import base64
from datetime import datetime
import re
import numpy as np
import threading

app = Flask(__name__)

# 全局变量存储服务器配置和任务数据
SERVER_URL = ""
TOKEN = ""
TASK_DATA = {}
CURRENT_IMAGE_INDEX = 0
CLASSIFIED_DATA = {}

# 添加预加载缓存
PRELOAD_CACHE = {}
PRELOAD_CACHE_SIZE = 2  # 缓存大小

# 创建数据目录
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# 辅助函数用于生成带token的文件名
def get_task_filename(token):
    """根据token生成任务文件名"""
    # 验证token格式，只允许字母、数字和下划线
    if not re.match(r'^[a-zA-Z0-9_]+$', token):
        raise ValueError("Invalid token format")
    return os.path.join(DATA_DIR, f"task_{token}.json")

def get_classified_filename(token):
    """根据token生成分类文件名"""
    # 验证token格式，只允许字母、数字和下划线
    if not re.match(r'^[a-zA-Z0-9_]+$', token):
        raise ValueError("Invalid token format")
    return os.path.join(DATA_DIR, f"classified_{token}.json")

# 获取当前token对应的文件路径
def get_current_files():
    """获取当前token对应的任务和分类文件路径"""
    if TOKEN:
        try:
            task_file = get_task_filename(TOKEN)
            classified_file = get_classified_filename(TOKEN)
            return task_file, classified_file
        except ValueError:
            # 如果token格式无效，使用默认文件名
            pass
    
    # 默认文件名（向后兼容）
    return os.path.join(DATA_DIR, "task.json"), os.path.join(DATA_DIR, "classified.json")

def load_local_data():
    """加载本地保存的任务和分类数据"""
    global TASK_DATA, CLASSIFIED_DATA, CURRENT_IMAGE_INDEX
    
    task_file, classified_file = get_current_files()
    
    # 加载任务数据
    if os.path.exists(task_file):
        try:
            with open(task_file, 'r', encoding='utf-8') as f:
                TASK_DATA = json.load(f)
        except Exception as e:
            print(f"加载任务数据时出错: {e}")
    
    # 加载分类数据
    if os.path.exists(classified_file):
        try:
            with open(classified_file, 'r', encoding='utf-8') as f:
                CLASSIFIED_DATA = json.load(f)
                
            # 根据已分类的数据更新当前索引
            if TASK_DATA:
                # 获取任务列表
                if 'files' in TASK_DATA:
                    task_files = TASK_DATA['files']
                else:
                    task_files = list(TASK_DATA.keys())
                
                # 计算已处理的图片数量
                processed_count = len(CLASSIFIED_DATA)
                CURRENT_IMAGE_INDEX = min(processed_count, len(task_files))
        except Exception as e:
            print(f"加载分类数据时出错: {e}")

def save_task_data():
    """保存任务数据到本地文件"""
    task_file, _ = get_current_files()
    try:
        with open(task_file, 'w', encoding='utf-8') as f:
            json.dump(TASK_DATA, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存任务数据时出错: {e}")

def save_classified_data():
    """保存分类数据到本地文件"""
    _, classified_file = get_current_files()
    try:
        with open(classified_file, 'w', encoding='utf-8') as f:
            json.dump(CLASSIFIED_DATA, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存分类数据时出错: {e}")

def preload_image(image_name):
    """预加载图片到缓存"""
    global PRELOAD_CACHE
    
    # 如果已经在缓存中，直接返回
    if image_name in PRELOAD_CACHE:
        return PRELOAD_CACHE[image_name]
    
    try:
        # 从服务器获取图片
        image_response = requests.get(f"{SERVER_URL}/get_image?filename={image_name}&token={TOKEN}")
        if image_response.status_code == 200 and image_response.content:
            # 添加到缓存
            PRELOAD_CACHE[image_name] = image_response.content
            
            # 如果缓存超过限制大小，移除最旧的条目
            if len(PRELOAD_CACHE) > PRELOAD_CACHE_SIZE:
                # 移除第一个（最旧的）条目
                oldest_key = next(iter(PRELOAD_CACHE))
                del PRELOAD_CACHE[oldest_key]
            
            return image_response.content
    except Exception as e:
        print(f"预加载图片时出错: {e}")
    
    return None

def get_image_data(image_name):
    """获取图片数据，优先从缓存获取"""
    global PRELOAD_CACHE
    
    # 如果在缓存中，直接返回并移除缓存
    if image_name in PRELOAD_CACHE:
        image_data = PRELOAD_CACHE[image_name]
        del PRELOAD_CACHE[image_name]
        return image_data
    
    # 否则从服务器获取
    try:
        image_response = requests.get(f"{SERVER_URL}/get_image?filename={image_name}&token={TOKEN}")
        if image_response.status_code == 200:
            return image_response.content
    except Exception as e:
        print(f"获取图片时出错: {e}")
    
    return None

def process_image(image_data, layout_mode="row"):
    """
    借鉴data_q的图片处理算法，处理图片并生成组合视图
    """
    try:
        # 打开原始图片
        big_img = Image.open(io.BytesIO(image_data)).convert('RGB')
        w, h = big_img.size
        part_w = w // 3
        
        # 分割图片为三部分：原始图、蒙版图、裁剪图
        orig_img = big_img.crop((0, 0, part_w, h))
        mask_img = big_img.crop((part_w, 0, part_w * 2, h)).convert('L')
        crop_img = big_img.crop((part_w * 2, 0, w, h))
        
        # 计算前景占比 (使用analyze_foreground.py中的算法)
        mask_array = np.array(mask_img)
        foreground_pixels = np.count_nonzero(mask_array > 0)
        total_pixels = mask_array.size
        foreground_ratio = foreground_pixels / total_pixels if total_pixels > 0 else 0
        
        # 创建带标注的图片（红色半透明蒙版）
        label_img = orig_img.copy()
        red = Image.new('RGBA', orig_img.size, (255, 0, 128, 128))  # 半透明红色
        # 应用蒙版到红色图层
        mask_rgba = mask_img.point(lambda x: 128 if x > 30 else 0)  # 阈值处理
        label_img = Image.composite(red, label_img, mask_rgba)
        
        if layout_mode == "grid":
            # 创建2x2宫格布局
            # 计算每张图片的尺寸
            w1, h1 = orig_img.size
            w2, h2 = mask_img.size
            w3, h3 = label_img.size
            w4, h4 = crop_img.size
            
            # 计算行列的高度和宽度
            row1_h = max(h1, h2)
            row2_h = max(h3, h4)
            col1_w = max(w1, w3)
            col2_w = max(w2, w4)
            
            # 创建宫格图片
            total_w = col1_w + col2_w
            total_h = row1_h + row2_h
            grid_img = Image.new('RGB', (total_w, total_h), (30, 30, 30))
            
            # 粘贴四张图片
            grid_img.paste(orig_img, (0, 0))
            grid_img.paste(mask_img.convert('RGB'), (col1_w, 0))
            grid_img.paste(label_img, (0, row1_h))
            grid_img.paste(crop_img, (col1_w, row1_h))
            
            return grid_img, foreground_ratio
        else:
            # 创建1x4横向排列的组合图
            imgs = [orig_img, mask_img.convert('RGB'), label_img, crop_img]
            total_w = sum(im.width for im in imgs)
            max_h = max(im.height for im in imgs)
            row_img = Image.new('RGB', (total_w, max_h), (30, 30, 30))
            
            x_offset = 0
            for im in imgs:
                # 垂直居中粘贴
                y_offset = (max_h - im.height) // 2
                row_img.paste(im, (x_offset, y_offset))
                x_offset += im.width
                
            return row_img, foreground_ratio
    except Exception as e:
        print(f"处理图片时出错: {e}")
        return None, 0

def image_to_base64(image):
    """
    将PIL图片转换为base64编码
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/connect', methods=['POST'])
def connect():
    global SERVER_URL, TOKEN, TASK_DATA, CURRENT_IMAGE_INDEX, CLASSIFIED_DATA
    
    data = request.json
    SERVER_URL = data.get('server_url', '').rstrip('/')
    TOKEN = data.get('token', '')
    
    if not SERVER_URL or not TOKEN:
        return jsonify({'status': 'error', 'message': '服务器地址和Token不能为空'}), 400
    
    # 验证token格式
    if not re.match(r'^[a-zA-Z0-9_]+$', TOKEN):
        return jsonify({'status': 'error', 'message': 'Token格式无效，只能包含字母、数字和下划线'}), 400
    
    try:
        # 验证Token - 修改为正确的认证方式
        auth_response = requests.post(f"{SERVER_URL}/auth", json={'token': TOKEN})
        if auth_response.status_code != 200:
            # 改进错误处理，提供更详细的错误信息
            error_msg = f'Token验证失败: {auth_response.status_code}'
            try:
                error_detail = auth_response.text
                if error_detail:
                    error_msg += f" - {error_detail}"
            except:
                pass
            return jsonify({'status': 'error', 'message': error_msg}), 403
        
        # 获取任务
        task_response = requests.get(f"{SERVER_URL}/get_task?token={TOKEN}")
        if task_response.status_code != 200:
            return jsonify({'status': 'error', 'message': f'获取任务失败: {task_response.text}'}), 404
            
        TASK_DATA = task_response.json().get('task', {})
        # 重置索引，将根据已分类的数据重新计算
        CURRENT_IMAGE_INDEX = 0
        
        # 保存任务数据到本地（使用带token的文件名）
        save_task_data()

        # 加载本地已有的分类数据（使用带token的文件名）
        load_local_data()
        
        return jsonify({'status': 'ok', 'message': '连接成功', 'task_count': len(TASK_DATA)})
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': f'网络连接错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'连接服务器时出错: {str(e)}'}), 500

@app.route('/get_current_image')
def get_current_image():
    global CURRENT_IMAGE_INDEX
    
    if not TASK_DATA:
        return jsonify({'status': 'error', 'message': '未获取到任务数据'}), 400
    
    # 修改: 正确处理任务数据结构
    # 原来的TASK_DATA是 {"files": [...]} 结构
    if 'files' in TASK_DATA:
        image_files = TASK_DATA['files']
    else:
        # 兼容旧格式
        image_files = list(TASK_DATA.keys())
    
    if CURRENT_IMAGE_INDEX >= len(image_files):
        return jsonify({'status': 'completed', 'message': '所有图片处理完成'}), 200
    
    current_image = image_files[CURRENT_IMAGE_INDEX]
    
    # 预加载下一张图片（如果存在）
    next_index = CURRENT_IMAGE_INDEX + 1
    if next_index < len(image_files):
        next_image = image_files[next_index]
        # 在后台线程中预加载下一张图片
        preload_thread = threading.Thread(target=preload_image, args=(next_image,))
        preload_thread.daemon = True
        preload_thread.start()
    
    return jsonify({'status': 'ok', 'image': current_image, 'index': CURRENT_IMAGE_INDEX, 'total': len(image_files)})

@app.route('/process_image/<image_name>')
def process_image_endpoint(image_name):
    try:
        # 获取布局模式参数，默认为row
        layout_mode = request.args.get('layout', 'row')
        
        # 获取图片数据（优先从缓存获取）
        image_data = get_image_data(image_name)
        if not image_data:
            return jsonify({'status': 'error', 'message': '获取图片失败'}), 404
        
        # 处理图片，根据布局模式选择不同的处理方式
        processed_image, foreground_ratio = process_image(image_data, layout_mode)
        if not processed_image:
            return jsonify({'status': 'error', 'message': '图片处理失败'}), 500
        
        # 转换为base64
        image_base64 = image_to_base64(processed_image)
        
        return jsonify({
            'status': 'ok', 
            'image_data': image_base64,
            'foreground_ratio': foreground_ratio
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'处理图片时出错: {str(e)}'}), 500

@app.route('/classify_image', methods=['POST'])
def classify_image():
    global CURRENT_IMAGE_INDEX, CLASSIFIED_DATA
    
    data = request.json
    image_name = data.get('image_name')
    category = data.get('category')
    
    # 检查是否已经完成所有图片分类
    if 'files' in TASK_DATA:
        task_files = TASK_DATA['files']
    else:
        task_files = list(TASK_DATA.keys())
        
    if CURRENT_IMAGE_INDEX >= len(task_files):
        return jsonify({'status': 'error', 'message': '所有图片已分类完成，无法继续分类'}), 400
    
    if not image_name or not category:
        return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400
    
    # 记录分类结果
    if image_name not in CLASSIFIED_DATA:
        CLASSIFIED_DATA[image_name] = []
    
    CLASSIFIED_DATA[image_name].append({
        'category': category,
        'user_id': TOKEN
    })
    
    # 保存分类数据到本地（使用带token的文件名）
    save_classified_data()
    
    # 更新进度
    CURRENT_IMAGE_INDEX += 1
    
    # 发送进度到服务器
    try:
        progress_data = {
            'user_id': TOKEN,
            'total_images': len(TASK_DATA.get('files', [])) if 'files' in TASK_DATA else len(TASK_DATA),
            'processed_images': CURRENT_IMAGE_INDEX,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        requests.post(f"{SERVER_URL}/upload_progress", json=progress_data)
    except Exception as e:
        print(f"上传进度时出错: {e}")
    
    return jsonify({'status': 'ok'})

@app.route('/submit_classification', methods=['POST'])
def submit_classification():
    global CLASSIFIED_DATA
    
    if not CLASSIFIED_DATA:
        return jsonify({'status': 'error', 'message': '没有分类数据可提交'}), 400
    
    try:
        # 提交分类结果到服务器
        classified_payload = {
            'user_id': TOKEN,
            'classified': CLASSIFIED_DATA
        }
        response = requests.post(f"{SERVER_URL}/upload_classified", json=classified_payload)
        
        if response.status_code == 200:
            # 提交成功后清空当前分类数据
            CLASSIFIED_DATA = {}
            # 删除本地分类文件（使用带token的文件名）
            _, classified_file = get_current_files()
            if os.path.exists(classified_file):
                os.remove(classified_file)
            return jsonify({'status': 'ok', 'message': '分类结果提交成功'})
        else:
            return jsonify({'status': 'error', 'message': f'提交分类结果失败，状态码: {response.status_code}'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'提交时出错: {str(e)}'}), 500

@app.route('/undo_classification', methods=['POST'])
def undo_classification():
    global CURRENT_IMAGE_INDEX, CLASSIFIED_DATA
    
    data = request.json
    image_name = data.get('image_name')
    category = data.get('category')
    from_memory = data.get('from_memory', False)
    
    # 验证TOKEN是否存在
    if not TOKEN:
        return jsonify({'status': 'error', 'message': '未连接到服务器，无法执行撤销操作'}), 400
    
    # 验证token格式
    if not re.match(r'^[a-zA-Z0-9_]+$', TOKEN):
        return jsonify({'status': 'error', 'message': 'Token格式无效'}), 400
    
    if not image_name or not category:
        return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400
    
    # 从分类数据中移除该图片的分类记录
    if image_name in CLASSIFIED_DATA:
        # 移除指定的分类记录
        CLASSIFIED_DATA[image_name] = [
            record for record in CLASSIFIED_DATA[image_name] 
            if record.get('category') != category
        ]
        
        # 如果该图片没有其他分类记录，则完全移除该图片的条目
        if not CLASSIFIED_DATA[image_name]:
            del CLASSIFIED_DATA[image_name]
    
    # 保存更新后的分类数据到本地（使用带token的文件名）
    save_classified_data()
    
    # 更新进度（回退）
    if from_memory:
        CURRENT_IMAGE_INDEX = max(0, CURRENT_IMAGE_INDEX - 1)
    
    # 发送进度更新到服务器
    try:
        progress_data = {
            'user_id': TOKEN,
            'total_images': len(TASK_DATA.get('files', [])) if 'files' in TASK_DATA else len(TASK_DATA),
            'processed_images': CURRENT_IMAGE_INDEX,
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        requests.post(f"{SERVER_URL}/upload_progress", json=progress_data)
    except Exception as e:
        print(f"上传进度时出错: {e}")
    
    return jsonify({'status': 'ok'})

@app.route('/undo_from_local_file', methods=['POST'])
def undo_from_local_file():
    global CURRENT_IMAGE_INDEX, CLASSIFIED_DATA
    
    # 验证TOKEN是否存在
    if not TOKEN:
        return jsonify({'status': 'error', 'message': '未连接到服务器，无法执行撤销操作'}), 400
    
    # 验证token格式
    if not re.match(r'^[a-zA-Z0-9_]+$', TOKEN):
        return jsonify({'status': 'error', 'message': 'Token格式无效'}), 400
    
    # 获取带token的分类文件路径
    try:
        _, classified_file = get_current_files()
    except ValueError as e:
        return jsonify({'status': 'error', 'message': f'Token验证失败: {str(e)}'}), 400
    
    # 检查本地分类文件是否存在
    if not os.path.exists(classified_file):
        return jsonify({'status': 'error', 'message': '本地没有分类记录'}), 400
    
    try:
        # 读取本地分类数据
        with open(classified_file, 'r', encoding='utf-8') as f:
            local_classified_data = json.load(f)
        
        # 如果有分类数据，移除最后一个分类项
        if local_classified_data:
            # 获取所有图片名
            image_names = list(local_classified_data.keys())
            if image_names:
                # 移除最后一个图片的分类记录
                last_image = image_names[-1]
                del local_classified_data[last_image]
                
                # 更新全局分类数据
                CLASSIFIED_DATA = local_classified_data
                
                # 保存更新后的分类数据到本地（使用带token的文件名）
                save_classified_data()
                
                # 更新进度（回退）
                CURRENT_IMAGE_INDEX = max(0, CURRENT_IMAGE_INDEX - 1)
                
                # 发送进度更新到服务器
                try:
                    progress_data = {
                        'user_id': TOKEN,
                        'total_images': len(TASK_DATA.get('files', [])) if 'files' in TASK_DATA else len(TASK_DATA),
                        'processed_images': CURRENT_IMAGE_INDEX,
                        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    requests.post(f"{SERVER_URL}/upload_progress", json=progress_data)
                except Exception as e:
                    print(f"上传进度时出错: {e}")
                
                return jsonify({
                    'status': 'ok', 
                    'new_index': CURRENT_IMAGE_INDEX,
                    'message': f'已从本地文件撤销对"{last_image}"的分类操作'
                })
        
        return jsonify({'status': 'error', 'message': '没有分类记录可撤销'}), 400
    except json.JSONDecodeError:
        return jsonify({'status': 'error', 'message': '分类文件格式错误'}), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'从本地文件撤销时出错: {str(e)}'}), 500

if __name__ == '__main__':
    # 启动时加载本地数据（使用带token的文件名）
    load_local_data()
    app.run(host='0.0.0.0', port=5001, debug=True)