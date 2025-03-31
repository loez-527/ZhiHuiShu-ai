# gui.py
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import configparser
import os
import sys
import threading
from io import StringIO
from subprocess import Popen, PIPE
from main import main  # 请将main_program替换为你的主程序文件名


class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = StringIO()
        self.last_line_length = 0  # 记录上一行长度用于覆盖

    def write(self, message):
        # 处理\r的特殊逻辑
        if '\r' in message:
            parts = message.split('\r')
            final_msg = parts[-1]
            # 删除上一行内容
            self.text_widget.delete("end-1l linestart", "end-1c")
            # 插入新内容
            self.text_widget.insert("end-1c", final_msg)
            self.last_line_length = len(final_msg)
        else:
            # 普通写入
            self.text_widget.insert(tk.END, message)
            self.last_line_length = len(message)

        self.text_widget.see(tk.END)
        self.buffer.write(message)

    def flush(self):
        pass


class ConsoleInput:
    def __init__(self, text_widget, input_var):
        self.text_widget = text_widget
        self.input_var = input_var  # 保存变量引用
        self.input_buffer = []

    def readline(self):
        while not self.input_buffer:
            self.input_var.set(False)  # 重置状态
            self.text_widget.mark_set("input_start", "end-1c")
            self.text_widget.insert(tk.END, "\n>> ")
            self.text_widget.mark_gravity("input_start", "left")
            self.text_widget.wait_variable(self.input_var)
        return self.input_buffer.pop(0)



class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("智慧树学习助手")
        self.geometry("800x600")
        self.create_widgets()
        self.load_config()
        self.input_var = tk.BooleanVar(value=False)
        self.console = ConsoleInput(self.console_output, self.input_var)  # 传递变量
        sys.stdin = self.console
        sys.stdout = RedirectText(self.console_output)
        sys.stderr = RedirectText(self.console_output)

    def create_widgets(self):
        # 配置区域
        config_frame = ttk.LabelFrame(self, text="配置设置")
        config_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(config_frame, text="账号:").grid(row=0, column=0, padx=5, pady=2)
        self.username = ttk.Entry(config_frame)
        self.username.grid(row=0, column=1, padx=5, pady=2, sticky=tk.EW)

        ttk.Label(config_frame, text="密码:").grid(row=1, column=0, padx=5, pady=2)
        self.password = ttk.Entry(config_frame, show="*")
        self.password.grid(row=1, column=1, padx=5, pady=2, sticky=tk.EW)
        # 添加显示/隐藏密码按钮
        self.show_password_var = tk.BooleanVar(value=False)
        self.show_password_btn = ttk.Checkbutton(
            config_frame, text="显示密码", variable=self.show_password_var,
            command=lambda: self.toggle_password_visibility()
        )
        self.show_password_btn.grid(row=1, column=2, padx=5, pady=2)

        ttk.Label(config_frame, text="浏览器路径:").grid(row=2, column=0, padx=5, pady=2)
        self.browser_path = ttk.Entry(config_frame, width=50)  # 加长输入框
        self.browser_path.grid(row=2, column=1, padx=5, pady=2, sticky=tk.EW)
        ttk.Button(config_frame, text="浏览", command=self.select_browser).grid(row=2, column=2, padx=5)

        ttk.Label(config_frame, text="课程地址:").grid(row=3, column=0, padx=5, pady=2)
        self.course_url = ttk.Entry(config_frame, width=50)  # 加长输入框
        self.course_url.grid(row=3, column=1, padx=5, pady=2, sticky=tk.EW)

        # 按钮区域
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(btn_frame, text="保存配置", command=self.save_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="开始学习", command=self.start_learning).pack(side=tk.LEFT, padx=2)

        # 控制台区域
        console_frame = ttk.LabelFrame(self, text="控制台")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.console_output = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD)
        self.console_output.pack(fill=tk.BOTH, expand=True)
        # 移除 self.console_output.input_var = tk.StringVar()
        # 改为在控件创建后添加标记
        self.console_output.mark_set("input_start", "end")
        self.console_output.mark_gravity("input_start", "left")
        self.console_output.bind("<Return>", self.process_input)

        # 新增方法：切换密码显示/隐藏
    def toggle_password_visibility(self):
            if self.show_password_var.get():
                self.password.config(show="")
            else:
                self.password.config(show="*")
    # 修改process_input方法
    def process_input(self, event):
        input_text = self.console_output.get("input_start", "end-1c").split(">> ")[-1]
        self.console.input_buffer.append(input_text + "\n")
        self.input_var.set(not self.input_var.get())  # 切换布尔值触发变化
        return "break"

    def select_browser(self):
        path = filedialog.askopenfilename()
        if path:
            self.browser_path.delete(0, tk.END)
            self.browser_path.insert(0, path)

    def load_config(self):
        config = configparser.ConfigParser()
        if os.path.exists("config.ini"):
            config.read("config.ini")
            self.username.insert(0, config.get("Credentials", "username", fallback=""))
            self.password.insert(0, config.get("Credentials", "password", fallback=""))
            self.browser_path.insert(0, config.get("Browser", "chrome_path", fallback=""))
            self.course_url.insert(0, config.get("Course", "url", fallback=""))

    def save_config(self):
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
        with open("config.ini", "w") as f:
            config.write(f)
        print("配置已保存！")

    def start_learning(self):
        def run_main():
            try:
                main({
                    'username': self.username.get(),
                    'password': self.password.get(),
                    'chrome_path': self.browser_path.get(),
                    'course_url': self.course_url.get()
                })
            except Exception as e:
                print(f"发生错误: {str(e)}")

        thread = threading.Thread(target=run_main, daemon=True)
        thread.start()


if __name__ == "__main__":
    app = Application()
    app.mainloop()