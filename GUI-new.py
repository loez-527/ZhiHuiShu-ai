# gui.py
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import configparser
import os
import sys
import threading
import logging
from io import StringIO
from typing import Optional, Dict, Any
from ai import main  # 请将main_program替换为你的主程序文件名
from about import AboutWindow  # 导入关于窗口类
import webbrowser
import subprocess
from PIL import Image, ImageTk  # 添加PIL导入用于处理图像

# 设置现代化主题
def setup_modern_theme():
    style = ttk.Style()
    style.theme_use('clam')  # 使用clam主题作为基础
    
    # 配置颜色
    bg_color = "#ffffff"
    accent_color = "#00bfa5"  # 更改为青绿色
    hover_color = "#008e76"  # 更改为深一点的青绿色
    text_color = "#333333"
    
    # 配置通用样式
    style.configure(".", 
        background=bg_color,
        foreground=text_color,
        font=('Microsoft YaHei UI', 11))
    
    # 配置标签样式
    style.configure("TLabel",
        padding=3,
        font=('Microsoft YaHei UI', 11))
    
    # 配置按钮样式
    style.configure("TButton",
        padding=4,
        background=accent_color,
        foreground="white",
        font=('Microsoft YaHei UI', 11))
    
    # 配置按钮悬停效果
    style.map("TButton",
        background=[('active', hover_color)],
        foreground=[('active', 'white')])
    
    # 配置复选框样式
    style.configure("TCheckbutton",
        padding=3,
        font=('Microsoft YaHei UI', 11),
        background=bg_color)
    
    # 配置复选框选中状态样式
    style.map("TCheckbutton",
        background=[('active', bg_color)],
        foreground=[('active', text_color)],
        indicatorcolor=[('selected', accent_color), ('!selected', bg_color)],
        indicatorrelief=[('pressed', 'sunken'), ('!pressed', 'flat')])
    
    # 配置输入框样式
    style.configure("TEntry",
        padding=3,
        fieldbackground=bg_color)
    
    # 配置框架样式
    style.configure("TLabelframe",
        background=bg_color,
        padding=8)
    
    # 配置标签框架标题样式
    style.configure("TLabelframe.Label",
        font=('Microsoft YaHei UI', 11, 'bold'),
        foreground=accent_color)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class RedirectText:
    def __init__(self, text_widget: scrolledtext.ScrolledText):
        self.text_widget = text_widget
        self.buffer = StringIO()
        self.last_line_length = 0

    def write(self, message: str) -> None:
        try:
            if '\r' in message:
                parts = message.split('\r')
                final_msg = parts[-1]
                self.text_widget.delete("end-1l linestart", "end-1c")
                self.text_widget.insert("end-1c", final_msg)
                self.last_line_length = len(final_msg)
            else:
                self.text_widget.insert(tk.END, message)
                self.last_line_length = len(message)

            self.text_widget.see(tk.END)
            self.buffer.write(message)
        except Exception as e:
            logging.error(f"写入文本时发生错误: {str(e)}")

    def flush(self) -> None:
        pass


class ConsoleInput:
    def __init__(self, text_widget: scrolledtext.ScrolledText, input_var: tk.BooleanVar):
        self.text_widget = text_widget
        self.input_var = input_var
        self.input_buffer = []

    def readline(self) -> str:
        while not self.input_buffer:
            self.input_var.set(False)
            self.text_widget.mark_set("input_start", "end-1c")
            self.text_widget.insert(tk.END, "\n>> ")
            self.text_widget.mark_gravity("input_start", "left")
            self.text_widget.wait_variable(self.input_var)
        return self.input_buffer.pop(0)



