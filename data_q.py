import os
import shutil
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from PIL import Image, ImageTk
import tkinter.ttk as ttk

# 设置分类文件夹
categories = ['清洗', '保留', '阴影', '遮挡']
image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif']

# 获取当前目录所有图片
def get_image_files():
    return [f for f in os.listdir('.') if os.path.splitext(f)[1].lower() in image_extensions]

# 创建分类文件夹（如果不存在）
def create_folders():
    for category in categories:
        if not os.path.exists(category):
            os.makedirs(category)

class ImageSorter:
    def setup_style(self):
        style = ttk.Style()
        style.theme_use('clam')
        # Material 3 Expressive 主色调
        primary = "#6750A4"
        on_primary = "#FFFFFF"
        surface = "#23272F"  # 深灰
        secondary = "#353945"
        on_surface = "#F5F6FA"  # 浅灰字体
        accent = "#7D5260"
        # 按钮
        style.configure('TButton',
                        font=('SegoeUI', 12),
                        background=primary,
                        foreground=on_primary,
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor=accent,
                        padding=8)
        style.map('TButton',
                  background=[('active', secondary), ('pressed', accent)])
        style.configure('Rounded.TButton',
                        font=('SegoeUI', 12),
                        background=primary,
                        foreground=on_primary,
                        borderwidth=0,
                        relief='flat',
                        padding=8)
        style.configure('TMenubutton',
                        font=('SegoeUI', 12),
                        background=secondary,
                        foreground=on_surface,
                        borderwidth=0,
                        padding=8)
        style.configure('TLabel',
                        font=('SegoeUI', 12),
                        background=surface,
                        foreground=on_surface)
        self.root.option_add("*Font", "SegoeUI 12")

    def __init__(self, root):
        self.root = root
        self.root.title("图片分类工具 - 数据清洗")
        self.root.geometry("1468x736")
        self.root.configure(bg="#23272F")
        self.setup_style()
        self.image_files = get_image_files()
        self.total_count = len(self.image_files)  # 记录总数
        self.index = 0
        self.history = []  # 记录历史操作
        self.scale = 1.0   # 当前缩放比例
        self.min_scale = 0.1
        self.max_scale = 5.0
        self.img = None    # 当前PIL图片对象
        self.tk_img = None # 当前Tk图片对象
        self.offset_x = 0  # 平移偏移
        self.offset_y = 0
        self.drag_data = {'x': 0, 'y': 0, 'dragging': False}
        try:
            self.resample_method = Image.Resampling.LANCZOS
        except AttributeError:
            self.resample_method = Image.ANTIALIAS
        self.label_cache = {}  # 缓存已生成的四图拼接图

        # 先显示选择图片界面
        if self.image_files:
            self.show_start_image_selector()
        else:
            self.init_main_ui()
            self.load_image()

    def show_start_image_selector(self):
        self.selector_frame = tk.Frame(self.root, bg="#23272F")
        self.selector_frame.pack(expand=True, fill='both')
        tk.Label(self.selector_frame, text="请选择开始图片：", font=("SegoeUI", 14, "bold"), bg="#23272F", fg="#F5F6FA").pack(padx=10, pady=16)
        list_frame = tk.Frame(self.selector_frame, bg="#23272F")
        list_frame.pack(padx=10, pady=8, fill='both', expand=True)
        self.start_var = tk.StringVar(value=self.image_files[0])
        self.listbox = tk.Listbox(list_frame, listvariable=tk.StringVar(value=self.image_files),
                                  selectmode='browse', height=12, width=40, bg="#23272F", fg="#F5F6FA", font=("SegoeUI", 12),
                                  highlightthickness=0, selectbackground="#6750A4", selectforeground="#FFFFFF")
        self.listbox.pack(side='left', fill='both', expand=True)
        self.listbox.selection_set(0)
        scrollbar = tk.Scrollbar(list_frame, orient='vertical', command=self.listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.bind('<Double-Button-1>', lambda e: self.on_start_image_selected())
        self.listbox.bind('<MouseWheel>', self.on_listbox_mousewheel)
        ok_btn = ttk.Button(self.selector_frame, text="确定", style='Rounded.TButton', command=self.on_start_image_selected)
        ok_btn.pack(pady=18, ipadx=16, ipady=4)

    def on_listbox_mousewheel(self, event):
        self.listbox.yview_scroll(-1 * int(event.delta / 120), 'units')

    def on_start_image_selected(self):
        sel = self.listbox.curselection()
        if sel:
            start_img = self.image_files[sel[0]]
        else:
            start_img = self.image_files[0]
        self.index = self.image_files.index(start_img)
        self.selector_frame.destroy()
        self.init_main_ui()
        self.load_image()

    def init_main_ui(self):
        self.canvas = tk.Canvas(self.root, bg='#000000', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True, padx=16, pady=12)
        self.canvas_img = None
        self.canvas.bind('<ButtonPress-1>', self.on_drag_start)
        self.canvas.bind('<B1-Motion>', self.on_drag_move)
        self.canvas.bind('<ButtonRelease-1>', self.on_drag_end)
        self.canvas.bind('<MouseWheel>', self.mousewheel_zoom)
        # 方向键绑定到canvas，确保有焦点时可用
        self.canvas.bind('<Left>', lambda e: self.arrow_pan(-40, 0))
        self.canvas.bind('<Right>', lambda e: self.arrow_pan(40, 0))
        self.canvas.bind('<Up>', lambda e: self.arrow_pan(0, -40))
        self.canvas.bind('<Down>', lambda e: self.arrow_pan(0, 40))
        self.canvas.focus_set()
        self.button_frame = tk.Frame(self.root, bg="#23272F")
        self.button_frame.pack(pady=14)
        for cat in categories:
            btn = ttk.Button(self.button_frame, text=cat, style='Rounded.TButton', width=10, command=lambda c=cat: self.move_image(c))
            btn.pack(side='left', padx=8, ipadx=8, ipady=4)
        undo_btn = ttk.Button(self.button_frame, text="撤销", style='Rounded.TButton', width=10, command=self.undo)
        undo_btn.pack(side='left', padx=8, ipadx=8, ipady=4)
        self.status_label = ttk.Label(self.root, text="", style='TLabel')
        self.status_label.pack(pady=8)
        # 右下角GitHub
        self.github_frame = tk.Frame(self.root, bg="#23272F")
        self.github_frame.place(relx=1.0, rely=1.0, anchor='se', x=-12, y=-8)
        try:
            from urllib.request import urlopen
            from io import BytesIO
            from PIL import Image as PILImage, ImageTk as PILImageTk
            icon_url = 'https://github.githubassets.com/images/modules/logos_page/GitHub-Mark-Light-32px.png'
            icon_data = urlopen(icon_url).read()
            icon_img = PILImage.open(BytesIO(icon_data))
            self.github_icon = PILImageTk.PhotoImage(icon_img)
            icon_label = tk.Label(self.github_frame, image=self.github_icon, bg="#23272F", cursor="hand2")
            icon_label.pack(side='left')
            icon_label.bind('<Button-1>', lambda e: self.open_github())
        except Exception:
            icon_label = tk.Label(self.github_frame, text="G", fg="#F5F6FA", bg="#23272F", font=("SegoeUI", 14, "bold"), cursor="hand2")
            icon_label.pack(side='left')
            icon_label.bind('<Button-1>', lambda e: self.open_github())
        link_label = tk.Label(self.github_frame, text="Github jdhnsu", fg="#F5F6FA", bg="#23272F", font=("SegoeUI", 10, "underline"), cursor="hand2")
        link_label.pack(side='left', padx=(4,0))
        link_label.bind('<Button-1>', lambda e: self.open_github())

        # 全局快捷键绑定
        self.root.bind_all("1", lambda e: self.move_image("清洗"))
        self.root.bind_all("2", lambda e: self.move_image("保留"))
        self.root.bind_all("3", lambda e: self.move_image("阴影"))
        self.root.bind_all("4", lambda e: self.move_image("遮挡"))
        self.root.bind_all("z", lambda e: self.undo())
        self.root.bind_all("<Control-plus>", self.ctrl_plus)
        self.root.bind_all("<Control-minus>", self.ctrl_minus)
        self.root.bind_all("<Control-equal>", self.ctrl_plus)
        self.root.bind_all("<Configure>", self.on_resize)
        # 方向键全局绑定，兼容所有焦点情况
        self.root.bind_all('<Left>', lambda e: self.arrow_pan(-40, 0))
        self.root.bind_all('<Right>', lambda e: self.arrow_pan(40, 0))
        self.root.bind_all('<Up>', lambda e: self.arrow_pan(0, -40))
        self.root.bind_all('<Down>', lambda e: self.arrow_pan(0, 40))

    def mousewheel_zoom(self, event):
        if event.delta > 0:
            self.ctrl_plus()
        else:
            self.ctrl_minus()

    def load_image(self):
        if self.index >= len(self.image_files):
            self.canvas.delete('all')
            self.status_label.config(text="🎉 所有图片已分类完成！")
            messagebox.showinfo("完成", "所有图片已完成分类。")
            return

        img_path = self.image_files[self.index]
        # 优先从缓存读取
        if img_path in self.label_cache:
            new_img = self.label_cache[img_path]
        else:
            # 批量处理当前段（每段10张）
            seg_size = 10
            seg_start = (self.index // seg_size) * seg_size
            seg_end = min(seg_start + seg_size, len(self.image_files))
            for i in range(seg_start, seg_end):
                path = self.image_files[i]
                if path in self.label_cache:
                    continue
                try:
                    big_img = Image.open(path).convert('RGB')
                    w, h = big_img.size
                    part_w = w // 3
                    orig_img = big_img.crop((0, 0, part_w, h))
                    mask_img = big_img.crop((part_w, 0, part_w * 2, h)).convert('L')
                    crop_img = big_img.crop((part_w * 2, 0, w, h))
                    label_img = orig_img.copy()
                    red = Image.new('RGB', orig_img.size, (255,0,0))
                    label_img = Image.composite(red, label_img, mask_img.point(lambda x: 128 if x > 30 else 0))
                    imgs = [orig_img, mask_img.convert('RGB'), label_img, crop_img]
                    total_w = sum(im.width for im in imgs)
                    max_h = max(im.height for im in imgs)
                    seg_img = Image.new('RGB', (total_w, max_h), (0,0,0))
                    x = 0
                    for im in imgs:
                        seg_img.paste(im, (x, 0))
                        x += im.width
                    self.label_cache[path] = seg_img
                except Exception as e:
                    self.label_cache[path] = None
            new_img = self.label_cache.get(img_path)
            if new_img is None:
                self.canvas.delete('all')
                self.status_label.config(text=f"图片加载失败: {img_path}")
                return
        self.img = new_img
        self.offset_x = 0
        self.offset_y = 0
        self.render_image()
        done = self.total_count - len(self.image_files) + self.index + 1
        self.status_label.config(text=f"当前图片：{img_path} (已分 {done}/{self.total_count}) - 快捷键：1清洗 2保留 3阴影 4遮挡  滚轮/Ctrl +/Ctrl -(缩放)")

    def render_image(self, force_new_img=True):
        if self.img is None:
            return
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        # 如果窗口未布局好，延迟重绘，保证图片居中
        if w < 100 or h < 100:
            self.root.after(50, lambda: self.render_image(force_new_img))
            return
        img_w, img_h = self.img.size
        scale = self.scale
        max_w = int(w * scale)
        max_h = int(h * scale)
        ratio = min(max_w / img_w, max_h / img_h, 1.0 * scale)
        new_size = (max(1, int(img_w * ratio)), max(1, int(img_h * ratio)))
        if force_new_img or self.tk_img is None or self.tk_img.width() != new_size[0] or self.tk_img.height() != new_size[1]:
            img_resized = self.img.resize(new_size, self.resample_method)
            self.tk_img = ImageTk.PhotoImage(img_resized)
            self.canvas.delete('all')
            # 计算中心点+偏移
            cx = w // 2 + self.offset_x
            cy = h // 2 + self.offset_y
            self.canvas_img = self.canvas.create_image(cx, cy, image=self.tk_img)
        else:
            # 只移动图片
            cx = w // 2 + self.offset_x
            cy = h // 2 + self.offset_y
            self.canvas.coords(self.canvas_img, cx, cy)

    def on_drag_start(self, event):
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
        self.drag_data['dragging'] = True

    def on_drag_move(self, event):
        if not self.drag_data['dragging']:
            return
        dx = event.x - self.drag_data['x']
        dy = event.y - self.drag_data['y']
        self.offset_x += dx
        self.offset_y += dy
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
        # 只移动canvas图片，不重建tk_img
        self.render_image(force_new_img=False)

    def on_drag_end(self, event):
        self.drag_data['dragging'] = False

    def move_image(self, category):
        img_path = self.image_files[self.index]
        self.history.append((img_path, self.index, category))
        shutil.move(img_path, os.path.join(category, img_path))
        del self.image_files[self.index]
        self.load_image()

    def undo(self):
        if not self.history:
            messagebox.showinfo("提示", "没有可撤销的操作！")
            return
        last_img, last_index, last_category = self.history.pop()
        src = os.path.join(last_category, last_img)
        dst = last_img
        if os.path.exists(src):
            shutil.move(src, dst)
        if last_img in self.image_files:
            self.image_files.remove(last_img)
        self.image_files.insert(last_index, last_img)
        self.index = last_index
        self.load_image()

    def ctrl_plus(self, event=None):
        self.scale = min(self.max_scale, self.scale * 1.1)
        self.render_image(force_new_img=True)

    def ctrl_minus(self, event=None):
        self.scale = max(self.min_scale, self.scale / 1.1)
        self.render_image(force_new_img=True)

    def ctrl_mousewheel(self, event):
        pass  # 兼容保留，不再绑定

    def open_github(self):
        import webbrowser
        webbrowser.open('https://github.com/jdhnsu')

    def on_resize(self, event):
        self.render_image(force_new_img=True)

    def arrow_pan(self, dx, dy):
        self.offset_x += dx
        self.offset_y += dy
        self.render_image(force_new_img=False)

# 运行程序
if __name__ == "__main__":
    create_folders()
    root = tk.Tk()
    app = ImageSorter(root)
    root.mainloop()
