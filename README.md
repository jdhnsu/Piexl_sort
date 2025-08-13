# 图片分类工具 - 数据清洗 (网络版)

本工具用于高效筛选和分类拼接大图（原图/掩码/修剪图），采用现代化的Web界面和客户端-服务器架构。支持图片四图展示、分类、撤销、缩放、拖动、快捷键操作。适合团队协作的数据清洗、标注辅助等场景。

---
注意 ： 仓库已经更新（老版本代码是old/ 目录下,版本为v1.2dev之前的版本）
## 目录
- [功能简介](#功能简介)
- [项目架构](#项目架构)
- [工作模式](#工作模式)
- [客户端使用说明](#客户端使用说明)
  - [1. 环境准备](#1-环境准备)
  - [2. 运行客户端](#2-运行客户端)
  - [3. 连接服务器](#3-连接服务器)
  - [4. 操作说明](#4-操作说明)
- [服务器端部署](#服务器端部署)
- [常见问题](#常见问题)
- [联系方式](#联系方式)

---

## 功能简介
- 支持拼接大图（原图/掩码/修剪图）自动等宽裁剪，生成"原图/蒙版图/标注图/裁剪图"四图展示（支持横向和宫格两种布局）。
- 支持自定义分类按钮和快捷键（默认提供8个分类选项，可自定义启用/禁用）。
- 支持撤销操作、快捷键操作、图片缩放、拖动、方向键平移。
- 实时显示前景占比信息，帮助用户更好地进行分类决策。
- 界面美观，深色风格，支持窗口自适应和布局切换。
- 支持多用户协作，通过Token区分不同用户的数据。

## 项目架构

本项目采用客户端-服务器架构：

- `client/` - Web客户端，通过浏览器访问，连接服务器获取任务
- `server/` - 服务器端，负责任务分发、进度跟踪和结果收集
- `old/` - 早期的本地工具版本（独立运行，无需网络，已废弃）

## 工作模式

1. 服务器端准备任务文件并启动服务
2. 客户端通过浏览器访问服务器，使用Token验证身份
3. 客户端获取分配的任务，开始处理图片
4. 客户端实时上传进度和分类结果到服务器
5. 管理员可在服务器端查看所有用户的进度和结果

> 当前版本需要服务器支持。本地独立运行版本正在开发中。（本地可以使用old/的老版本，后续将老版本设为独立仓库）
---

## 客户端使用说明

### 1. 环境准备

确保已安装 Python 3.7+ 和必要的依赖库：

```bash
pip install flask requests pillow numpy
```

### 2. 运行客户端

在命令行进入项目目录，运行客户端：

```bash
cd client
python client_web.py
```

客户端默认运行在 `http://localhost:5001`

### 3. 连接服务器

1. 打开浏览器，访问 `http://localhost:5001`
2. 输入服务器地址（如 `http://localhost:5000`）
3. 输入个人Token（由服务器管理员提供）
4. 点击"连接服务器"按钮

### 4. 操作说明

- **图片展示区**：展示"原图/蒙版图/标注图/裁剪图"四图
- **分类按钮**：点击分类按钮或使用数字快捷键对图片进行分类
- **撤销**：点击"撤销"按钮或使用 Ctrl+Z 撤销上一步操作
- **布局切换**：使用右上角按钮切换横向布局和宫格布局
- **缩放操作**：
    - 鼠标滚轮：缩放图片
    - +/-按钮：缩放图片
    - 双击图片：重置视图
- **拖动平移**：按住鼠标左键拖动图片
- **方向键**：微调图片位置
- **设置功能**：
    - 点击右下角齿轮图标打开设置面板
    - 可自定义分类按钮名称和快捷键（1-9数字键）
    - 可选择启用/禁用分类按钮
- **前景占比**：左上角显示当前图片的前景占比信息

---

## 服务器端部署

服务器端采用Flask框架构建，负责任务分发、进度跟踪和结果收集。

### 部署步骤

1. 安装依赖：
```bash
cd server
pip install flask
```

2. 准备任务数据：
- 将用户任务文件放入[client_task_list/](file:///c:/Users/Administrator/Desktop/Piexl_sort/server/client_task_list)目录，文件名格式为`task_{token}.json`
- 配置[token.txt](file://c:/Users/Administrator/Desktop/Piexl_sort/server/token.txt)文件，每行一个有效token

3. 启动服务器：
```bash
# 开发模式（Flask内置服务器）
python server_online.py

# 生产模式（自动检测环境并推荐合适的服务器）
python server_online.py prod

# 明确指定使用Waitress（跨平台兼容）
python server_online.py waitress

# 明确指定使用Gunicorn（仅Linux/macOS）
python server_online.py gunicorn
```

服务器默认运行在 `http://localhost:5000`

### 跨平台部署方案

本项目支持在Windows、Linux和macOS上部署，不同平台推荐使用不同的WSGI服务器以获得最佳性能：

#### Windows平台
推荐使用Waitress，它是纯Python实现，与Windows兼容性最好：
```bash
# 安装
pip install waitress

# 运行
python server_online.py prod
# 或明确指定
python server_online.py waitress
```

#### Linux/macOS平台
推荐使用Gunicorn，它是专门为Unix系统设计的高性能WSGI服务器：
```bash
# 安装
pip install gunicorn

# 运行
python server_online.py prod
# 或明确指定
python server_online.py gunicorn

# 也可以直接使用gunicorn命令
gunicorn -w 4 -b 0.0.0.0:5000 server_online:app
```

### 生产环境部署选项

对于生产环境，建议使用以下更高效的服务器：

#### 1. Waitress（Windows推荐，跨平台兼容）
Waitress是一个纯Python编写的WSGI服务器，具有以下特点：
- 跨平台兼容性好，特别适合Windows环境
- 配置简单，易于部署
- 性能优于Flask内置开发服务器
- 支持多线程处理并发请求

```bash
pip install waitress
python server_online.py prod
```

#### 2. Gunicorn（Linux/macOS推荐）
Gunicorn是专门为Unix系统设计的高性能WSGI服务器，具有以下特点：
- 在Unix系统上性能优异
- 支持多种工作模式（同步、异步）
- 配置选项丰富
- 易于与Nginx等反向代理集成

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 server_online:app
```

#### 3. uWSGI
uWSGI是一个功能齐全的应用服务器，适用于复杂的生产环境：
```bash
pip install uwsgi
# 创建uwsgi.ini配置文件后运行
uwsgi --ini uwsgi.ini
```


### 目录结构说明

- `client_task_list/` - 用户任务文件目录（每个用户一个任务文件）
- `client_classified` - 用户分类结果目录
- `client_progress/` - 用户进度记录目录
- `json_data/` - 服务器数据目录

### API接口说明

- `POST /auth` - Token验证接口
- `GET /get_task` - 获取用户任务接口
- `GET /get_image` - 获取图片数据接口
- `POST /upload_progress` - 上传进度接口
- `POST /upload_classified` - 上传分类结果接口

---

## 常见问题

- **Q: 连接服务器失败？**
  - 请确认服务器地址和Token正确
  - 检查网络连接是否正常
  - 确认服务器是否正在运行
  
- **Q: 图片未显示？**
  - 请确认图片格式是否支持（jpg/png/bmp/gif）
  - 检查图片是否被其他程序占用
  
- **Q: 如何批量撤销？**
  - 目前支持逐步撤销，可通过多次点击撤销按钮实现
  
- **Q: 前景占比是什么？**
  - 前景占比表示蒙版图中前景区域占整个图片的比例，帮助判断图片内容质量

---

## 联系方式

- GitHub: [jdhnsu](https://github.com/jdhnsu)
- Issues/建议请在 GitHub 提交

---

> _如需定制功能或遇到问题，欢迎联系作者！_

>_代码70%以下由AI编写，请自行判断!，如果介意AI生成的代码，立即停止使用!_  

>_感谢[OpenAI](https://openai.com/) ,[copilot](https://copilot.github.com/) ,[Qianwen LLM](https://www.qianwen.com/) ,[fittencoder](https://fittencoder.com/) 提供免费AI服务支持！_