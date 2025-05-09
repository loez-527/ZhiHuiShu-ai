import tkinter as tk
from tkinter import ttk
import webbrowser
from PIL import Image, ImageTk
import os

class AboutWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("关于智慧树学习助手")
        self.geometry("500x500")  # 增加窗口高度以容纳图片
        self.configure(bg="#ffffff")
        
        # 设置窗口图标和模态
        self.transient(parent)
        self.grab_set()
        
        # 创建主框架
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="智慧树学习助手",
            font=('Microsoft YaHei UI', 16, 'bold')
        )
        title_label.pack(pady=(0, 20))
        
        # 版本信息
        version_label = ttk.Label(
            main_frame,
            text="版本：4.0.0",
            font=('Microsoft YaHei UI', 10)
        )
        version_label.pack(pady=(0, 20))
        
        # 添加二维码图片
        try:
            # 获取当前脚本所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            qr_path = os.path.join(current_dir, "assets", "qrcode.png")
            
            # 加载并显示图片
            qr_image = Image.open(qr_path)
            qr_image = qr_image.resize((300, 300), Image.Resampling.LANCZOS)  # 调整图片大小为200x200像素
            self.qr_photo = ImageTk.PhotoImage(qr_image)
            
            qr_label = ttk.Label(main_frame, image=self.qr_photo)
            qr_label.pack(pady=(0, 20))
            
            # 添加扫码提示文字
            qr_text = ttk.Label(
                main_frame,
                text="扫码关注获取更多帮助",
                font=('Microsoft YaHei UI', 10)
            )
            qr_text.pack(pady=(0, 20))
        except Exception as e:
            print(f"加载二维码图片失败: {e}")
        
        # 项目说明
        description_text = """
本项目是一个自动化学习工具，旨在帮助用户高效地完成智慧树的学习任务。
"""
        description = tk.Text(
            main_frame,
            wrap=tk.WORD,
            font=('Microsoft YaHei UI', 10),
            height=12,
            bg="#f8f9fa",
            relief=tk.FLAT
        )
        description.insert(tk.END, description_text)
        description.configure(state='disabled')
        description.pack(pady=(0, 20), fill=tk.X)
        
        # 链接框架
        link_frame = ttk.Frame(main_frame)
        link_frame.pack(fill=tk.X)
        
        # 文档链接
        doc_link = ttk.Label(
            link_frame,
            text="查看详细文档",
            font=('Microsoft YaHei UI', 10),
            foreground="#007AFF",
            cursor="hand2"
        )
        doc_link.pack(side=tk.LEFT, padx=5)
        doc_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/your-repo/zhihuishu"))
        
        # 更新链接
        update_link = ttk.Label(
            link_frame,
            text="检查更新",
            font=('Microsoft YaHei UI', 10),
            foreground="#007AFF",
            cursor="hand2"
        )
        update_link.pack(side=tk.LEFT, padx=5)
        update_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/your-repo/zhihuishu/releases"))
        
        # 关闭按钮
        close_btn = ttk.Button(
            main_frame,
            text="关闭",
            command=self.destroy
        )
        close_btn.pack(pady=(20, 0))
        
        # 居中显示
        self.center_window()
    
    def center_window(self):
        """将窗口居中显示"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}') 