class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("智慧树AI助手v4.1")
        self.geometry("900x700")  # 增加窗口大小
        self.configure(bg="#ffffff")  # 设置白色背景
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 设置窗口图标
        self.set_window_icon()
        
        # 设置现代化主题
        setup_modern_theme()
        
        # 初始化变量
        self.input_var = tk.BooleanVar(value=False)
        self.show_password_var = tk.BooleanVar(value=False)
        self.is_running = False
        self.always_on_top = tk.BooleanVar(value=False)  # 添加置顶状态变量
        
        # 创建菜单栏
        self.create_menu()
        
        # 创建界面
        self.create_widgets()
        self.load_config()
        
        # 设置控制台重定向
        self.console = ConsoleInput(self.console_output, self.input_var)
        sys.stdin = self.console
        sys.stdout = RedirectText(self.console_output)
        sys.stderr = RedirectText(self.console_output)

    def set_window_icon(self):
        """设置窗口图标"""
        try:
            # 获取图标路径
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons", "ico.png")
            if os.path.exists(icon_path):
                # 在Windows下设置图标
                if sys.platform == 'win32':
                    # 使用PhotoImage设置图标，因为没有ico文件
                    icon = tk.PhotoImage(file=icon_path)
                    self.iconphoto(True, icon)
                # 在其他平台使用PhotoImage设置图标
                else:
                    icon = tk.PhotoImage(file=icon_path)
                    self.iconphoto(True, icon)
                logging.info("已成功加载应用图标")
            else:
                logging.warning(f"未找到图标文件: {icon_path}")
        except Exception as e:
            logging.error(f"设置窗口图标时发生错误: {str(e)}")

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # 首页菜单
        menubar.add_command(label="首页", command=self.return_home)
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="使用教程", command=self.show_tutorial)
        help_menu.add_command(label="常见问题", command=self.show_faq)
        
        # 关于菜单
        about_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="关于", menu=about_menu)
        about_menu.add_command(label="关于软件", command=self.show_about)
        about_menu.add_command(label="官方网站", command=lambda: webbrowser.open("https://zhs.loez.store/"))

    def return_home(self):
        """返回主页"""
        # 清空控制台输出
        self.console_output.delete(1.0, tk.END)
        print("欢迎使用本项目૮(˶ᵔ ᵕ ᵔ˶)ა")
        print("本项目完全免费！如果觉得不错就打赏一下吧૮(˶ᵔ ᵕ ᵔ˶)ა")
        print("使用前请先查看README文档")
        print("遇到问题请打包好两个日志文件发送至下方邮箱⬇️")
        print("loez-527@outlook.com 或 3466017194@qq.com")
        print('-' * 40)

    def show_tutorial(self):
        """显示使用教程"""
        tutorial_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "使用教程.mp4")
        if os.path.exists(tutorial_path):
            try:
                if sys.platform == 'win32':
                    os.startfile(tutorial_path)
                elif sys.platform == 'darwin':  # macOS
                    subprocess.run(['open', tutorial_path])
                else:  # Linux
                    subprocess.run(['xdg-open', tutorial_path])
            except Exception as e:
                logging.error(f"打开教程视频时发生错误: {str(e)}")
                messagebox.showerror("错误", f"打开教程视频失败: {str(e)}")
        else:
            messagebox.showwarning("警告", "未找到教程视频文件，请确保'使用教程.mp4'文件存在于程序目录中。")

    def show_faq(self):
        """显示常见问题"""
        faq_text = """Q: 为什么程序无法启动？
A: 请确保电脑安装chrome、edge等WebKit 内核 (Chrome)。

Q: 加载慢或长时间页面没有变化？
A: 这是对方服务器问题，可以等一会再刷或者换个网络（刷新ip）。

Q: 如何更新到最新版本？
A: 访问官方网站下载。

Q: 刷完掌握度或进度怎么不继续了？
A: 是这样设计的,按需学习，可以点开始学习再重新选择。

Q: 遇到问题如何反馈？
A: 请发送日志文件至指定邮箱"""
        messagebox.showinfo("常见问题", faq_text)

    def check_update(self):
        """检查更新"""
        webbrowser.open("https://github.com/your-repo/zhihuishu/releases")

    def create_widgets(self):
        # 创建主框架
        main_frame = ttk.Frame(self, padding="15")  # 减小外边距
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="配置设置", padding="10")  # 减小内边距
        config_frame.pack(fill=tk.X, pady=(0, 10))  # 减小间距

        # 创建网格布局
        config_frame.columnconfigure(1, weight=1)

        # 账号密码区域
        self._create_credential_widgets(config_frame)
        
        # 浏览器和课程URL区域
        self._create_browser_widgets(config_frame)
        
        # 按钮区域
        self._create_button_widgets(main_frame)
        
        # 控制台区域
        self._create_console_widgets(main_frame)

    def _create_credential_widgets(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="账号:").grid(row=0, column=0, padx=3, pady=1, sticky=tk.W)  # 减小间距
        self.username = ttk.Entry(parent)
        self.username.grid(row=0, column=1, padx=3, pady=1, sticky=tk.EW)  # 减小间距

        ttk.Label(parent, text="密码:").grid(row=1, column=0, padx=3, pady=1, sticky=tk.W)  # 减小间距
        self.password = ttk.Entry(parent, show="*")
        self.password.grid(row=1, column=1, padx=3, pady=1, sticky=tk.EW)  # 减小间距
        
        self.show_password_btn = ttk.Checkbutton(
            parent, text="显示密码", variable=self.show_password_var,
            command=self.toggle_password_visibility
        )
        self.show_password_btn.grid(row=1, column=2, padx=3, pady=1)  # 减小间距

    def _create_browser_widgets(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="浏览器路径:").grid(row=2, column=0, padx=3, pady=1, sticky=tk.W)  # 减小间距
        self.browser_path = ttk.Entry(parent)
        self.browser_path.grid(row=2, column=1, padx=3, pady=1, sticky=tk.EW)  # 减小间距
        ttk.Button(parent, text="浏览", command=self.select_browser).grid(row=2, column=2, padx=3, pady=1)  # 减小间距

        ttk.Label(parent, text="课程地址:").grid(row=3, column=0, padx=3, pady=1, sticky=tk.W)  # 减小间距
        self.course_url = ttk.Entry(parent)
        self.course_url.grid(row=3, column=1, padx=3, pady=1, sticky=tk.EW)  # 减小间距

    def _create_button_widgets(self, parent: ttk.Frame) -> None:
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=3)
        
        # 左侧按钮
        left_btn_frame = ttk.Frame(btn_frame)
        left_btn_frame.pack(side=tk.LEFT)
        
        self.save_btn = ttk.Button(left_btn_frame, text="保存配置", command=self.save_config)
        self.save_btn.pack(side=tk.LEFT, padx=2)
        
        self.start_btn = ttk.Button(left_btn_frame, text="开始学习", command=self.start_learning)
        self.start_btn.pack(side=tk.LEFT, padx=2)
        
        # 右侧按钮
        right_btn_frame = ttk.Frame(btn_frame)
        right_btn_frame.pack(side=tk.RIGHT)
        
        self.top_btn = ttk.Checkbutton(
            right_btn_frame,
            text="窗口置顶",
            variable=self.always_on_top,
            command=self.toggle_always_on_top
        )
        self.top_btn.pack(side=tk.RIGHT, padx=2)

    def _create_console_widgets(self, parent: ttk.Frame) -> None:
        console_frame = ttk.LabelFrame(parent, text="控制台", padding="10")  # 减小内边距
        console_frame.pack(fill=tk.BOTH, expand=True)

        self.console_output = scrolledtext.ScrolledText(
            console_frame,
            wrap=tk.WORD,
            font=('Consolas', 11),  # 增大字体
            bg="#f8f9fa",
            fg="#333333",
            padx=8,  # 减小内边距
            pady=8   # 减小内边距
        )
        self.console_output.pack(fill=tk.BOTH, expand=True)
        self.console_output.mark_set("input_start", "end")
        self.console_output.mark_gravity("input_start", "left")
        self.console_output.bind("<Return>", self.process_input)

    def toggle_password_visibility(self) -> None:
        self.password.config(show="" if self.show_password_var.get() else "*")

    def process_input(self, event: tk.Event) -> str:
        try:
            input_text = self.console_output.get("input_start", "end-1c").split(">> ")[-1]
            self.console.input_buffer.append(input_text + "\n")
            self.input_var.set(not self.input_var.get())
        except Exception as e:
            logging.error(f"处理输入时发生错误: {str(e)}")
        return "break"

    def select_browser(self) -> None:
        try:
            path = filedialog.askopenfilename(
                title="选择浏览器",
                filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")]
            )
            if path:
                self.browser_path.delete(0, tk.END)
                self.browser_path.insert(0, path)
        except Exception as e:
            logging.error(f"选择浏览器时发生错误: {str(e)}")
            messagebox.showerror("错误", f"选择浏览器时发生错误: {str(e)}")

    def load_config(self) -> None:
        try:
            config = configparser.ConfigParser()
            if os.path.exists("config.ini"):
                config.read("config.ini", encoding="utf-8")
                self.username.insert(0, config.get("Credentials", "username", fallback=""))
                self.password.insert(0, config.get("Credentials", "password", fallback=""))
                self.browser_path.insert(0, config.get("Browser", "chrome_path", fallback=""))
                self.course_url.insert(0, config.get("Course", "url", fallback=""))
        except Exception as e:
            logging.error(f"加载配置时发生错误: {str(e)}")
            messagebox.showerror("错误", f"加载配置时发生错误: {str(e)}")

    def save_config(self) -> None:
        try:
            config = configparser.ConfigParser()
            config["Credentials"] = {
                "username": self.username.get(),
                "password": self.password.get()
            }
            config["Browser"] = {
                "chrome_path": self.browser_path.get()
            }
            config["Course"] = {
                "url": self.course_url.get()
            }
            
            with open("config.ini", "w", encoding="utf-8") as f:
                config.write(f)
            
            messagebox.showinfo("成功", "配置已保存！")
            logging.info("配置已保存")
        except Exception as e:
            logging.error(f"保存配置时发生错误: {str(e)}")
            messagebox.showerror("错误", f"保存配置时发生错误: {str(e)}")

    def start_learning(self) -> None:
        if self.is_running:
            messagebox.showwarning("警告", "程序正在运行中，请等待当前任务完成")
            return

        if not self._validate_inputs():
            return

        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        
        def run_main():
            try:
                main({
                    'username': self.username.get(),
                    'password': self.password.get(),
                    'chrome_path': self.browser_path.get(),
                    'course_url': self.course_url.get()
                })
            except Exception as e:
                logging.error(f"运行主程序时发生错误: {str(e)}")
                messagebox.showerror("错误", f"运行程序时发生错误: {str(e)}")
            finally:
                self.is_running = False
                self.start_btn.config(state=tk.NORMAL)

        thread = threading.Thread(target=run_main, daemon=True)
        thread.start()

    def _validate_inputs(self) -> bool:
        if not self.username.get() or not self.password.get():
            messagebox.showwarning("警告", "请输入账号和密码")
            return False
        if not self.course_url.get():
            messagebox.showwarning("警告", "请输入课程地址")
            return False
        return True

    def on_closing(self) -> None:
        if self.is_running:
            if messagebox.askokcancel("确认", "程序正在运行中，确定要退出吗？"):
                self.destroy()
        else:
            self.destroy()

    def toggle_always_on_top(self):
        """切换窗口置顶状态"""
        self.attributes('-topmost', self.always_on_top.get())

    def show_about(self):
        """显示关于窗口"""
        about_window = AboutWindow(self)
        # 如果图标文件存在，设置关于窗口的图标
        try:
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icons", "ico.png")
            if os.path.exists(icon_path):
                # 使用PhotoImage设置图标
                icon = tk.PhotoImage(file=icon_path)
                about_window.iconphoto(True, icon)
        except Exception as e:
            logging.error(f"设置关于窗口图标时发生错误: {str(e)}")

if __name__ == "__main__":
    try:
        app = Application()
        print("欢迎使用本项目૮(˶ᵔ ᵕ ᵔ˶)ა")
        print("本项目完全免费！如果觉得不错就打赏一下吧૮(˶ᵔ ᵕ ᵔ˶)ა")
        print("使用前请先查看README文档")
        print("遇到问题请打包好两个日志文件发送至下方邮箱⬇️")
        print("loez-527@outlook.com 或 3466017194@qq.com")
        print('-' * 40)
        app.mainloop()
    except Exception as e:
        logging.critical(f"程序启动时发生严重错误: {str(e)}")
        messagebox.showerror("严重错误", f"程序启动失败: {str(e)}")