import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import logging
import random
import webbrowser
import re
from ai_chat_tab import AIChatTab
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import traceback
import time
import numpy as np
import requests
import openai
import json
from ai_questionnaire_parser import ai_parse_questionnaire
import os
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, \
    ElementNotInteractableException
from ttkthemes import ThemedTk
from PIL import Image, ImageTk
import sv_ttk  # 用于现代主题
import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
# ================== 配置参数 ==================
# 默认参数值
DEFAULT_CONFIG = {
    "url": "https://www.wjx.cn/vm/OaRP2BF.aspx",
    "target_num": 100,
    "min_duration":1,
    "max_duration":20,
    "weixin_ratio": 0.5,
    "min_delay": 1,
    "max_delay": 2,
    "submit_delay": 1,
    "page_load_delay": 2,
    "per_question_delay": (0.5, 1),
    "min_submit_gap": 5,  # 单份提交最小间隔（分钟）
    "max_submit_gap": 15,  # 单份提交最大间隔（分钟）
    "batch_size": 5,  # 每N份后暂停
    "batch_pause": 15,  # 批量暂停M分钟
    "per_page_delay": (2.0, 6.0),
    "enable_smart_gap": True,  # 智能提交间隔开关

    "headless": False,
    "num_threads": 4,
    "use_ip": False,
    "ip_api": "https://service.ipzan.com/core-extract?num=1&minute=1&pool=quality&secret=YOUR_SECRET",
    "ip_change_mode": "per_submit",  # 新增, 可选: per_submit, per_batch
    "ip_change_batch": 5,  # 每N份切换, 仅per_batch有效


    # 单选题概率配置
    "single_prob": {
        "1": -1,  # -1表示随机选择
        "2": [0.3, 0.7],  # 数组表示每个选项的选择概率
        "3": [0.2, 0.2, 0.6]
    },
    "other_texts": {
        # 题号: [可选的其他文本1, 2, 3...]
        "4": ["自定义内容A", "自定义内容B", "自定义内容C"],
        "5": ["随便写点", "哈哈哈", "其他情况"]
    },
    # 多选题概率配置 - 增强版
    "multiple_prob": {
        "4": {
            "prob": [0.4, 0.3, 0.3],  # 每个选项被选中的概率
            "min_selection": 1,  # 最小选择项数
            "max_selection": 2  # 最大选择项数
        },
        "5": {
            "prob": [0.5, 0.5, 0.5, 0.5],
            "min_selection": 2,
            "max_selection": 3
        }
    },
    "ai_service": "质谱清言",
    "ai_fill_enabled": False,
    "openai_api_key": "",
    "qingyan_api_key": "",
    "ai_prompt_template": "请用简洁、自然的中文回答：{question}",
    # 矩阵题概率配置
    "matrix_prob": {
        "6": [0.2, 0.3, 0.5],  # 每行选项的选择概率
        "7": -1  # -1表示随机选择
    },

    # 量表题概率配置
    "scale_prob": {
        "8": [0.1, 0.2, 0.4, 0.2, 0.1],  # 每个刻度的选择概率
        "9": [0.2, 0.2, 0.2, 0.2, 0.2]
    },

    # 填空题答案配置
    "texts": {
        "10": ["示例答案1", "示例答案2", "示例答案3"],
        "11": ["回答A", "回答B", "回答C"]
    },

    # 多项填空配置
    "multiple_texts": {
        "12": [
            ["选项1", "选项2", "选项3"],
            ["选项A", "选项B", "选项C"]
        ]
    },

    # 排序题概率配置
    "reorder_prob": {
        "13": [0.4, 0.3, 0.2, 0.1],  # 每个位置的选择概率
        "14": [0.25, 0.25, 0.25, 0.25]
    },

    # 下拉框概率配置
    "droplist_prob": {
        "15": [0.3, 0.4, 0.3],  # 每个选项的选择概率
        "16": [0.5, 0.5]
    },

    # 题目文本存储
    "question_texts": {
        "1": "您的性别",
        "2": "您的年级",
        "3": "您每月的消费项目",
        "4": "您喜欢的运动",
        "5": "您的兴趣爱好",
        "6": "您对学校的满意度",
        "7": "您的专业课程评价",
        "8": "您的生活满意度",
        "9": "您的学习压力程度",
        "10": "您的姓名",
        "11": "您的联系方式",
        "12": "您的家庭信息",
        "13": "您喜欢的食物排序",
        "14": "您喜欢的电影类型排序",
        "15": "您的出生地",
        "16": "您的职业"
    },
    "page_load_timeout": 20,  # 页面加载超时时间(秒)
    "element_timeout": 10,# 元素查找超时时间(秒)
    # 选项文本存储
    "option_texts": {
        "1": ["男", "女"],
        "2": ["大一", "大二", "大三", "大四"],
        "3": ["伙食", "购置衣物", "交通通讯", "生活用品", "日常交际", "学习用品", "娱乐旅游", "其他"],
        "4": ["篮球", "足球", "游泳", "跑步", "羽毛球"],
        "5": ["阅读", "音乐", "游戏", "旅行", "摄影"],
        "6": ["非常满意", "满意", "一般", "不满意", "非常不满意"],
        "7": ["非常满意", "满意", "一般", "不满意", "非常不满意"],
        "8": ["非常满意", "满意", "一般", "不满意", "非常不满意"],
        "9": ["非常大", "较大", "一般", "较小", "没有压力"],
        "13": ["中餐", "西餐", "日料", "快餐"],
        "14": ["科幻", "动作", "喜剧", "爱情"],
        "15": ["北京", "上海", "广州", "深圳"],
        "16": ["学生", "上班族", "自由职业", "退休"]
    }
}


# ToolTip类用于显示题目提示
class ToolTip:
    def __init__(self, widget, text='', delay=300, wraplength=500):  # 减少延迟，增加宽度
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wraplength = wraplength
        self.tip_window = None
        self.id = None
        self.x = self.y = 0

        # 绑定事件
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<Motion>", self.motion)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def motion(self, event=None):
        self.x, self.y = event.x, event.y
        self.x += self.widget.winfo_rootx() + 25
        self.y += self.widget.winfo_rooty() + 20
        if self.tip_window:
            self.tip_window.geometry(f"+{self.x}+{self.y}")

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self):
        if self.tip_window:
            return
        # 创建提示窗口
        self.tip_window = tk.Toplevel(self.widget)
        self.tip_window.wm_overrideredirect(True)
        self.tip_window.wm_geometry(f"+{self.x}+{self.y}")
        # 使用更明显的样式
        label = tk.Label(self.tip_window, text=self.text, justify=tk.LEFT,
                         background="#ffffff", relief=tk.SOLID, borderwidth=1,
                         wraplength=self.wraplength, padx=10, pady=5,
                         font=("Arial", 10))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tip_window
        self.tip_window = None
        if tw:
            tw.destroy()


class WJXAutoFillApp:
    def __init__(self, root):
        self.root = root
        # 全局字体设置（所有控件之前）
        default_font = ('楷体', 15)
        style = ttk.Style()
        style.configure('.', font=default_font)
        self.root.title("问卷星自动填写工具 v4.0")
        self.root.geometry("1200x900")
        self.root.resizable(True, True)

        # 设置应用图标
        try:
            self.root.iconbitmap("wjx_icon.ico")
        except:
            pass

        # 使用现代主题
        sv_ttk.set_theme("light")

        # 自定义样式 - 优化UI设计
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('TNotebook.Tab', padding=[10, 5], font=('Arial', 10, 'bold'))
        self.style.configure('TButton', padding=[10, 5], font=('Arial', 10))
        self.style.configure('TLabel', padding=[5, 2], font=('Arial', 10))
        self.style.configure('TEntry', padding=[5, 2])
        self.style.configure('TFrame', background='#f5f5f5')
        self.style.configure('Header.TLabel', font=('Arial', 11, 'bold'), foreground="#2c6fbb")
        self.style.configure('Title.TLabel', font=('Arial', 16, 'bold'), foreground="#2c6fbb")
        self.style.configure('Success.TLabel', foreground='green')
        self.style.configure('Warning.TLabel', foreground='orange')
        self.style.configure('Error.TLabel', foreground='red')
        self.style.configure('Accent.TButton', background='#4a90e2', foreground='white')

        self.config = DEFAULT_CONFIG.copy()
        self.running = False
        self.paused = False
        self.cur_num = 0
        self.cur_fail = 0
        self.lock = threading.Lock()
        self.pause_event = threading.Event()
        self.tooltips = []
        self.parsing = False
        self.previous_url = None  # <--- 加在__init__里
        self.dynamic_prompt_list = None  # 新增：用于存放最新AI生成的Prompt列表
        # 初始化字体
        self.font_family = tk.StringVar()
        self.font_size = tk.IntVar()
        self.font_family.set("Arial")
        self.font_size.set(10)

        # 创建主框架
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题栏
        title_frame = ttk.Frame(main_frame, style='TFrame')
        title_frame.pack(fill=tk.X, pady=(0, 10))

        # 添加logo
        try:
            logo_img = Image.open("wjx_logo.png")
            logo_img = logo_img.resize((40, 40), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(logo_img)
            logo_label = ttk.Label(title_frame, image=self.logo)
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        except:
            pass

        title_label = ttk.Label(title_frame, text="问卷星自动填写工具", style='Title.TLabel')
        title_label.pack(side=tk.LEFT)

        # 创建主面板
        self.main_paned = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)

        # 上半部分：控制区域和标签页
        self.top_frame = ttk.Frame(self.main_paned)
        self.main_paned.add(self.top_frame, weight=1)

        # 下半部分：日志区域
        self.log_frame = ttk.LabelFrame(self.main_paned, text="运行日志")
        self.main_paned.add(self.log_frame, weight=0)

        # === 添加控制按钮区域（顶部）===
        control_frame = ttk.LabelFrame(self.top_frame, text="控制面板")
        control_frame.pack(fill=tk.X, padx=5, pady=5)

        # 按钮框架
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        # 第一行按钮
        self.start_btn = ttk.Button(btn_frame, text="▶ 开始填写", command=self.start_filling, width=12,
                                    style='Accent.TButton')
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.pause_btn = ttk.Button(btn_frame, text="⏸ 暂停", command=self.toggle_pause, state=tk.DISABLED, width=10)
        self.pause_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(btn_frame, text="⏹ 停止", command=self.stop_filling, state=tk.DISABLED, width=10)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        # 添加手动修正按钮到控制面板
        self.correct_btn = ttk.Button(btn_frame, text="修正题型", command=self.correct_question_types, width=10)
        self.correct_btn.pack(side=tk.LEFT, padx=5)
        self.ai_struct_btn = ttk.Button(btn_frame, text="AI一键生成题型配置", command=self.ai_generate_structure,
                                        width=16)
        self.ai_struct_btn.pack(side=tk.LEFT, padx=5)

        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)
        ttk.Separator(btn_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=10, fill=tk.Y)

        # 状态栏
        status_frame = ttk.Frame(control_frame)
        status_frame.pack(fill=tk.X, pady=(5, 0))

        # 状态指示器
        self.status_indicator = ttk.Label(status_frame, text="●", font=("Arial", 14), foreground="green")
        self.status_indicator.pack(side=tk.LEFT, padx=(5, 0))

        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 10))
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100, length=200)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # 题目进度
        self.question_progress_var = tk.DoubleVar()
        self.question_progress_bar = ttk.Progressbar(status_frame,
                                                     variable=self.question_progress_var,
                                                     maximum=100,
                                                     length=150)
        self.question_progress_bar.pack(side=tk.RIGHT, padx=5)

        self.question_status_var = tk.StringVar(value="题目: 0/0")
        self.question_status_label = ttk.Label(status_frame, textvariable=self.question_status_var, width=12)
        self.question_status_label.pack(side=tk.RIGHT, padx=5)

        # 创建标签页
        self.notebook = ttk.Notebook(self.top_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 创建全局设置和题型设置标签页
        self.global_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.global_frame, text="⚙️ 全局设置")
        self.create_global_settings()

        self.question_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.question_frame, text="📝 题型设置")

        # 初始化问卷题型设置的 Notebook
        self.question_notebook = ttk.Notebook(self.question_frame)
        self.question_notebook.pack(fill=tk.X, expand=False)

        # 初始化所有题型的输入框列表 - 移到这里确保在create_question_settings前初始化
        self.single_entries = []
        self.multi_entries = []
        self.min_selection_entries = []
        self.max_selection_entries = []
        self.matrix_entries = []
        self.text_entries = []
        self.multiple_text_entries = []
        self.reorder_entries = []
        self.droplist_entries = []
        self.scale_entries = []

        self.create_question_settings()
        # 新增AI助手tab
        self.ai_chat_tab = AIChatTab(
            self.notebook,
            api_key_getter=lambda: (
                self.openai_api_key_entry.get().strip() if self.ai_service.get() == "OpenAI"
                else self.qingyan_api_key_entry.get().strip()
            ),
            api_service_getter=lambda: self.ai_service.get(),
            app_ref=self
        )
        self.notebook.add(self.ai_chat_tab, text="💬 AI问卷助手")
        # 创建日志区域
        self.create_log_area()

        # 设置日志系统
        self.setup_logging()

        # 绑定字体更新事件
        self.font_family.trace_add("write", self.update_font)
        self.font_size.trace_add("write", self.update_font)

        # 初始化字体
        self.update_font()

        self.root.after(200, lambda: self.main_paned.sashpos(0, 600))
    def create_log_area(self):
        """创建日志区域"""
        # 日志控制按钮
        log_control_frame = ttk.Frame(self.log_frame)
        log_control_frame.pack(fill=tk.X, padx=5, pady=(5, 0))

        self.clear_log_btn = ttk.Button(log_control_frame, text="清空日志", command=self.clear_log)
        self.clear_log_btn.pack(side=tk.LEFT, padx=5)

        self.export_log_btn = ttk.Button(log_control_frame, text="导出日志", command=self.export_log)
        self.export_log_btn.pack(side=tk.LEFT, padx=5)

        # 日志文本区域
        self.log_area = scrolledtext.ScrolledText(self.log_frame, height=10)
        self.log_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_area.config(state=tk.DISABLED)


    def setup_logging(self):
        """配置日志系统"""

        class TextHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget

            def emit(self, record):
                msg = self.format(record)
                color_map = {
                    'INFO': 'black',
                    'WARNING': 'orange',
                    'ERROR': 'red',
                    'CRITICAL': 'red'
                }
                color = color_map.get(record.levelname, 'black')

                def append():
                    self.text_widget.configure(state='normal')
                    self.text_widget.tag_config(record.levelname, foreground=color)
                    self.text_widget.insert(tk.END, msg + '\n', record.levelname)
                    self.text_widget.configure(state='disabled')
                    self.text_widget.see(tk.END)

                self.text_widget.after(0, append)

        handler = TextHandler(self.log_area)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
                                      datefmt='%H:%M:%S')
        handler.setFormatter(formatter)

        logger = logging.getLogger()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logging.info("应用程序已启动")

    def create_global_settings(self):
        """创建全局设置界面，包括智能提交间隔和批量休息设置，并支持鼠标滚轮滚动（支持字体字号手输且自动校验）"""
        frame = self.global_frame
        padx, pady = 8, 5

        # 创建滚动条
        canvas = tk.Canvas(frame, background='#f0f0f0')
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, style='TFrame')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮支持（跨平台）
        def _on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)

        # ======== 字体设置 ========
        font_frame = ttk.LabelFrame(scrollable_frame, text="显示设置")
        font_frame.grid(row=0, column=0, columnspan=2, padx=padx, pady=pady, sticky=tk.EW)

        ttk.Label(font_frame, text="字体选择:").grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.W)
        font_options = sorted(tkfont.families())
        self.font_menu = ttk.Combobox(font_frame, textvariable=self.font_family, values=font_options, width=15,
                                      state="normal")
        self.font_menu.grid(row=0, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.font_menu.set("楷体")
        self.font_menu.bind("<FocusOut>", self._validate_font_family)
        self.font_menu.bind("<<ComboboxSelected>>", self._validate_font_family)

        ttk.Label(font_frame, text="字体大小:").grid(row=0, column=2, padx=padx, pady=pady, sticky=tk.W)
        self.font_size_spinbox = ttk.Spinbox(
            font_frame, from_=8, to=24, increment=1,
            textvariable=self.font_size, width=5,
            validate='focusout',
            validatecommand=(font_frame.register(self._validate_font_size), '%P')
        )
        self.font_size_spinbox.grid(row=0, column=3, padx=padx, pady=pady, sticky=tk.W)
        self.font_size_spinbox.set(16)

        # ======== 问卷设置 ========
        survey_frame = ttk.LabelFrame(scrollable_frame, text="问卷设置")
        survey_frame.grid(row=1, column=0, columnspan=2, padx=padx, pady=pady, sticky=tk.EW)

        ttk.Label(survey_frame, text="问卷链接:").grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.url_entry = ttk.Entry(survey_frame, width=50)
        self.url_entry.grid(row=0, column=1, columnspan=3, padx=padx, pady=pady, sticky=tk.EW)
        self.url_entry.insert(0, self.config["url"])

        ttk.Label(survey_frame, text="目标份数:").grid(row=1, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.target_entry = ttk.Spinbox(survey_frame, from_=1, to=10000, width=8)
        self.target_entry.grid(row=1, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.target_entry.set(self.config["target_num"])

        ttk.Label(survey_frame, text="微信作答比率:").grid(row=1, column=2, padx=padx, pady=pady, sticky=tk.W)
        self.ratio_scale = ttk.Scale(survey_frame, from_=0, to=1, orient=tk.HORIZONTAL, length=100)
        self.ratio_scale.grid(row=1, column=3, padx=padx, pady=pady, sticky=tk.EW)
        self.ratio_scale.set(self.config["weixin_ratio"])
        self.ratio_var = tk.StringVar()
        self.ratio_var.set(f"{self.config['weixin_ratio'] * 100:.0f}%")
        ratio_label = ttk.Label(survey_frame, textvariable=self.ratio_var, width=4)
        ratio_label.grid(row=1, column=4, padx=(0, padx), pady=pady, sticky=tk.W)
        self.ratio_scale.bind("<Motion>", self.update_ratio_display)
        self.ratio_scale.bind("<ButtonRelease-1>", self.update_ratio_display)

        ttk.Label(survey_frame, text="作答时长(秒):").grid(row=2, column=0, padx=padx, pady=pady, sticky=tk.W)
        ttk.Label(survey_frame, text="最短:").grid(row=2, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.min_duration = ttk.Spinbox(survey_frame, from_=5, to=300, width=5)
        self.min_duration.grid(row=2, column=2, padx=padx, pady=pady, sticky=tk.W)
        self.min_duration.set(self.config["min_duration"])
        ttk.Label(survey_frame, text="最长:").grid(row=2, column=3, padx=padx, pady=pady, sticky=tk.W)
        self.max_duration = ttk.Spinbox(survey_frame, from_=5, to=300, width=5)
        self.max_duration.grid(row=2, column=4, padx=padx, pady=pady, sticky=tk.W)
        self.max_duration.set(self.config["max_duration"])

        # ======== 延迟设置 ========
        delay_frame = ttk.LabelFrame(scrollable_frame, text="延迟设置")
        delay_frame.grid(row=2, column=0, columnspan=2, padx=padx, pady=pady, sticky=tk.EW)
        ttk.Label(delay_frame, text="基础延迟(秒):").grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.W)
        ttk.Label(delay_frame, text="最小:").grid(row=0, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.min_delay = ttk.Spinbox(delay_frame, from_=0.1, to=10, increment=0.1, width=5)
        self.min_delay.grid(row=0, column=2, padx=padx, pady=pady, sticky=tk.W)
        self.min_delay.set(self.config["min_delay"])
        ttk.Label(delay_frame, text="最大:").grid(row=0, column=3, padx=padx, pady=pady, sticky=tk.W)
        self.max_delay = ttk.Spinbox(delay_frame, from_=0.1, to=10, increment=0.1, width=5)
        self.max_delay.grid(row=0, column=4, padx=padx, pady=pady, sticky=tk.W)
        self.max_delay.set(self.config["max_delay"])

        ttk.Label(delay_frame, text="每题延迟(秒):").grid(row=1, column=0, padx=padx, pady=pady, sticky=tk.W)
        ttk.Label(delay_frame, text="最小:").grid(row=1, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.min_q_delay = ttk.Spinbox(delay_frame, from_=0.1, to=5, increment=0.1, width=5)
        self.min_q_delay.grid(row=1, column=2, padx=padx, pady=pady, sticky=tk.W)
        self.min_q_delay.set(self.config["per_question_delay"][0])
        ttk.Label(delay_frame, text="最大:").grid(row=1, column=3, padx=padx, pady=pady, sticky=tk.W)
        self.max_q_delay = ttk.Spinbox(delay_frame, from_=0.1, to=5, increment=0.1, width=5)
        self.max_q_delay.grid(row=1, column=4, padx=padx, pady=pady, sticky=tk.W)
        self.max_q_delay.set(self.config["per_question_delay"][1])

        ttk.Label(delay_frame, text="页面延迟(秒):").grid(row=2, column=0, padx=padx, pady=pady, sticky=tk.W)
        ttk.Label(delay_frame, text="最小:").grid(row=2, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.min_p_delay = ttk.Spinbox(delay_frame, from_=0.1, to=10, increment=0.1, width=5)
        self.min_p_delay.grid(row=2, column=2, padx=padx, pady=pady, sticky=tk.W)
        self.min_p_delay.set(self.config["per_page_delay"][0])
        ttk.Label(delay_frame, text="最大:").grid(row=2, column=3, padx=padx, pady=pady, sticky=tk.W)
        self.max_p_delay = ttk.Spinbox(delay_frame, from_=0.1, to=10, increment=0.1, width=5)
        self.max_p_delay.grid(row=2, column=4, padx=padx, pady=pady, sticky=tk.W)
        self.max_p_delay.set(self.config["per_page_delay"][1])

        ttk.Label(delay_frame, text="提交延迟:").grid(row=3, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.submit_delay = ttk.Spinbox(delay_frame, from_=1, to=10, width=5)
        self.submit_delay.grid(row=3, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.submit_delay.set(self.config["submit_delay"])

        # ======== 智能提交间隔设置 ========
        smart_gap_frame = ttk.LabelFrame(scrollable_frame, text="智能提交间隔")
        smart_gap_frame.grid(row=3, column=0, columnspan=2, padx=padx, pady=pady, sticky=tk.EW)
        self.enable_smart_gap_var = tk.BooleanVar(value=self.config.get("enable_smart_gap", True))
        smart_gap_switch = ttk.Checkbutton(
            smart_gap_frame, text="开启智能提交间隔与批量休息", variable=self.enable_smart_gap_var)
        smart_gap_switch.grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.W, columnspan=5)
        ttk.Label(smart_gap_frame, text="单份提交间隔(分钟):").grid(row=1, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.min_submit_gap = ttk.Spinbox(smart_gap_frame, from_=1, to=120, width=5)
        self.min_submit_gap.grid(row=1, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.min_submit_gap.set(self.config.get("min_submit_gap", 10))
        ttk.Label(smart_gap_frame, text="~").grid(row=1, column=2, padx=2, pady=pady, sticky=tk.W)
        self.max_submit_gap = ttk.Spinbox(smart_gap_frame, from_=1, to=180, width=5)
        self.max_submit_gap.grid(row=1, column=3, padx=padx, pady=pady, sticky=tk.W)
        self.max_submit_gap.set(self.config.get("max_submit_gap", 20))
        ttk.Label(smart_gap_frame, text="每").grid(row=2, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.batch_size = ttk.Spinbox(smart_gap_frame, from_=1, to=100, width=5)
        self.batch_size.grid(row=2, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.batch_size.set(self.config.get("batch_size", 5))
        ttk.Label(smart_gap_frame, text="份后暂停").grid(row=2, column=2, padx=2, pady=pady, sticky=tk.W)
        self.batch_pause = ttk.Spinbox(smart_gap_frame, from_=1, to=120, width=5)
        self.batch_pause.grid(row=2, column=3, padx=padx, pady=pady, sticky=tk.W)
        self.batch_pause.set(self.config.get("batch_pause", 15))
        ttk.Label(smart_gap_frame, text="分钟").grid(row=2, column=4, padx=2, pady=pady, sticky=tk.W)

        # ======== 高级设置 ========
        advanced_frame = ttk.LabelFrame(scrollable_frame, text="高级设置")
        advanced_frame.grid(row=4, column=0, columnspan=2, padx=padx, pady=pady, sticky=tk.EW)

        # 第0行：浏览器窗口数量
        ttk.Label(advanced_frame, text="浏览器窗口数量:").grid(row=0, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.num_threads = ttk.Spinbox(advanced_frame, from_=1, to=10, width=5)
        self.num_threads.grid(row=0, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.num_threads.set(self.config["num_threads"])

        # 第1行：代理IP设置
        self.use_ip_var = tk.BooleanVar(value=self.config["use_ip"])
        ttk.Checkbutton(advanced_frame, text="使用代理IP", variable=self.use_ip_var).grid(
            row=1, column=0, padx=padx, pady=pady, sticky=tk.W)
        ttk.Label(advanced_frame, text="IP API:").grid(row=1, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.ip_entry = ttk.Entry(advanced_frame, width=40)
        self.ip_entry.grid(row=1, column=2, columnspan=3, padx=padx, pady=pady, sticky=tk.EW)
        self.ip_entry.insert(0, self.config["ip_api"])

        # 第2行：代理切换设置
        ttk.Label(advanced_frame, text="代理切换:").grid(row=2, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.ip_change_mode = ttk.Combobox(advanced_frame, values=["per_submit", "per_batch"], width=12)
        self.ip_change_mode.grid(row=2, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.ip_change_mode.set(self.config.get("ip_change_mode", "per_submit"))
        ttk.Label(advanced_frame, text="每N份切换:").grid(row=2, column=2, padx=padx, pady=pady, sticky=tk.W)
        self.ip_change_batch = ttk.Spinbox(advanced_frame, from_=1, to=100, width=5)
        self.ip_change_batch.grid(row=2, column=3, padx=padx, pady=pady, sticky=tk.W)
        self.ip_change_batch.set(self.config.get("ip_change_batch", 5))

        # 第3行：无头模式设置
        self.headless_var = tk.BooleanVar(value=self.config["headless"])
        ttk.Checkbutton(advanced_frame, text="无头模式(不显示浏览器)", variable=self.headless_var).grid(
            row=3, column=0, padx=padx, pady=pady, sticky=tk.W)

        # 第4行：启用AI答题
        self.ai_fill_var = tk.BooleanVar(value=self.config.get("ai_fill_enabled", False))
        ttk.Checkbutton(advanced_frame, text="启用AI自动答题（填空题）", variable=self.ai_fill_var).grid(
            row=4, column=0, padx=padx, pady=pady, sticky=tk.W, columnspan=2)

        # ======== AI服务设置 ========
        # 第5行：AI服务选择
        ttk.Label(advanced_frame, text="AI服务:").grid(row=5, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.ai_service = ttk.Combobox(advanced_frame, values=["质谱清言", "OpenAI"], width=10)
        self.ai_service.grid(row=5, column=1, padx=padx, pady=pady, sticky=tk.W)
        self.ai_service.set(self.config.get("ai_service", "质谱清言"))

        # 第6行：质谱清言API Key
        # 使用正确的变量名 - 删除_label后缀
        self.qingyan_api_key_label = ttk.Label(advanced_frame, text="质谱清言 API Key:")  # 添加此行
        self.qingyan_api_key_label.grid(row=6, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.qingyan_api_key_entry = ttk.Entry(advanced_frame, width=40)
        self.qingyan_api_key_entry.grid(row=6, column=1, columnspan=2, padx=padx, pady=pady, sticky=tk.EW)

        # 获取API Key链接（放在质谱清言行）
        self.api_link = ttk.Label(advanced_frame, text="获取API Key", foreground="blue", cursor="hand2")  # 添加此行
        self.api_link.grid(row=6, column=3, padx=5, pady=pady)
        self.api_link.bind("<Button-1>", lambda e: webbrowser.open("https://open.bigmodel.cn/usercenter/apikeys"))

        # 第7行：OpenAI API Key
        # 使用正确的变量名 - 删除_label后缀
        self.openai_api_key_label = ttk.Label(advanced_frame, text="OpenAI API Key:")  # 添加此行
        self.openai_api_key_label.grid(row=7, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.openai_api_key_entry = ttk.Entry(advanced_frame, width=40)
        self.openai_api_key_entry.grid(row=7, column=1, columnspan=2, padx=padx, pady=pady, sticky=tk.EW)

        # 第8行：AI答题Prompt模板
        self.ai_prompt_label = ttk.Label(advanced_frame, text="AI答题Prompt模板:")  # 添加此行
        self.ai_prompt_label.grid(row=8, column=0, padx=padx, pady=pady, sticky=tk.W)
        self.ai_prompt_var = tk.StringVar()
        self.ai_prompt_combobox = ttk.Combobox(
            advanced_frame, textvariable=self.ai_prompt_var, width=60, state="normal"
        )
        self.ai_prompt_combobox.grid(row=8, column=1, columnspan=2, padx=padx, pady=pady, sticky=tk.EW)
        self.ai_prompt_combobox['values'] = [
            self.config.get("ai_prompt_template", "请用简洁、自然的中文回答：{question}")]
        self.ai_prompt_combobox.set(self.config.get("ai_prompt_template", "请用简洁、自然的中文回答：{question}"))

        # 重新生成Prompt按钮
        self.refresh_prompt_btn = ttk.Button(  # 添加此行
            advanced_frame, text="重新生成Prompt(质谱清言)",
            command=self.on_refresh_qingyan_prompts
        )
        self.refresh_prompt_btn.grid(row=8, column=3, padx=5, pady=pady)

        # ======== 操作按钮 ========
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10, sticky=tk.W)
        self.save_btn = ttk.Button(button_frame, text="保存配置", command=self.on_save_config, width=15)
        self.save_btn.grid(row=0, column=2, padx=5)
        self.parse_btn = ttk.Button(button_frame, text="解析问卷", command=self.parse_survey, width=15)
        self.parse_btn.grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="重置默认", command=self.reset_defaults, width=15).grid(row=0, column=1, padx=5)
        scrollable_frame.columnconfigure(0, weight=1)
        tip_label = ttk.Label(scrollable_frame, text="提示: 填写前请先解析问卷以获取题目结构", style='Warning.TLabel')
        tip_label.grid(row=6, column=0, columnspan=2, pady=(10, 0))

        # 添加AI服务切换事件绑定
        self.ai_service.bind("<<ComboboxSelected>>", self.on_ai_service_change)
        # 初始化UI状态
        self.on_ai_service_change()

    def on_ai_service_change(self, event=None):
        """动态显示/隐藏API Key输入框 - 修复版"""
        service = self.ai_service.get()

        # 使用grid_forget()完全移除旧布局
        self.qingyan_api_key_label.grid_forget()
        self.qingyan_api_key_entry.grid_forget()
        self.api_link.grid_forget()
        self.openai_api_key_label.grid_forget()
        self.openai_api_key_entry.grid_forget()

        if service == "OpenAI":
            # 重新布局OpenAI相关控件
            self.openai_api_key_label.grid(row=7, column=0, padx=5, pady=5, sticky=tk.W)
            self.openai_api_key_entry.grid(row=7, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)

            # 修改提示文本
            self.refresh_prompt_btn.config(text="重新生成Prompt(OpenAI)")
        else:
            # 重新布局质谱清言相关控件
            self.qingyan_api_key_label.grid(row=6, column=0, padx=5, pady=5, sticky=tk.W)
            self.qingyan_api_key_entry.grid(row=6, column=1, columnspan=2, padx=5, pady=5, sticky=tk.EW)
            self.api_link.grid(row=6, column=3, padx=5, pady=5)

            # 恢复按钮文本
            self.refresh_prompt_btn.config(text="重新生成Prompt(质谱清言)")

        # 确保布局更新
        self.advanced_frame.update_idletasks()
    def _validate_font_family(self, event=None):
        family = self.font_family.get()
        valid_families = set(tkfont.families())
        # 限长防止撑界面
        if len(family) > 32:
            family = family[:32]
            self.font_family.set(family)
        if family not in valid_families:
            self.font_family.set("楷体")

    def run_ai_structured_analysis(self):
        api_key = self.qingyan_api_key_entry.get().strip()
        # 采集问卷结构
        qlist = []
        for qid, qtext in self.config["question_texts"].items():
            opts = self.config["option_texts"].get(qid, [])
            qlist.append({"text": qtext, "options": opts})
        ai_result = ai_parse_questionnaire(qlist, api_key)
        # ai_result["questions"]、ai_result["dimensions"] 可直接用于自动填充题型设置和维度分组
        # 你可以自动刷新界面，用AI推荐的题型/分组/配置覆盖现有设置，或者让用户确认
        # 也支持将json结构显示在AI分析tab
        self.ai_analysis_text.delete(1.0, "end")
        self.ai_analysis_text.insert("end", json.dumps(ai_result, ensure_ascii=False, indent=2))
    def _validate_font_size(self, value):
        try:
            v = int(value)
            if 8 <= v <= 24:
                return True
        except Exception:
            pass
        self.font_size.set("16")
        return False
    def generate_prompt_templates_by_qingyan(self, question_texts, api_key):
        import requests

        # 只取前8个题目避免过长
        question_samples = "\n".join([f"{i + 1}. {q}" for i, q in enumerate(question_texts[:10])])

        # 构建Prompt要求
        prompt = (
            f"你是问卷填写专家，需要为以下问卷题目生成答题人设和答题风格：\n{question_samples}\n"
            "请根据题目内容，创造20-30个不同的真实答题人设，每个包含性别、年龄、职业、地域、教育背景、收入水平等细节。"
            "为每个人设生成1条答题Prompt，要求：\n"
            "1. 人设真实自然，符合中国社会各阶层特征\n"
            "2. 答案必须极简：数字题只输出数字，选择题只输出选项字母或编号\n"
            "3. 主观题答案不超过5个字（如'满意'、'一般'、'不同意'）\n"
            "4. 涉及隐私信息（姓名/电话）时生成合理虚构数据\n"
            "5. 不要任何解释性文字，不要重复题干\n"
            "6. 格式：'你是[人设]，请直接作答：{question}'\n"
            "示例1：你是28岁杭州程序员，月入1.5万，已婚有房贷。请直接作答：{question}\n"
            "示例2：你是19岁广州女大学生，月消费2000元。请直接作答：{question}\n"
            "直接输出Prompt列表，每行一条，不要编号。"
        )

        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "glm-4",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.89,

        }

        try:
            resp = requests.post(url, headers=headers, json=data, timeout=40)
            resp.raise_for_status()
            result = resp.json()

            # 提取API返回内容
            content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            # 按行分割并清洗结果
            lines = [line.strip() for line in content.split("\n") if line.strip()]

            # 过滤包含禁用词的Prompt
            ban_words = ["AI", "助手", "机器人", "智能", "人工智能", "模型", "自动", "程序"]
            prompt_list = [line for line in lines if not any(word in line for word in ban_words)]

            # 空结果处理：返回默认模板
            if not prompt_list:
                return [
                    "你是19岁的山东男生，大学生。请用极简数字/短语作答：{question}",
                    "你是28岁的北京白领。请直接用'无'或数字作答：{question}"
                ]
            return prompt_list

        except Exception as e:
            return ["你是23岁的南方女生，性格内向，大学生。请简答：{question}"]
    def on_refresh_qingyan_prompts(self):
        """生成Prompt - 优化版（带状态提示和错误处理）"""
        api_key = self.qingyan_api_key_entry.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请先填写质谱清言API Key")
            return

        # 获取题目文本（最多15题）
        q_texts = list(self.config.get("question_texts", {}).values())[:15]
        if not q_texts:
            messagebox.showerror("错误", "请先解析问卷获取题目")
            return

        # 更新UI状态
        self.status_var.set("AI正在生成Prompt...")
        self.status_indicator.config(foreground="orange")
        self.root.update()

        # 禁用按钮防止重复点击
        self.parse_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.DISABLED)
        self.save_btn.config(state=tk.DISABLED)

        # 显示加载动画
        self.progress_bar.config(mode="indeterminate")
        self.progress_bar.start()

        def worker():
            try:
                prompt_list = self.generate_prompt_templates_by_qingyan(q_texts, api_key)

                self.root.after(0, lambda: self._update_prompt_list(prompt_list))
                self.root.after(0, lambda: self.status_var.set("Prompt生成成功"))
                self.root.after(0, lambda: self.status_indicator.config(foreground="green"))
                self.root.after(0, lambda: messagebox.showinfo("成功", f"已生成{len(prompt_list)}条Prompt模板"))

            except Exception as e:
                error_msg = f"生成Prompt失败: {str(e)}"
                self.root.after(0, lambda: self.status_var.set("生成失败"))
                self.root.after(0, lambda: self.status_indicator.config(foreground="red"))
                self.root.after(0, lambda: messagebox.showerror("错误", error_msg))
                logging.error(error_msg)

            finally:
                # 恢复UI状态
                self.root.after(0, lambda: self.progress_bar.stop())
                self.root.after(0, lambda: self.progress_bar.config(mode="determinate"))
                self.root.after(0, lambda: self.parse_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.save_btn.config(state=tk.NORMAL))

        # 启动工作线程
        threading.Thread(target=worker, daemon=True).start()

    def _update_prompt_list(self, prompt_list):
        """更新Prompt下拉框 - 优化版"""
        if not prompt_list:
            messagebox.showwarning("提示", "未生成有效的Prompt")
            return

        # 更新下拉框
        current_values = list(self.ai_prompt_combobox["values"])
        new_values = current_values + prompt_list
        self.ai_prompt_combobox["values"] = new_values
        self.ai_prompt_combobox.set(prompt_list[0])
        self.dynamic_prompt_list = prompt_list
        logging.info(f"已生成{len(prompt_list)}条Prompt模板")

    def on_save_config(self):
        if self.save_config():
            messagebox.showinfo("提示", "配置已保存（仅存于内存，如需导出请用导出功能）")

    def _process_parsed_questions(self, questions_data):
        """处理解析得到的问卷题目数据 - 优化版"""
        try:
            import logging
            logging.info(f"解析到的题目数量: {len(questions_data)}")

            # 记录题型分布
            type_count = {
                "1": 0, "2": 0, "3": 0, "4": 0,
                "5": 0, "6": 0, "7": 0, "11": 0
            }

            # 清空原有配置
            self.config["question_texts"] = {}
            self.config["option_texts"] = {}

            # 初始化题型配置
            self.config["single_prob"] = {}
            self.config["multiple_prob"] = {}
            self.config["matrix_prob"] = {}
            self.config["texts"] = {}
            self.config["multiple_texts"] = {}
            self.config["reorder_prob"] = {}
            self.config["droplist_prob"] = {}
            self.config["scale_prob"] = {}
            # === 新增: 初始化other_texts ===
            if "other_texts" not in self.config:
                self.config["other_texts"] = {}

            # 更新题目和选项信息
            for question in questions_data:
                question_id = str(question.get('id'))
                question_text = question.get('text', f"题目{question_id}")
                options = question.get('options', [])
                q_type = question.get('type', '1')

                # 统计题型
                type_count[q_type] = type_count.get(q_type, 0) + 1

                # 更新题目文本
                self.config["question_texts"][question_id] = question_text

                # 默认先存options原始值
                self.config["option_texts"][question_id] = options

                # 根据题型初始化配置
                if q_type == '3':  # 单选题
                    self.config["single_prob"][question_id] = -1  # 默认随机
                elif q_type == '4':  # 多选题
                    self.config["multiple_prob"][question_id] = {
                        "prob": [50] * len(options),
                        "min_selection": 1,
                        "max_selection": min(3, len(options))
                    }
                    # === 新增: 自动检测"其他"选项并初始化other_texts ===
                    for opt in options:
                        if "其他" in opt or "other" in str(opt).lower():
                            if question_id not in self.config["other_texts"]:
                                # 可以自定义默认内容
                                self.config["other_texts"][question_id] = ["其他：自定义答案1", "其他：自定义答案2",
                                                                           "其他：自定义答案3"]
                elif q_type == '6':  # 矩阵题
                    self.config["matrix_prob"][question_id] = -1  # 默认随机
                elif q_type == '1':  # 填空题
                    self.config["texts"][question_id] = ["示例答案"]
                elif q_type == '5':  # 量表题
                    self.config["scale_prob"][question_id] = [0.2] * len(options)
                elif q_type == '7':  # 下拉框
                    # ---- 仅保留有效选项（非空value，非disabled），支持dict、对象、字符串 ----
                    valid_options = []
                    for opt in options:
                        # 结构1：dict型
                        if isinstance(opt, dict):
                            value = opt.get('value', '').strip()
                            disabled = opt.get('disabled', False)
                            text = opt.get('text', '') or opt.get('label', '')
                            if value and not disabled:
                                valid_options.append(text)
                        # 结构2：对象型
                        elif hasattr(opt, 'value'):
                            value = getattr(opt, 'value', '').strip()
                            disabled = getattr(opt, 'disabled', False)
                            text = getattr(opt, 'text', '') or getattr(opt, 'label', '')
                            if value and not disabled:
                                valid_options.append(text)
                        # 结构3：字符串
                        elif isinstance(opt, str):
                            if opt and opt != "请选择":
                                valid_options.append(opt)

                    # 直接存储选项列表（一维）
                    self.config["option_texts"][question_id] = valid_options

                    # 使用一维概率列表
                    self.config["droplist_prob"][question_id] = [0.3] * len(valid_options) if valid_options else []
                elif q_type == '11':  # 排序题
                    self.config["reorder_prob"][question_id] = [0.25] * len(options)
                    self.config["option_texts"][question_id] = options
                elif q_type == '2':  # 多项填空
                    self.config["multiple_texts"][question_id] = [["示例答案"]] * len(options)

            # 处理完成后，统一保证所有题号key为str
            self.config["question_texts"] = {str(k): v for k, v in self.config["question_texts"].items()}
            self.config["option_texts"] = {str(k): v for k, v in self.config["option_texts"].items()}

            # 打印题型统计
            type_names = {
                "1": "填空题", "2": "多项填空", "3": "单选题",
                "4": "多选题", "5": "量表题", "6": "矩阵题",
                "7": "下拉框", "11": "排序题"
            }
            stats = [f"{type_names.get(k, k)}: {v}" for k, v in type_count.items()]
            logging.info("题型统计: " + ", ".join(stats))

            # 处理完成后，更新题型设置界面
            self.root.after(0, self.reload_question_settings)

        except Exception as e:
            import logging
            logging.error(f"处理解析的题目时出错: {str(e)}")
            # 显示错误提示
            self.root.after(0, lambda: messagebox.showerror("错误", f"处理解析的题目时出错: {str(e)}"))

    def ai_generate_answer(self, question: str, api_key: str, prompt_template: str) -> str:
        """使用OpenAI API生成答案（适配1.0+版本）"""
        try:
            # 确保导入在函数内部以避免兼容性问题
            from openai import OpenAI

            if not api_key:
                return "自动填写内容"

            client = OpenAI(api_key=api_key)
            prompt = prompt_template.format(question=question)

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.7,
                n=1
            )

            return response.choices[0].message.content.strip()
        except ImportError:
            logging.error("OpenAI库未安装，请运行: pip install openai")
            return "自动填写内容"
        except Exception as e:
            logging.error(f"AI答题失败: {str(e)}")
            return "自动填写内容"

    def zhipu_generate_answer(self, question: str, api_key: str, prompt_template: str) -> str:
        """
        优化版AI答题 - 支持题型识别和格式控制
        """
        import re
        import logging

        # 1. 提取人设
        identity = self.extract_identity_from_prompt(prompt_template)

        # 2. 题型识别与格式控制
        format_rules = ""
        if re.search(r'年龄|岁数|多大', question):
            format_rules = "请只回答数字（如'25'），不要任何文字说明。"
        elif re.search(r'金额|价格|费用|收入|支出|消费', question):
            format_rules = "请只回答数字（如'5000'或'1.2万'），可带简单单位。"
        elif re.search(r'日期|时间|何时|时候', question):
            format_rules = "请按'YYYY-MM-DD'或'X年前'格式回答。"
        elif re.search(r'评分|打分|评价|满意度', question):
            format_rules = "请用1-10的数字回答。"
        elif re.search(r'姓名|称呼', question):
            format_rules = "请生成常见中文姓名。"
        elif re.search(r'电话|手机|联系方式', question):
            format_rules = "请生成13开头的手机号。"

        # 3. 构建Prompt
        full_prompt = (
            f"你现在的身份是：{identity}。请严格按以下要求回答：\n"
            f"1. 只输出最终答案，不要任何解释\n"
            f"2. 答案长度不超过10个字\n"
            f"3. {format_rules}\n"
            f"问题：{question}"
        )

        # 4. API请求（增加超时和重试）
        try:
            url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            data = {
                "model": "glm-4",
                "messages": [{"role": "user", "content": full_prompt}],
                "max_tokens": 50,  # 限制长度
                "temperature": 0.3,  # 降低随机性
                "top_p": 0.8
            }

            # 增加重试机制
            for attempt in range(3):
                try:
                    response = requests.post(url, headers=headers, json=data, timeout=15)
                    response.raise_for_status()
                    result = response.json()
                    content = (
                        result.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )

                    # 5. 答案后处理
                    return self.simplify_answer(content, question)
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                    if attempt < 2:
                        time.sleep(1.5)
                        continue
                    else:
                        raise
        except Exception as e:
            logging.error(f"AI答题失败: {str(e)}")

        return self.get_identity_answer(identity, question)

    def extract_identity_from_prompt(self, prompt_template: str) -> str:
        """从Prompt模板提取身份（只保留“xx岁xx职业/地区/性别”这种）"""
        import re
        # 匹配“你是...”或“身份：...”等格式
        match = re.search(r"你是([^\u4e00-\u9fa5a-zA-Z0-9]*[\u4e00-\u9fa5a-zA-Z0-9，、 ]+)", prompt_template)
        if match:
            return match.group(1).split("，请")[0].strip()
        return "用户"

    def simplify_answer(self, answer: str, question: str) -> str:
        """答案后处理 - 增强版（按题型优化）"""
        import re

        # 移除所有标点符号和多余空格
        answer = re.sub(r'[^\w\u4e00-\u9fa5]', ' ', answer).strip()

        # 题型特定处理
        if re.search(r'年龄|岁数|多大', question):
            # 提取数字
            match = re.search(r'\d{1,2}', answer)
            return match.group(0) if match else "30"

        elif re.search(r'金额|价格|费用|收入|支出|消费', question):
            # 提取数字和单位
            match = re.search(r'(\d+\.?\d*)(万?元?)', answer)
            if match:
                num, unit = match.groups()
                return f"{num}{unit}" if unit else num
            return "5000"

        elif re.search(r'日期|时间|何时|时候', question):
            # 标准化日期格式
            if re.match(r'\d{4}-\d{1,2}-\d{1,2}', answer):
                return answer
            return "2023-01-01"

        elif re.search(r'评分|打分|评价|满意度', question):
            # 确保1-10分
            match = re.search(r'\d+', answer)
            if match:
                score = min(10, max(1, int(match.group(0))))
                return str(score)
            return "7"

        elif re.search(r'姓名|称呼', question):
            # 保留中文姓名
            match = re.search(r'[\u4e00-\u9fa5]{2,3}', answer)
            return match.group(0) if match else "张三"

        elif re.search(r'电话|手机|联系方式', question):
            # 生成有效手机号
            match = re.search(r'1[3-9]\d{9}', answer)
            return match.group(0) if match else "13800138000"

        # 通用处理：取第一个有效片段
        parts = answer.split()
        return parts[0][:15] if parts else "无"

    def get_identity_answer(self, identity: str, question: str) -> str:
        """备选答案池 - 按题目类型优化"""
        import random

        # 按题型分类的答案池
        answer_pools = {
            "age": [str(i) for i in range(18, 65)],
            "income": ["5000", "8000", "10000", "15000", "20000", "30000"],
            "rating": [str(i) for i in range(1, 11)],
            "date": ["2020-01-01", "2021-05-15", "2022-07-20", "2023-03-10"],
            "name": ["李明", "张伟", "王芳", "刘洋", "陈静", "赵强"],
            "phone": ["13800138000", "13912345678", "13787654321", "13511223344"],
            "bool": ["是", "否", "有", "无", "满意", "不满意", "同意", "不同意"],
            "default": ["无", "不知道", "一般", "还行", "3年", "5次", "1000元"]
        }

        # 题目类型识别
        if re.search(r'年龄|岁数|多大', question):
            return random.choice(answer_pools["age"])
        elif re.search(r'金额|价格|收入|支出|消费', question):
            return random.choice(answer_pools["income"])
        elif re.search(r'评分|打分|评价|满意度', question):
            return random.choice(answer_pools["rating"])
        elif re.search(r'日期|时间|何时|时候', question):
            return random.choice(answer_pools["date"])
        elif re.search(r'姓名|称呼', question):
            return random.choice(answer_pools["name"])
        elif re.search(r'电话|手机|联系方式', question):
            return random.choice(answer_pools["phone"])
        elif re.search(r'是否|有没有|同意吗', question):
            return random.choice(answer_pools["bool"])

        return random.choice(answer_pools["default"])

    def fill_associated_textbox(
            self, driver, question, option_element,
            default_text="自动填写内容", max_retry=8,
            ai_enabled=False, ai_api_key="", ai_prompt_template="", question_text=""
    ):
        """
        多选题/单选题选中某选项后，在整个题目区域下查找所有空白且可见的文本框，自动填入内容（支持AI）。
        """
        import time, random
        from selenium.webdriver.common.by import By

        # content内容：AI优先，否则默认
        if ai_enabled and ai_api_key and question_text and ai_prompt_template:
            try:
                content = self.zhipu_generate_answer(question_text, ai_api_key, ai_prompt_template)
            except Exception as e:
                print(f"AI生成失败: {e}")
                content = default_text + str(random.randint(1000, 9999))
        else:
            content = default_text + str(random.randint(1000, 9999))

        for _ in range(max_retry):
            candidates = []
            try:
                candidates += [el for el in question.find_elements(By.CSS_SELECTOR, "input[type='text']") if
                               el.is_displayed() and not el.get_attribute("value")]
                candidates += [el for el in question.find_elements(By.CSS_SELECTOR, "textarea") if
                               el.is_displayed() and not el.get_attribute("value")]
                candidates += [el for el in question.find_elements(By.CSS_SELECTOR, "input.OtherText") if
                               el.is_displayed() and not el.get_attribute("value")]
                candidates += [el for el in question.find_elements(By.CSS_SELECTOR, "input[placeholder*='其他']") if
                               el.is_displayed() and not el.get_attribute("value")]
                candidates += [el for el in question.find_elements(By.CSS_SELECTOR, "input[placeholder*='补充']") if
                               el.is_displayed() and not el.get_attribute("value")]
            except Exception:
                pass
            try:
                candidates += [el for el in question.find_elements(By.CSS_SELECTOR, "[contenteditable='true']") if
                               el.is_displayed() and not el.text.strip()]
            except Exception:
                pass
            uniq = []
            seen = set()
            for c in candidates:
                h = id(c)
                if h not in seen:
                    seen.add(h)
                    uniq.append(c)

            for tb in uniq:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", tb)
                except Exception:
                    pass
                try:
                    if tb.tag_name == "span" and tb.get_attribute("contenteditable") == "true":
                        driver.execute_script("arguments[0].innerText = '';", tb)
                        for ch in content:
                            tb.send_keys(ch)
                            time.sleep(random.uniform(0.01, 0.03))
                    else:
                        tb.clear()
                        for ch in content:
                            tb.send_keys(ch)
                            time.sleep(random.uniform(0.01, 0.03))
                except Exception:
                    if tb.tag_name == "span":
                        driver.execute_script("arguments[0].innerText = arguments[1];", tb, content)
                    else:
                        driver.execute_script("arguments[0].value = arguments[1];", tb, content)
                try:
                    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", tb)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", tb)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('blur', { bubbles: true }));", tb)
                except Exception:
                    pass
                val = tb.get_attribute("value") if tb.tag_name != "span" else tb.text.strip()
                if val and content[:4] in val:
                    return True
            time.sleep(0.5)

        return False

    def create_question_settings(self):
        """创建题型设置界面 - 推荐每次完整重建Canvas, Frame, Notebook等所有结构"""
        # 创建滚动框架
        self.question_canvas = tk.Canvas(self.question_frame)
        self.question_scrollbar = ttk.Scrollbar(self.question_frame, orient="vertical",
                                                command=self.question_canvas.yview)
        self.scrollable_question_frame = ttk.Frame(self.question_canvas)
        self.scrollable_question_frame.bind(
            "<Configure>",
            lambda e: self.question_canvas.configure(scrollregion=self.question_canvas.bbox("all"))
        )
        self.question_canvas.create_window((0, 0), window=self.scrollable_question_frame, anchor="nw")
        self.question_canvas.configure(yscrollcommand=self.question_scrollbar.set)
        self.question_scrollbar.pack(side="right", fill="y")
        self.question_canvas.pack(side="left", fill="both", expand=True)
        self.bind_mousewheel_to_scrollbar(self.question_canvas)  # 添加这行绑定鼠标滚轮

        # 创建Notebook（每次都新建）
        self.question_notebook = ttk.Notebook(self.scrollable_question_frame)
        self.question_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 题型tab配置
        question_types = [
            ('single_prob', "单选题", self.create_single_settings),
            ('multiple_prob', "多选题", self.create_multi_settings),
            ('matrix_prob', "矩阵题", self.create_matrix_settings),
            ('texts', "填空题", self.create_text_settings),
            ('multiple_texts', "多项填空", self.create_multiple_text_settings),
            ('reorder_prob', "排序题", self.create_reorder_settings),
            ('droplist_prob', "下拉框", self.create_droplist_settings),
            ('scale_prob', "量表题", self.create_scale_settings)
        ]
        for config_key, label_text, create_func in question_types:
            count = len(self.config[config_key])
            frame = ttk.Frame(self.question_notebook)
            self.question_notebook.add(frame, text=f"{label_text}({count})")
            desc_frame = ttk.Frame(frame)
            desc_frame.pack(fill=tk.X, padx=8, pady=5)
            if count == 0:
                ttk.Label(desc_frame, text=f"暂无{label_text}题目", font=("Arial", 10, "italic"),
                          foreground="gray").pack(pady=20)
            else:
                create_func(frame)

        # 添加提示和手动修正按钮
        tip_frame = ttk.Frame(self.scrollable_question_frame)
        tip_frame.pack(fill=tk.X, pady=10)

        # 提示标签（保留）
        ttk.Label(tip_frame, text="提示: 鼠标悬停在题号上可查看题目内容",
                  style='Warning.TLabel').pack(side=tk.LEFT, padx=5)


        self.scrollable_question_frame.update_idletasks()
        self.question_canvas.configure(scrollregion=self.question_canvas.bbox("all"))

    def correct_question_types(self):
        """手动修正题型对话框 - 增强版（带滚动条，按钮底部居中，支持鼠标滚轮，确保所有题目都能显示，弹窗居中显示）"""
        dialog = tk.Toplevel(self.root)
        dialog.title("手动修正题型")
        dialog.geometry("800x600")
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中弹窗到屏幕中间
        dialog.update_idletasks()
        w = 800
        h = 600
        screen_w = dialog.winfo_screenwidth()
        screen_h = dialog.winfo_screenheight()
        x = int((screen_w - w) / 2)
        y = int((screen_h - h) / 2)
        dialog.geometry(f"{w}x{h}+{x}+{y}")

        # 主框架
        main_frame = ttk.Frame(dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 滚动区域
        canvas = tk.Canvas(main_frame, background='#f0f0f0')
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 鼠标滚轮绑定
        self.bind_mousewheel_to_scrollbar(canvas)

        # 提示标签
        tip_label = ttk.Label(scrollable_frame,
                              text="提示：下拉框题目通常包含'请选择'文本或小三角形图标，"
                                   "如果自动识别错误请手动修正为'下拉框'",
                              style='Warning.TLabel',
                              font=("Arial", 9, "italic"),
                              wraplength=700)
        tip_label.grid(row=0, column=0, columnspan=4, pady=(0, 10), sticky=tk.W)

        # 表头
        headers = ["题号", "题目预览", "当前题型", "修正为"]
        for col, header in enumerate(headers):
            header_label = ttk.Label(scrollable_frame, text=header, font=("Arial", 9, "bold"))
            header_label.grid(row=1, column=col, padx=5, pady=5, sticky=tk.W)

        # 题型映射
        type_names = {
            "1": "填空题",
            "2": "多项填空",
            "3": "单选题",
            "4": "多选题",
            "5": "量表题",
            "6": "矩阵题",
            "7": "下拉框",
            "11": "排序题"
        }
        type_codes = {v: k for k, v in type_names.items()}
        all_types = list(type_names.values())

        # 填充数据
        self.correction_vars = {}
        row_idx = 2  # 从第2行开始（标题在第1行）
        for q_num in sorted(self.config["question_texts"].keys(), key=int):
            q_text = self.config["question_texts"][q_num]
            preview = (q_text[:25] + '...') if len(q_text) > 25 else q_text

            # 当前题型判断
            current_type_code = "unknown"
            current_type_name = "未知"

            # 检查所有题型配置
            for config_key, data in [
                ("single_prob", "单选题"),
                ("multiple_prob", "多选题"),
                ("matrix_prob", "矩阵题"),
                ("texts", "填空题"),
                ("multiple_texts", "多项填空"),
                ("reorder_prob", "排序题"),
                ("droplist_prob", "下拉框"),
                ("scale_prob", "量表题")
            ]:
                if q_num in self.config[config_key]:
                    current_type_name = data
                    current_type_code = [k for k, v in type_names.items() if v == data][0]
                    break

            # 题号
            ttk.Label(scrollable_frame, text=f"第{q_num}题").grid(
                row=row_idx, column=0, padx=5, pady=2, sticky=tk.W)

            # 题目预览
            preview_label = ttk.Label(scrollable_frame, text=preview, width=25)
            preview_label.grid(row=row_idx, column=1, padx=5, pady=2, sticky=tk.W)
            tooltip_text = f"题目类型: {current_type_name}\n\n完整题目: {q_text}"
            ToolTip(preview_label, tooltip_text, wraplength=400)

            # 当前题型
            ttk.Label(scrollable_frame, text=current_type_name).grid(
                row=row_idx, column=2, padx=5, pady=2, sticky=tk.W)

            # 修正下拉框
            var = tk.StringVar(value=current_type_name)
            self.correction_vars[q_num] = var
            combo = ttk.Combobox(scrollable_frame, textvariable=var, width=12,
                                 values=all_types, state="readonly")
            combo.grid(row=row_idx, column=3, padx=5, pady=2, sticky=tk.W)

            # 特别提示下拉框题目
            if "选择" in q_text or "下拉" in q_text or "select" in q_text.lower():
                ttk.Label(scrollable_frame, text="← 可能是下拉框",
                          style='Warning.TLabel', font=("Arial", 8)).grid(
                    row=row_idx, column=4, padx=5, pady=2, sticky=tk.W)

            row_idx += 1

        # 按钮框架 - 放在主框架底部中间
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=10, side=tk.BOTTOM)

        # 居中按钮
        apply_btn = ttk.Button(btn_frame, text="应用修正", width=15,
                               command=lambda: self.apply_corrections(dialog))
        apply_btn.pack(side=tk.LEFT, padx=10, expand=True)

        cancel_btn = ttk.Button(btn_frame, text="取消", width=15,
                                command=dialog.destroy)
        cancel_btn.pack(side=tk.LEFT, padx=10, expand=True)

    def apply_corrections(self, dialog):
        """应用手动修正"""
        type_codes = {
            "填空题": "1", "多项填空": "2", "单选题": "3",
            "多选题": "4", "量表题": "5", "矩阵题": "6",
            "下拉框": "7", "排序题": "11"
        }

        for q_num, var in self.correction_vars.items():
            new_type = type_codes.get(var.get(), "")
            if not new_type:
                continue

            # 从所有题型配置中移除该题
            for config_key in [
                "single_prob", "multiple_prob", "matrix_prob",
                "texts", "multiple_texts", "reorder_prob",
                "droplist_prob", "scale_prob"
            ]:
                if q_num in self.config[config_key]:
                    del self.config[config_key][q_num]

            # 添加到正确的题型配置
            if new_type == "1":
                self.config["texts"][q_num] = ["示例答案"]
            elif new_type == "2":
                option_count = len(self.config["option_texts"].get(q_num, []))
                self.config["multiple_texts"][q_num] = [["示例答案"]] * (option_count or 1)
            elif new_type == "3":
                self.config["single_prob"][q_num] = -1
            elif new_type == "4":
                option_count = len(self.config["option_texts"].get(q_num, []))
                self.config["multiple_prob"][q_num] = {
                    "prob": [50] * (option_count or 1),
                    "min_selection": 1,
                    "max_selection": option_count or 1
                }
            elif new_type == "5":
                option_count = len(self.config["option_texts"].get(q_num, []))
                self.config["scale_prob"][q_num] = [0.2] * (option_count or 1)
            elif new_type == "6":
                self.config["matrix_prob"][q_num] = -1
            elif new_type == "7":
                option_count = len(self.config["option_texts"].get(q_num, []))
                self.config["droplist_prob"][q_num] = [0.3] * (option_count or 1)
            elif new_type == "11":
                option_count = len(self.config["option_texts"].get(q_num, []))
                self.config["reorder_prob"][q_num] = [0.25] * (option_count or 1)

        dialog.destroy()
        self.reload_question_settings()
        logging.info("已应用手动修正")
    def update_ratio_display(self, event=None):
        """更新微信作答比率显示"""
        ratio = self.ratio_scale.get()
        self.ratio_var.set(f"{ratio * 100:.0f}%")
        self.config["weixin_ratio"] = ratio

    def parse_survey(self):
        """
        解析问卷结构并生成配置模板 - 强化题型判别
        """
        if self.parsing:
            messagebox.showwarning("警告", "正在解析问卷，请稍候...")
            return

        self.parsing = True
        self.parse_btn.config(state=tk.DISABLED, text="解析中...")
        self.status_var.set("正在解析问卷...")
        self.status_indicator.config(foreground="orange")

        threading.Thread(target=self._parse_survey_thread, daemon=True).start()

    def _parse_survey_thread(self):
        """
        解析问卷结构并生成配置模板 - 题型判别加强版（更强量表题检测，结构/文本/内容多维度）
        """
        driver = None
        try:
            url = self.url_entry.get().strip()
            if not url:
                self.root.after(0, lambda: messagebox.showerror("错误", "请输入问卷链接"))
                return

            if not re.match(r'^https?://(www\.)?wjx\.cn/vm/[\w\d]+\.aspx(#)?$', url):
                self.root.after(0, lambda: messagebox.showerror("错误", "问卷链接格式不正确"))
                return

            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--disable-gpu')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--blink-settings=imagesEnabled=false')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-logging')
            options.add_argument('--log-level=3')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-web-security')
            options.add_argument('--allow-running-insecure-content')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--disable-infobars')
            options.add_argument('--disable-save-password-bubble')
            options.add_argument('--disable-translate')
            options.add_argument('--ignore-certificate-errors')

            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1"
            ]
            options.add_argument(f'--user-agent={random.choice(user_agents)}')
            prefs = {
                'profile.default_content_setting_values': {
                    'images': 2,
                    'javascript': 1,
                    'css': 2
                }
            }
            options.add_experimental_option('prefs', prefs)

            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(20)
            driver.implicitly_wait(8)

            try:
                logging.info(f"正在访问问卷: {url}")
                driver.get(url)
                self.root.after(0, lambda: self.question_progress_var.set(10))
                self.root.after(0, lambda: self.question_status_var.set("加载问卷..."))

                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".div_question, .field, .question"))
                )

                # ----------- 增强量表题检测的JS核心 -----------
                questions_data = driver.execute_script("""
                    const getText = (element) => element ? element.textContent.trim() : '';
                    const questionSelectors = [
                        '.div_question',
                        '.field',
                        '.question',
                        '.question-wrapper',
                        '.survey-question'
                    ];
                    let questions = [];
                    for (const selector of questionSelectors) {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 0) {
                            questions = Array.from(elements);
                            break;
                        }
                    }
                    if (questions.length === 0) {
                        const potentialQuestions = document.querySelectorAll('div[id^="div"], div[id^="field"]');
                        questions = Array.from(potentialQuestions).filter(q => {
                            return q.querySelector('.question-title, .field-label, .question-text');
                        });
                    }
                    const result = [];
                    questions.forEach((q, index) => {
                        let id = q.id.replace('div', '').replace('field', '').replace('question', '') || `${index+1}`;
                        let titleElement = q.querySelector('.div_title_question, .field-label, .question-title');
                        if (!titleElement) {
                            titleElement = q.querySelector('h2, h3, .title, .question-text');
                        }
                        const title = titleElement ? getText(titleElement) : `题目${id}`;

                        // ========== 增强的量表题检测 ==========
                        let isLikertScale = false;

                        // 1. 量表相关类名
                        const scaleClasses = [
                            'scale-ul', 'scale', 'likert', 'rating', 'wjx-scale',
                            'likert-scale', 'rating-scale', 'matrix-rating'
                        ];
                        if (scaleClasses.some(cls => q.querySelector('.' + cls))) {
                            isLikertScale = true;
                        }

                        // 2. 表格结构（带量表表头）
                        if (!isLikertScale) {
                            const table = q.querySelector('table');
                            if (table) {
                                const ths = table.querySelectorAll('th');
                                const hasScaleHeaders = Array.from(ths).some(th =>
                                    /非常|比较|一般|不太|从不|满意|同意/.test(th.textContent)
                                );
                                const rows = table.querySelectorAll('tr');
                                if (rows.length > 1) {
                                    const dataRows = Array.from(rows).slice(1);
                                    const radiosPerRow = dataRows.map(row =>
                                        row.querySelectorAll('input[type="radio"]').length
                                    );
                                    if (
                                        radiosPerRow.length > 0 &&
                                        radiosPerRow.every(count => count === radiosPerRow[0]) &&
                                        radiosPerRow[0] > 1 &&
                                        hasScaleHeaders
                                    ) {
                                        isLikertScale = true;
                                    }
                                }
                            }
                        }

                        // 3. 选项文本模式
                        if (!isLikertScale) {
                            const options = q.querySelectorAll('.ulradiocheck label, .wjx-option-label, .option-label');
                            if (options.length > 0) {
                                const optionTexts = Array.from(options).map(opt => getText(opt));
                                const isLikertPattern = (
                                    optionTexts.some(t => /非常|比较|一般|不太|从不/.test(t)) ||
                                    optionTexts.some(t => /完全|大部分|部分|少量|没有/.test(t)) ||
                                    optionTexts.some(t => /总是|经常|有时|很少|从不/.test(t)) ||
                                    optionTexts.some(t => /非常满意|满意|一般|不满意|非常不满意/.test(t))
                                );
                                const allNumbers = optionTexts.every(t => /^\\d+$/.test(t));
                                const nums = optionTexts.map(t => parseInt(t));
                                const isConsecutive = nums.every((num, i, arr) => i === 0 || num === arr[i-1] + 1);
                                if ((isLikertPattern || (allNumbers && isConsecutive)) && options.length >= 3) {
                                    isLikertScale = true;
                                }
                            }
                        }

                        // 4. 特殊结构
                        if (!isLikertScale) {
                            const hasScaleDescription = q.textContent.includes('请选择最符合您情况的选项') ||
                                                       q.textContent.includes('请根据您的同意程度选择');
                            const hasEndLabels = q.querySelector('.left-label') &&
                                                 q.querySelector('.right-label');
                            if (hasScaleDescription || hasEndLabels) {
                                isLikertScale = true;
                            }
                        }

                        // ========== 排序题检测 ==========
                        const sortableSelectors = ['.sort-ul', '.sortable', '.wjx-sortable', '.ui-sortable', '.sort-container'];
                        const isSortableElement = sortableSelectors.some(sel => q.querySelector(sel));
                        const hasSortClass = /sort|sortable|reorder/i.test(q.className);
                        const hasSortText = /排序|顺序|拖动|reorder|sort/i.test(q.textContent);

                        // ========== 题型判定 ==========
                        let type = '1';
                        if (isSortableElement || hasSortClass || hasSortText) {
                            type = '11';
                        } else if (isLikertScale) {
                            type = '5';
                        } else if (q.querySelector('.ui-checkbox, input[type="checkbox"]')) {
                            type = '4';
                        } else if (q.querySelector('.ui-radio, input[type="radio"]') && !isLikertScale) {
                            type = '3';
                        } else if (q.querySelector('.matrix, table.matrix')) {
                            type = '6';
                        } else if (q.querySelector('select, .custom-select, .dropdown, .select-box')) {
                            type = '7';
                        } else if (
                            q.querySelectorAll('input[type="text"]').length > 1 ||
                            q.querySelectorAll('textarea').length > 1 ||
                            q.querySelectorAll('span[contenteditable="true"]').length > 1
                        ) {
                            type = '2';
                        } else if (
                            q.querySelectorAll('input[type="text"]').length === 1 ||
                            q.querySelectorAll('textarea').length === 1 ||
                            q.querySelectorAll('span[contenteditable="true"]').length === 1
                        ) {
                            type = '1';
                        }

                        // ========== 选项提取 ==========
                        let options = [];
                        let 空数 = 0;
                        if (type === '2') {
                            let blanks = q.querySelectorAll('input[type="text"]');
                            if (blanks.length === 0) blanks = q.querySelectorAll('textarea');
                            if (blanks.length === 0) blanks = q.querySelectorAll('span[contenteditable="true"]');
                            空数 = blanks.length;
                            for (let b of blanks) {
                                let hint = b.getAttribute('placeholder') || b.getAttribute('title') || b.getAttribute('aria-label') || '填空项';
                                options.push(hint);
                            }
                        } else if (type === '11') {
                            // 排序题选项
                            let lis = q.querySelectorAll('.sort-ul li, .sortable li, .wjx-sortable li, .ui-sortable li, .sort-container li, ul li');
                            for (let li of lis) {
                                let txt = getText(li);
                                if (txt) options.push(txt);
                            }
                        } else if (type === '7') {
                            // 下拉框选项
                            let selects = q.querySelectorAll('select');
                            if (selects.length > 0) {
                                for (let sel of selects) {
                                    for (let op of sel.options) {
                                        if (op.disabled || !op.value || op.value === "" || op.value === "请选择" || op.textContent.includes("请选择")) {
                                            continue;
                                        }
                                        options.push(op.textContent.trim());
                                    }
                                }
                            } else {
                                let customDropdowns = q.querySelectorAll('.custom-select, .dropdown, .select-box');
                                for (let dd of customDropdowns) {
                                    try {
                                        dd.click();
                                        let dropdownOptions = document.querySelectorAll('.option, .select-item, .dropdown-item');
                                        for (let op of dropdownOptions) {
                                            if (op.style.display !== 'none' && op.textContent.trim() !== "请选择") {
                                                options.push(op.textContent.trim());
                                            }
                                        }
                                        dd.click();
                                    } catch(e) {}
                                }
                            }
                            if (options.length === 0) {
                                let optionElems = q.querySelectorAll('.option, .select-item, .dropdown-item');
                                for (let op of optionElems) {
                                    if (op.textContent.trim() !== "请选择" && !op.classList.contains('disabled')) {
                                        options.push(op.textContent.trim());
                                    }
                                }
                            }
                        } else {
                            const optionSelectors = [
                                '.ulradiocheck label',
                                '.wjx-option-label',
                                '.ui-radio',
                                '.ui-checkbox',
                                'label[for]',
                                '.matrix th',
                                '.scale-ul li',
                                'select option',
                                '.option-text',
                                '.option-item',
                                '.option-label',
                                'label'
                            ];
                            for (const selector of optionSelectors) {
                                const opts = q.querySelectorAll(selector);
                                if (opts.length > 0) {
                                    opts.forEach(opt => {
                                        const text = getText(opt);
                                        if (text) options.push(text);
                                    });
                                    break;
                                }
                            }
                        }
                        result.push({
                            id: id,
                            type: type,
                            text: title,
                            options: options,
                            空数: type === '2' ? 空数 : 0
                        });
                    });
                    return result;
                """)
                # ----------- END 增强量表题检测的JS核心 -----------

                # 处理解析结果并自动生成Prompt
                self._process_parsed_questions(questions_data)

                # 更新进度状态
                self.root.after(0, lambda: self.question_progress_var.set(100))
                self.root.after(0, lambda: self.question_status_var.set("解析完成"))
                self.root.after(0, lambda: messagebox.showinfo("成功", "问卷解析成功！"))

            except TimeoutException:
                logging.error("问卷加载超时，请检查网络或链接。")
                self.root.after(0, lambda: messagebox.showerror("错误", "问卷加载超时，请检查网络或链接。"))
            except Exception as e:
                logging.error(f"解析问卷时出错: {str(e)}")
                error_msg = str(e)
                self.root.after(0, lambda: messagebox.showerror("错误", f"解析问卷时出错: {error_msg}"))
        except Exception as e:
            logging.error(f"创建浏览器驱动失败: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"创建浏览器驱动失败: {str(e)}"))
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            self.parsing = False

            self.root.after(0, lambda: self.parse_btn.config(state=tk.NORMAL, text="解析问卷"))
            self.root.after(0, lambda: self.status_var.set("就绪"))
            self.root.after(0, lambda: self.status_indicator.config(foreground="green"))

    def create_single_settings(self, frame):
        """单选题，横向紧凑排版，题目预览文本宽度适中，题目间隔适中"""
        padx, pady = 4, 2
        desc_frame = ttk.LabelFrame(frame, text="单选题配置说明")
        desc_frame.pack(fill=tk.X, padx=padx, pady=pady)
        ttk.Label(desc_frame, text="• 输入-1表示随机选择，正数为选项权重", font=("Arial", 9)).pack(anchor=tk.W)
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        headers = ["题号", "题目预览", "选项配置及操作"]
        for col, header in enumerate(headers):
            ttk.Label(table_frame, text=header, font=("Arial", 9, "bold")).grid(row=0, column=col, padx=padx, pady=pady,
                                                                                sticky=tk.W)
        for row_idx, (q_num, probs) in enumerate(self.config["single_prob"].items(), start=1):
            base_row = row_idx * 2
            q_text = self.config["question_texts"].get(q_num, f"单选题 {q_num}")
            option_count = len(self.config["option_texts"].get(q_num, [])) or 1
            ttk.Label(table_frame, text=f"第{q_num}题", font=("Arial", 10)).grid(row=base_row, column=0, padx=padx,
                                                                                 pady=pady, sticky=tk.NW)
            preview_text = q_text
            ttk.Label(table_frame, text=preview_text, width=20, anchor="w", wraplength=300).grid(row=base_row, column=1,
                                                                                                 padx=padx, pady=pady,
                                                                                                 sticky=tk.NW)
            option_line = ttk.Frame(table_frame)
            option_line.grid(row=base_row, column=2, padx=padx, pady=pady, sticky=tk.W)
            entry_row = []
            for opt_idx in range(option_count):
                ttk.Label(option_line, text=f"选项{opt_idx + 1}:", width=5).pack(side=tk.LEFT, padx=(0, 2))
                entry = ttk.Entry(option_line, width=6)
                if isinstance(probs, list) and opt_idx < len(probs):
                    entry.insert(0, str(probs[opt_idx]))
                elif probs == -1:
                    entry.insert(0, "-1")
                else:
                    entry.insert(0, "1")
                entry.pack(side=tk.LEFT, padx=(0, 2))
                entry_row.append(entry)
            self.single_entries.append(entry_row)
            btn_group = ttk.Frame(option_line)
            btn_group.pack(side=tk.LEFT, padx=(8, 0))
            ttk.Button(btn_group, text="偏左", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_bias("single", "left", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="偏右", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_bias("single", "right", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="随机", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_random("single", q, e)).pack(side=tk.LEFT,
                                                                                                           padx=1)
            ttk.Button(btn_group, text="平均", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_average("single", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Separator(table_frame, orient='horizontal').grid(
                row=base_row + 1, column=0, columnspan=3, sticky='ew', pady=10
            )

    def create_multi_settings(self, frame):
        padx, pady = 4, 2
        desc_frame = ttk.LabelFrame(frame, text="多选题配置说明")
        desc_frame.pack(fill=tk.X, padx=padx, pady=pady)
        ttk.Label(desc_frame, text="• 每个选项概率为0-100，表示被选的独立概率", font=("Arial", 9)).pack(anchor=tk.W)
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        headers = ["题号", "题目预览", "最小", "最大", "选项及操作"]
        for col, header in enumerate(headers):
            ttk.Label(table_frame, text=header, font=("Arial", 9, "bold")).grid(row=0, column=col, padx=padx, pady=pady,
                                                                                sticky=tk.W)
        self.other_entries = {}
        for row_idx, (q_num, config) in enumerate(self.config["multiple_prob"].items(), start=1):
            base_row = row_idx * 2
            q_text = self.config["question_texts"].get(q_num, f"多选题 {q_num}")
            option_count = len(self.config["option_texts"].get(q_num, [])) or 1
            ttk.Label(table_frame, text=f"第{q_num}题", font=("Arial", 10)).grid(row=base_row, column=0, padx=padx,
                                                                                 pady=pady, sticky=tk.NW)
            preview_text = q_text
            ttk.Label(table_frame, text=preview_text, width=20, anchor="w", wraplength=300).grid(row=base_row, column=1,
                                                                                                 padx=padx, pady=pady,
                                                                                                 sticky=tk.NW)
            min_entry = ttk.Spinbox(table_frame, from_=1, to=option_count, width=3)
            min_entry.set(config.get("min_selection", 1))
            min_entry.grid(row=base_row, column=2, padx=padx, pady=pady)
            self.min_selection_entries.append(min_entry)
            max_entry = ttk.Spinbox(table_frame, from_=1, to=option_count, width=3)
            max_entry.set(config.get("max_selection", option_count))
            max_entry.grid(row=base_row, column=3, padx=padx, pady=pady)
            self.max_selection_entries.append(max_entry)
            option_line = ttk.Frame(table_frame)
            option_line.grid(row=base_row, column=4, padx=padx, pady=pady, sticky=tk.W)
            entry_row = []
            option_texts = self.config["option_texts"].get(q_num, [])
            for opt_idx in range(option_count):
                ttk.Label(option_line, text=f"选项{opt_idx + 1}:", width=5).pack(side=tk.LEFT, padx=(0, 2))
                entry = ttk.Entry(option_line, width=6)
                if isinstance(config["prob"], list) and opt_idx < len(config["prob"]):
                    entry.insert(0, config["prob"][opt_idx])
                else:
                    entry.insert(0, 50)
                entry.pack(side=tk.LEFT, padx=(0, 2))
                entry_row.append(entry)
                if opt_idx < len(option_texts):
                    if "其他" in option_texts[opt_idx] or "other" in option_texts[opt_idx].lower():
                        other_edit = ttk.Entry(option_line, width=14)
                        other_values = self.config.get("other_texts", {}).get(q_num, ["自定义"])
                        other_edit.insert(0, ", ".join(other_values))
                        other_edit.pack(side=tk.LEFT, padx=(6, 0))
                        self.other_entries[q_num] = other_edit
            self.multi_entries.append(entry_row)
            btn_group = ttk.Frame(option_line)
            btn_group.pack(side=tk.LEFT, padx=(8, 0))
            ttk.Button(btn_group, text="偏左", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_bias("multiple", "left", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="偏右", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_bias("multiple", "right", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="随机", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_random("multiple", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="50%", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_value("multiple", q, e, 50)).pack(
                side=tk.LEFT, padx=1)
            ttk.Separator(table_frame, orient='horizontal').grid(
                row=base_row + 1, column=0, columnspan=5, sticky='ew', pady=10
            )

    def create_matrix_settings(self, frame):
        padx, pady = 4, 2
        desc_frame = ttk.LabelFrame(frame, text="矩阵题配置说明")
        desc_frame.pack(fill=tk.X, padx=padx, pady=pady)
        ttk.Label(desc_frame, text="• 输入-1为随机，正数为权重", font=("Arial", 9)).pack(anchor=tk.W)
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        headers = ["题号", "题目预览", "选项配置及操作"]
        for col, header in enumerate(headers):
            ttk.Label(table_frame, text=header, font=("Arial", 9, "bold")).grid(row=0, column=col, padx=padx, pady=pady,
                                                                                sticky=tk.W)
        for row_idx, (q_num, probs) in enumerate(self.config["matrix_prob"].items(), start=1):
            base_row = row_idx * 2
            q_text = self.config["question_texts"].get(q_num, f"矩阵题 {q_num}")
            option_count = len(self.config["option_texts"].get(q_num, [])) or 1
            ttk.Label(table_frame, text=f"第{q_num}题", font=("Arial", 10)).grid(row=base_row, column=0, padx=padx,
                                                                                 pady=pady, sticky=tk.NW)
            preview_text = q_text
            ttk.Label(table_frame, text=preview_text, width=20, anchor="w", wraplength=300).grid(row=base_row, column=1,
                                                                                                 padx=padx, pady=pady,
                                                                                                 sticky=tk.NW)
            option_line = ttk.Frame(table_frame)
            option_line.grid(row=base_row, column=2, padx=padx, pady=pady, sticky=tk.W)
            entry_row = []
            for opt_idx in range(option_count):
                ttk.Label(option_line, text=f"选项{opt_idx + 1}:", width=5).pack(side=tk.LEFT, padx=(0, 2))
                entry = ttk.Entry(option_line, width=6)
                if isinstance(probs, list) and opt_idx < len(probs):
                    entry.insert(0, str(probs[opt_idx]))
                elif probs == -1:
                    entry.insert(0, "-1")
                else:
                    entry.insert(0, "1")
                entry.pack(side=tk.LEFT, padx=(0, 2))
                entry_row.append(entry)
            self.matrix_entries.append(entry_row)
            btn_group = ttk.Frame(option_line)
            btn_group.pack(side=tk.LEFT, padx=(8, 0))
            ttk.Button(btn_group, text="偏左", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_bias("matrix", "left", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="偏右", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_bias("matrix", "right", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="随机", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_random("matrix", q, e)).pack(side=tk.LEFT,
                                                                                                           padx=1)
            ttk.Button(btn_group, text="平均", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_average("matrix", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Separator(table_frame, orient='horizontal').grid(
                row=base_row + 1, column=0, columnspan=3, sticky='ew', pady=10
            )

    def create_reorder_settings(self, frame):
        padx, pady = 4, 2
        desc_frame = ttk.LabelFrame(frame, text="排序题配置说明")
        desc_frame.pack(fill=tk.X, padx=padx, pady=pady)
        ttk.Label(desc_frame, text="• 每个位置的概率为相对权重", font=("Arial", 9)).pack(anchor=tk.W)
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        headers = ["题号", "题目预览", "位置概率配置及操作"]
        for col, header in enumerate(headers):
            ttk.Label(table_frame, text=header, font=("Arial", 9, "bold")).grid(row=0, column=col, padx=padx, pady=pady,
                                                                                sticky=tk.W)
        for row_idx, (q_num, probs) in enumerate(self.config["reorder_prob"].items(), start=1):
            base_row = row_idx * 2
            q_text = self.config["question_texts"].get(q_num, f"排序题 {q_num}")
            option_count = len(self.config["option_texts"].get(q_num, [])) or 1
            ttk.Label(table_frame, text=f"第{q_num}题", font=("Arial", 10)).grid(row=base_row, column=0, padx=padx,
                                                                                 pady=pady, sticky=tk.NW)
            preview_text = q_text
            ttk.Label(table_frame, text=preview_text, width=20, anchor="w", wraplength=300).grid(row=base_row, column=1,
                                                                                                 padx=padx, pady=pady,
                                                                                                 sticky=tk.NW)
            option_line = ttk.Frame(table_frame)
            option_line.grid(row=base_row, column=2, padx=padx, pady=pady, sticky=tk.W)
            entry_row = []
            for pos_idx in range(option_count):
                ttk.Label(option_line, text=f"位置{pos_idx + 1}:", width=5).pack(side=tk.LEFT, padx=(0, 2))
                entry = ttk.Entry(option_line, width=6)
                if isinstance(probs, list) and pos_idx < len(probs):
                    entry.insert(0, str(probs[pos_idx]))
                else:
                    entry.insert(0, f"{1 / option_count:.2f}")
                entry.pack(side=tk.LEFT, padx=(0, 2))
                entry_row.append(entry)
            self.reorder_entries.append(entry_row)
            btn_group = ttk.Frame(option_line)
            btn_group.pack(side=tk.LEFT, padx=(8, 0))
            ttk.Button(btn_group, text="偏前", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_bias("reorder", "left", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="偏后", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_bias("reorder", "right", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="随机", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_random("reorder", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="平均", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_average("reorder", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Separator(table_frame, orient='horizontal').grid(
                row=base_row + 1, column=0, columnspan=3, sticky='ew', pady=10
            )

    def create_droplist_settings(self, frame):
        """下拉框题配置界面 - 支持概率配置和快捷按钮"""
        padx, pady = 4, 2
        desc_frame = ttk.LabelFrame(frame, text="下拉框题配置说明")
        desc_frame.pack(fill=tk.X, padx=padx, pady=pady)
        ttk.Label(desc_frame,
                  text="• 概率英文逗号分隔，数量等于下拉选项数，支持快捷按钮\n• 示例: 0.3, 0.4, 0.3 表示三个选项的选择概率",
                  font=("Arial", 9)).pack(anchor=tk.W)

        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        headers = ["题号", "题目预览", "选项概率配置及操作"]
        for col, header in enumerate(headers):
            ttk.Label(table_frame, text=header, font=("Arial", 9, "bold")).grid(
                row=0, column=col, padx=padx, pady=pady, sticky=tk.W)

        self.droplist_entries = []  # 清空现有条目

        # 遍历配置中的所有下拉框题
        for row_idx, (q_num, probs) in enumerate(self.config["droplist_prob"].items(), start=1):
            base_row = row_idx * 2
            q_text = self.config["question_texts"].get(q_num, f"下拉题 {q_num}")

            # 直接获取选项列表
            option_texts = self.config["option_texts"].get(q_num, [])
            option_count = len(option_texts)

            ttk.Label(table_frame, text=f"第{q_num}题", font=("Arial", 10)).grid(
                row=base_row, column=0, padx=padx, pady=pady, sticky=tk.NW)
            ttk.Label(table_frame, text=q_text, width=20, anchor="w", wraplength=300).grid(
                row=base_row, column=1, padx=padx, pady=pady, sticky=tk.NW)

            # 选项配置行
            option_line = ttk.Frame(table_frame)
            option_line.grid(row=base_row, column=2, padx=padx, pady=pady, sticky=tk.W)

            # 创建输入框
            entry = ttk.Entry(option_line, width=40)

            # 处理概率配置格式
            if not isinstance(probs, list):
                # 尝试转换为列表
                if isinstance(probs, (int, float)):
                    probs = [probs]
                elif isinstance(probs, str):
                    try:
                        probs = [float(p.strip()) for p in probs.split(",")]
                    except:
                        probs = [0.3] * option_count
                else:
                    probs = [0.3] * option_count

            # 确保概率数量匹配选项数量
            if len(probs) > option_count:
                probs = probs[:option_count]
                logging.info(f"题目 {q_num} 概率配置截断为 {option_count} 项")
            elif len(probs) < option_count:
                probs = probs + [0.3] * (option_count - len(probs))
                logging.info(f"题目 {q_num} 概率配置扩展为 {option_count} 项")

            # 格式化显示
            entry_str = ", ".join(str(round(p, 2)) for p in probs)
            entry.insert(0, entry_str)
            entry.pack(side=tk.LEFT, padx=(0, 2))
            self.droplist_entries.append(entry)

            # 按钮组
            btn_group = ttk.Frame(option_line)
            btn_group.pack(side=tk.LEFT, padx=(8, 0))

            # 快捷按钮
            ttk.Button(btn_group, text="偏前", width=4,
                       command=lambda e=entry, c=option_count: self.set_question_bias("droplist", "left", None, [e],
                                                                                      c)).pack(side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="偏后", width=4,
                       command=lambda e=entry, c=option_count: self.set_question_bias("droplist", "right", None, [e],
                                                                                      c)).pack(side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="随机", width=4,
                       command=lambda e=entry, c=option_count: self.set_question_random("droplist", None, [e], c)).pack(
                side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="平均", width=4,
                       command=lambda e=entry, c=option_count: self.set_question_average("droplist", None, [e],
                                                                                         c)).pack(side=tk.LEFT, padx=1)

            # 分隔线
            ttk.Separator(table_frame, orient='horizontal').grid(
                row=base_row + 1, column=0, columnspan=3, sticky='ew', pady=10
            )

    def create_scale_settings(self, frame):
        """创建量表题设置界面 - 修复刻度数量问题"""
        padx, pady = 4, 2
        # 创建描述框架
        desc_frame = ttk.LabelFrame(frame, text="量表题配置说明")
        desc_frame.pack(fill=tk.X, padx=padx, pady=pady)
        ttk.Label(desc_frame, text="• 概率越高，被选中的几率越大", font=("Arial", 9)).pack(anchor=tk.W)

        # 创建表格框架
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # 表头
        headers = ["题号", "题目预览", "刻度概率配置及操作"]
        for col, header in enumerate(headers):
            ttk.Label(table_frame, text=header, font=("Arial", 9, "bold")).grid(
                row=0, column=col, padx=padx, pady=pady, sticky=tk.W)

        # 遍历所有量表题配置
        for row_idx, (q_num, probs) in enumerate(self.config["scale_prob"].items(), start=1):
            base_row = row_idx * 2
            q_text = self.config["question_texts"].get(q_num, f"量表题 {q_num}")

            # 关键修复：使用概率配置列表的长度作为刻度数量
            option_count = len(probs) if probs else 0

            # 题号标签
            ttk.Label(table_frame, text=f"第{q_num}题", font=("Arial", 10)).grid(
                row=base_row, column=0, padx=padx, pady=pady, sticky=tk.NW)

            # 题目预览（带提示）
            preview_text = q_text[:30] + "..." if len(q_text) > 30 else q_text
            preview_label = ttk.Label(table_frame, text=preview_text, width=20, anchor="w", wraplength=300)
            preview_label.grid(row=base_row, column=1, padx=padx, pady=pady, sticky=tk.NW)

            # 添加题目提示
            ToolTip(preview_label, f"完整题目: {q_text}", wraplength=400)

            # 选项配置行
            option_line = ttk.Frame(table_frame)
            option_line.grid(row=base_row, column=2, padx=padx, pady=pady, sticky=tk.W)

            # 创建每个刻度的输入框
            entry_row = []
            for opt_idx in range(option_count):
                ttk.Label(option_line, text=f"刻度{opt_idx + 1}:", width=5).pack(side=tk.LEFT, padx=(0, 2))
                entry = ttk.Entry(option_line, width=6)
                if opt_idx < len(probs):
                    entry.insert(0, str(probs[opt_idx]))
                else:
                    entry.insert(0, "0.2")  # 默认值
                entry.pack(side=tk.LEFT, padx=(0, 2))
                entry_row.append(entry)

            # 保存输入框引用
            self.scale_entries.append(entry_row)

            # 按钮组
            btn_group = ttk.Frame(option_line)
            btn_group.pack(side=tk.LEFT, padx=(8, 0))

            # 快捷操作按钮
            ttk.Button(btn_group, text="偏左", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_bias("scale", "left", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="偏右", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_bias("scale", "right", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="随机", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_random("scale", q, e)).pack(
                side=tk.LEFT, padx=1)
            ttk.Button(btn_group, text="平均", width=4,
                       command=lambda q=q_num, e=entry_row: self.set_question_average("scale", q, e)).pack(
                side=tk.LEFT, padx=1)

            # 分隔线
            ttk.Separator(table_frame, orient='horizontal').grid(
                row=base_row + 1, column=0, columnspan=3, sticky='ew', pady=10
            )

    def create_text_settings(self, frame):
        padx, pady = 4, 2
        desc_frame = ttk.LabelFrame(frame, text="填空题配置说明")
        desc_frame.pack(fill=tk.X, padx=padx, pady=pady)
        ttk.Label(desc_frame, text="• 填空题答案用逗号分隔，自动随机选", font=("Arial", 9)).pack(anchor=tk.W)
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        headers = ["题号", "题目预览", "答案配置"]
        for col, header in enumerate(headers):
            ttk.Label(table_frame, text=header, font=("Arial", 9, "bold")).grid(row=0, column=col, padx=padx, pady=pady,
                                                                                sticky=tk.W)
        for row_idx, (q_num, answers) in enumerate(self.config["texts"].items(), start=1):
            base_row = row_idx * 2
            q_text = self.config["question_texts"].get(q_num, f"填空题 {q_num}")
            option_count = len(self.config["option_texts"].get(q_num, [])) or 1
            ttk.Label(table_frame, text=f"第{q_num}题", font=("Arial", 10)).grid(row=base_row, column=0, padx=padx,
                                                                                 pady=pady, sticky=tk.NW)
            preview_text = q_text
            ttk.Label(table_frame, text=preview_text, width=20, anchor="w", wraplength=300).grid(row=base_row, column=1,
                                                                                                 padx=padx, pady=pady,
                                                                                                 sticky=tk.NW)
            answer_line = ttk.Frame(table_frame)
            answer_line.grid(row=base_row, column=2, padx=padx, pady=pady, sticky=tk.W)
            entry_row = []
            for i in range(option_count):
                entry = ttk.Entry(answer_line, width=14)
                answer_str = ", ".join(answers) if i == 0 else ""
                entry.insert(0, answer_str)
                entry.pack(side=tk.LEFT, padx=(0, 2))
                entry_row.append(entry)
            self.text_entries.append(entry_row)
            reset_btn = ttk.Button(answer_line, text="重置", width=6,
                                   command=lambda e=entry_row: [ent.delete(0, tk.END) or ent.insert(0, "示例答案") for
                                                                ent in e])
            reset_btn.pack(side=tk.LEFT, padx=(6, 0))
            ttk.Separator(table_frame, orient='horizontal').grid(
                row=base_row + 1, column=0, columnspan=3, sticky='ew', pady=10
            )

    def create_multiple_text_settings(self, frame):
        padx, pady = 4, 2
        desc_frame = ttk.LabelFrame(frame, text="多项填空配置说明")
        desc_frame.pack(fill=tk.X, padx=padx, pady=pady)
        ttk.Label(desc_frame, text="• 每空答案用逗号分隔，自动随机选", font=("Arial", 9)).pack(anchor=tk.W)
        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        headers = ["题号", "题目预览", "答案配置"]
        for col, header in enumerate(headers):
            ttk.Label(table_frame, text=header, font=("Arial", 9, "bold")).grid(row=0, column=col, padx=padx, pady=pady,
                                                                                sticky=tk.W)
        for row_idx, (q_num, answers_list) in enumerate(self.config["multiple_texts"].items(), start=1):
            base_row = row_idx * 2
            q_text = self.config["question_texts"].get(q_num, f"多项填空 {q_num}")
            option_count = len(self.config["option_texts"].get(q_num, [])) or len(answers_list) or 1
            ttk.Label(table_frame, text=f"第{q_num}题", font=("Arial", 10)).grid(row=base_row, column=0, padx=padx,
                                                                                 pady=pady, sticky=tk.NW)
            preview_text = q_text
            ttk.Label(table_frame, text=preview_text, width=20, anchor="w", wraplength=300).grid(row=base_row, column=1,
                                                                                                 padx=padx, pady=pady,
                                                                                                 sticky=tk.NW)
            answer_line = ttk.Frame(table_frame)
            answer_line.grid(row=base_row, column=2, padx=padx, pady=pady, sticky=tk.W)
            entry_row = []
            for i in range(option_count):
                entry = ttk.Entry(answer_line, width=14)
                answer_str = ", ".join(answers_list[i]) if i < len(answers_list) else ""
                entry.insert(0, answer_str)
                entry.pack(side=tk.LEFT, padx=(0, 2))
                entry_row.append(entry)
            self.multiple_text_entries.append(entry_row)
            reset_btn = ttk.Button(answer_line, text="重置", width=6,
                                   command=lambda e=entry_row: [ent.delete(0, tk.END) or ent.insert(0, "示例答案") for
                                                                ent in e])
            reset_btn.pack(side=tk.LEFT, padx=(6, 0))
            ttk.Separator(table_frame, orient='horizontal').grid(
                row=base_row + 1, column=0, columnspan=3, sticky='ew', pady=10
            )

    def auto_click_next_page(self, driver):
        """
        更鲁棒的问卷星翻页函数：多重检测，保证翻页成功才返回True，否则False。
        优化点：
        - 只统计可见题目，防止隐藏题目影响判断
        - 检查URL、题目内容、页码文本、下一页按钮消失
        - 日志详细，便于排查
        """
        import time
        from selenium.webdriver.common.by import By
        import logging

        prev_url = driver.current_url
        try:
            main_questions = driver.find_elements(By.CSS_SELECTOR, ".div_question, .field, .question")
            prev_q_texts = [q.text[:30] for q in main_questions if q.is_displayed()] if main_questions else []
        except Exception:
            prev_q_texts = []

        # 多种方式查找“下一页”按钮
        selectors = [
            "#divNext a", "a[id*='NextPage']", "a[onclick*='next']", "button.next"
        ]
        next_btn = None
        for sel in selectors:
            try:
                btns = driver.find_elements(By.CSS_SELECTOR, sel)
                for b in btns:
                    if b.is_displayed() and b.is_enabled():
                        next_btn = b
                        break
                if next_btn:
                    break
            except Exception:
                continue
        # 兜底：文本查找
        if not next_btn:
            try:
                btns = driver.find_elements(By.XPATH, "//*[contains(text(),'下一页') or contains(text(),'Next')]")
                for b in btns:
                    if b.is_displayed() and b.is_enabled():
                        next_btn = b
                        break
            except Exception:
                pass

        if not next_btn:
            logging.warning("未找到下一页按钮")
            return False

        # 尝试点击
        try:
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", next_btn)
            time.sleep(0.1)
            next_btn.click()
        except Exception:
            try:
                driver.execute_script("arguments[0].click();", next_btn)
            except Exception as e:
                logging.error(f"下一页按钮点击失败: {e}")
                return False

        # 动态检测页面变化（最多5秒，每0.2s检测一次）
        start = time.time()
        while time.time() - start < 5:
            # 1. URL变化
            if driver.current_url != prev_url:
                logging.info("翻页成功：URL已变化")
                return True
            # 2. 题目内容变化
            try:
                new_questions = driver.find_elements(By.CSS_SELECTOR, ".div_question, .field, .question")
                new_q_texts = [q.text[:30] for q in new_questions if q.is_displayed()] if new_questions else []
                if new_q_texts != prev_q_texts and new_q_texts:
                    logging.info("翻页成功：题目内容已变化")
                    return True
            except Exception:
                pass
            # 3. 页码文本变化
            page_source = driver.page_source
            if any(word in page_source for word in ["第2页", "第3页", "Page 2", "Page 3", "下一页", "Next"]):
                logging.info("翻页成功：检测到页码变化")
                return True
            # 4. 下一页按钮消失（有些模板最后一页“下一页”按钮直接消失）
            try:
                btns = driver.find_elements(By.CSS_SELECTOR, "#divNext a, a[id*='NextPage']")
                if not any(b.is_displayed() for b in btns):
                    logging.info("翻页成功：下一页按钮消失")
                    return True
            except Exception:
                pass
            # 5. 验证码出现
            if any(word in page_source for word in ["验证码", "geetest_panel", "nc_iconfont"]):
                logging.warning("出现验证码，翻页流程暂停")
                return False
            time.sleep(0.2)
        logging.warning("翻页超时，页面未变化")
        return False

    def safe_click(self, driver, element):
        """
        安全点击元素，处理各种点击异常情况
        """
        import time
        from selenium.common.exceptions import ElementClickInterceptedException

        try:
            # 滚动元素到视图中央
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center', inline: 'center'});",
                element
            )
            time.sleep(0.5)

            # 尝试直接点击
            try:
                element.click()
                time.sleep(1)  # 等待页面响应
                return True
            except ElementClickInterceptedException:
                # 处理被遮挡的情况
                try:
                    # 尝试点击元素的中心点
                    location = element.location
                    size = element.size
                    x = location['x'] + size['width'] // 2
                    y = location['y'] + size['height'] // 2

                    actions = ActionChains(driver)
                    actions.move_to_element_with_offset(element, 0, 0)
                    actions.move_by_offset(size['width'] // 2, size['height'] // 2)
                    actions.click()
                    actions.perform()
                    time.sleep(1)
                    return True
                except Exception:
                    # 最后尝试JavaScript点击
                    try:
                        driver.execute_script("arguments[0].click();", element)
                        time.sleep(1)
                        return True
                    except Exception as e:
                        logging.error(f"JavaScript点击失败: {str(e)}")
                        return False
            except Exception as e:
                logging.error(f"直接点击失败: {str(e)}")
                return False
        except Exception as e:
            logging.error(f"安全点击异常: {str(e)}")
            return False

    def is_next_page_loaded(self, driver, prev_url=None, prev_q_texts=None):
        """
        更鲁棒的一次性检测，判断页面是否已翻页。
        - prev_url: 翻页前的URL
        - prev_q_texts: 翻页前题目文本列表
        """
        import logging
        from selenium.webdriver.common.by import By

        try:
            if prev_url and driver.current_url != prev_url:
                logging.info("检测到URL已变化，已翻页")
                return True
            # 题目内容变化
            new_questions = driver.find_elements(By.CSS_SELECTOR, ".div_question, .field, .question")
            new_q_texts = [q.text[:30] for q in new_questions] if new_questions else []
            if prev_q_texts is not None and new_q_texts != prev_q_texts and new_q_texts:
                logging.info("检测到题目内容变化，已翻页")
                return True
            # 页码文本
            page_source = driver.page_source
            if any(word in page_source for word in ["第2页", "第3页", "Page 2", "Page 3", "下一页", "Next"]):
                logging.info("检测到页码变化，已翻页")
                return True
            # 下一页按钮消失
            try:
                btns = driver.find_elements(By.CSS_SELECTOR, "#divNext a, a[id*='NextPage']")
                if not any(b.is_displayed() for b in btns):
                    logging.info("下一页按钮消失，疑似已翻页")
                    return True
            except Exception:
                pass
        except Exception as e:
            logging.error(f"is_next_page_loaded检测异常: {e}")
        return False

    def set_question_bias(self, q_type, direction, q_num, entries):
        """为单个题目设置偏左或偏右分布"""
        bias_factors = {
            "left": [0.4, 0.3, 0.2, 0.1, 0.05],
            "right": [0.05, 0.1, 0.2, 0.3, 0.4]
        }

        factors = bias_factors.get(direction, [0.2, 0.2, 0.2, 0.2, 0.2])

        for i, entry in enumerate(entries):
            if i < len(factors):
                prob = factors[i]
            else:
                prob = factors[-1] * (0.8 ** (i - len(factors) + 1))  # 指数衰减

            # 根据题目类型格式化概率值
            if q_type == "multiple":
                prob_value = int(prob * 100)
            else:
                prob_value = f"{prob:.2f}"

            entry.delete(0, tk.END)
            entry.insert(0, str(prob_value))

        logging.info(f"第{q_num}题已设置为{direction}偏置")

    def set_question_random(self, q_type, q_num, entries):
        """为单个题目设置随机选择"""
        for entry in entries:
            entry.delete(0, tk.END)
            entry.insert(0, "-1")

        logging.info(f"第{q_num}题已设置为随机选择")

    def set_question_average(self, q_type, q_num, entries):
        """为单个题目设置平均概率"""
        option_count = len(entries)
        if option_count == 0:
            return

        avg_prob = 1.0 / option_count

        for entry in entries:
            entry.delete(0, tk.END)
            if q_type == "multiple":
                entry.insert(0, str(int(avg_prob * 100)))
            else:
                entry.insert(0, f"{avg_prob:.2f}")

        logging.info(f"第{q_num}题已设置为平均概率")

    def set_question_value(self, q_type, q_num, entries, value):
        """为单个题目设置指定值（多用于多选题）"""
        for entry in entries:
            entry.delete(0, tk.END)
            entry.insert(0, str(value))

        logging.info(f"第{q_num}题已设置为{value}%概率")

    def clear_log(self):
        """清空日志"""
        self.log_area.config(state=tk.NORMAL)
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state=tk.DISABLED)
        logging.info("日志已清空")

    def export_log(self):
        """导出日志到文件"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile="wjx_log.txt"
            )
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_area.get(1.0, tk.END))
                logging.info(f"日志已导出到: {file_path}")
                messagebox.showinfo("成功", "日志导出成功！")
        except Exception as e:
            logging.error(f"导出日志时出错: {str(e)}")
            messagebox.showerror("错误", f"导出日志时出错: {str(e)}")

    def update_font(self, *args):
        """更新UI字体"""
        try:
            font_family = self.font_family.get()
            try:
                font_size = int(self.font_size.get())
            except (ValueError, TypeError):
                font_size = 10
                self.font_size.set(10)

            # 确保字体族名称有效
            if not font_family or font_family not in tk.font.families():
                font_family = "Arial"
                self.font_family.set(font_family)

            new_font = (font_family, font_size)

            # 更新所有控件的字体
            style = ttk.Style()
            style.configure('.', font=new_font)

            # 更新日志区域字体
            self.log_area.configure(font=new_font)

            # 更新按钮字体
            self.start_btn.configure(style='TButton')
            self.pause_btn.configure(style='TButton')
            self.stop_btn.configure(style='TButton')
            self.parse_btn.configure(style='TButton')

            # 更新标签字体
            for widget in self.root.winfo_children():
                self.update_widget_font(widget, new_font)

        except Exception as e:
            logging.error(f"更新字体时出错: {str(e)}")
            self.font_family.set("Arial")
            self.font_size.set(10)

    def update_widget_font(self, widget, font):
        """递归更新控件的字体"""
        try:
            # 更新当前控件
            if hasattr(widget, 'configure') and 'font' in widget.configure():
                widget.configure(font=font)

            # 递归更新子控件
            for child in widget.winfo_children():
                self.update_widget_font(child, font)
        except Exception as e:
            logging.debug(f"更新控件字体时出错: {str(e)}")

    def on_ai_service_change(self, event=None):
        """动态显示/隐藏API Key输入框"""
        service = self.ai_service.get()
        if service == "OpenAI":
            # 显示OpenAI相关控件
            self.openai_api_key_label.grid()
            self.openai_api_key_entry.grid()
            # 隐藏质谱清言相关控件
            self.qingyan_api_key_label.grid_remove()
            self.qingyan_api_key_entry.grid_remove()
            self.api_link.grid_remove()
            # 修改提示文本
            self.refresh_prompt_btn.config(text="重新生成Prompt(OpenAI)")
        else:
            # 显示质谱清言相关控件
            self.qingyan_api_key_label.grid()
            self.qingyan_api_key_entry.grid()
            self.api_link.grid()
            # 隐藏OpenAI相关控件
            self.openai_api_key_label.grid_remove()
            self.openai_api_key_entry.grid_remove()
            # 恢复按钮文本
            self.refresh_prompt_btn.config(text="重新生成Prompt(质谱清言)")
    def reload_question_settings(self):
        """重新加载题型设置界面 - 彻底销毁重建所有控件"""
        # 销毁所有子控件（包括Canvas/Scrollbar/Frame/Notebook）
        for widget in self.question_frame.winfo_children():
            widget.destroy()
        # 清空输入框和tooltip引用
        self.single_entries = []
        self.multi_entries = []
        self.min_selection_entries = []
        self.max_selection_entries = []
        self.matrix_entries = []
        self.text_entries = []
        self.multiple_text_entries = []
        self.reorder_entries = []
        self.droplist_entries = []
        self.scale_entries = []
        self.tooltips = []
        self.other_entries = {}
        # 重新创建所有内容
        self.create_question_settings()
        # 确保界面刷新
        self.root.update_idletasks()

    def start_filling(self):
        """开始填写问卷"""
        try:
            # 保存当前配置
            if not self.save_config():
                return

            # 验证基本参数
            if not self.config["url"]:
                messagebox.showerror("错误", "请输入问卷链接")
                return

            try:
                self.config["target_num"] = int(self.target_entry.get())
                if self.config["target_num"] <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror("错误", "目标份数必须是正整数")
                return

            # 验证URL格式
            if not re.match(r'^https?://(www\.)?wjx\.cn/vm/[\w\d]+\.aspx(#)?$', self.config["url"]):
                messagebox.showerror("错误", "问卷链接格式不正确")
                return

            # 更新运行状态
            self.running = True
            self.paused = False
            self.cur_num = 0
            self.cur_fail = 0
            self.pause_event.clear()

            # 更新按钮状态
            self.start_btn.config(state=tk.DISABLED, text="▶ 运行中")
            self.pause_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_indicator.config(foreground="green")

            # 设置进度条初始值
            self.progress_var.set(0)
            self.question_progress_var.set(0)
            self.status_var.set("运行中...")

            # 创建并启动线程
            self.threads = []
            for i in range(self.config["num_threads"]):
                x = (i % 2) * 600
                y = (i // 2) * 400
                t = threading.Thread(target=self.run_filling, args=(x, y), daemon=True)
                t.start()
                self.threads.append(t)

            # 启动进度更新线程（不再传参）
            progress_thread = threading.Thread(target=self.update_progress, daemon=True)
            progress_thread.start()

        except Exception as e:
            logging.error(f"启动失败: {str(e)}")
            messagebox.showerror("错误", f"启动失败: {str(e)}")

    def run_filling(self, x=0, y=0):
        """
        运行填写任务 - 可用微信作答比率滑动条控制微信来源填写比例
        增强：自动处理invalid session id异常，driver失效自动重启。
        """
        import random
        import time
        from selenium import webdriver
        import logging
        driver = None
        submit_count = 0
        proxy_ip = None

        WECHAT_UA = (
            "Mozilla/5.0 (Linux; Android 10; MI 8 Build/QKQ1.190828.002; wv) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/86.0.4240.99 "
            "XWEB/4317 MMWEBSDK/20220105 Mobile Safari/537.36 "
            "MicroMessenger/8.0.18.2040(0x28001235) "
            "Process/toolsmp WeChat/arm64 NetType/WIFI Language/zh_CN ABI/arm64"
        )
        PC_UA = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )

        def create_driver(options):
            try:
                return webdriver.Chrome(options=options)
            except Exception as e:
                logging.error(f"创建浏览器驱动失败: {e}")
                time.sleep(10)
                return None

        try:
            while self.running and self.cur_num < self.config["target_num"]:
                if self.paused:
                    time.sleep(1)
                    continue

                # 微信来源比例
                use_weixin = random.random() < float(self.config.get("weixin_ratio", 0.5))

                # chromedriver选项
                options = webdriver.ChromeOptions()
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option("useAutomationExtension", False)
                options.add_argument('--disable-blink-features=AutomationControlled')
                ua = WECHAT_UA if use_weixin else PC_UA
                options.add_argument(f'--user-agent={ua}')
                options.add_argument('--disable-gpu')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                if self.config["headless"]:
                    options.add_argument('--headless')
                else:
                    options.add_argument(f'--window-position={x},{y}')

                # 代理设置
                use_ip = self.config.get("use_ip", False)
                ip_mode = self.config.get("ip_change_mode", "per_submit")
                ip_batch = self.config.get("ip_change_batch", 5)
                need_new_proxy = False
                if use_ip:
                    if ip_mode == "per_submit":
                        need_new_proxy = True
                    elif ip_mode == "per_batch":
                        if submit_count % ip_batch == 0:
                            need_new_proxy = True
                if use_ip and need_new_proxy:
                    proxy_ip = self.get_new_proxy()
                    if proxy_ip:
                        logging.info(f"使用代理: {proxy_ip}")
                        options.add_argument(f'--proxy-server={proxy_ip}')
                    else:
                        logging.error("本次未获取到有效代理，等待10秒后重试。")
                        time.sleep(10)
                        continue
                elif use_ip and proxy_ip:
                    options.add_argument(f'--proxy-server={proxy_ip}')

                driver = create_driver(options)
                if not driver:
                    continue

                try:
                    # 设置窗口
                    if not self.config["headless"]:
                        if use_weixin:
                            driver.set_window_size(375, 812)
                        else:
                            driver.set_window_size(1024, 768)

                    driver.get(self.config["url"])
                    time.sleep(self.config["page_load_delay"])

                    # 填写问卷并自动处理invalid session id异常
                    max_retry = 2
                    for attempt in range(max_retry):
                        try:
                            success = self.fill_survey(driver)
                            if success:
                                with self.lock:
                                    self.cur_num += 1
                                logging.info(f"第 {self.cur_num} 份问卷提交成功")
                            else:
                                with self.lock:
                                    self.cur_fail += 1
                                logging.warning(f"第 {self.cur_num + 1} 份问卷提交失败")
                            break
                        except Exception as e:
                            err_msg = str(e)
                            if "invalid session id" in err_msg.lower() or "invalid session" in err_msg.lower():
                                logging.error("检测到invalid session id，重建driver后重试")
                                try:
                                    driver.quit()
                                except:
                                    pass
                                driver = create_driver(options)
                                if not driver:
                                    break
                                driver.get(self.config["url"])
                                time.sleep(self.config["page_load_delay"])
                                continue
                            else:
                                with self.lock:
                                    self.cur_fail += 1
                                logging.error(f"填写问卷时出错: {err_msg}")
                                import traceback
                                traceback.print_exc()
                                break

                except Exception as e:
                    with self.lock:
                        self.cur_fail += 1
                    logging.error(f"填写问卷时出错: {str(e)}")
                    import traceback
                    traceback.print_exc()
                finally:
                    try:
                        driver.quit()
                    except:
                        pass

                submit_count += 1

                # 智能提交间隔逻辑
                if self.config.get("enable_smart_gap", True):
                    batch_size = self.config.get("batch_size", 5)
                    if batch_size > 0 and submit_count % batch_size == 0:
                        batch_pause_minutes = self.config.get("batch_pause", 15)
                        batch_pause_seconds = batch_pause_minutes * 60
                        logging.info(f"已完成{submit_count}份问卷，批量休息{batch_pause_minutes}分钟...")
                        for i in range(batch_pause_seconds):
                            if not self.running:
                                break
                            time.sleep(1)
                    else:
                        min_gap = self.config.get("min_submit_gap", 10)
                        max_gap = self.config.get("max_submit_gap", 20)
                        if min_gap > max_gap:
                            min_gap, max_gap = max_gap, min_gap
                        submit_interval_minutes = random.uniform(min_gap, max_gap)
                        submit_interval_seconds = submit_interval_minutes * 60
                        logging.info(f"本次提交后等待{submit_interval_minutes:.2f}分钟...")
                        for i in range(int(submit_interval_seconds)):
                            if not self.running:
                                break
                            time.sleep(1)

        except Exception as e:
            logging.error(f"运行任务时出错: {str(e)}")
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

    def fill_survey(self, driver):
        """
        改进版：填写问卷，题目进度条按“实际可见题数”显示，避免统计错误，防死循环/多处理第一页。
        修正版：无题目时尝试提交按钮！
        """
        import random
        import time
        import logging
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, WebDriverException

        current_page = 1
        max_pages = 20  # 设置一个合理的最大页数限制
        processed_signatures = set()  # 用于判重，多页URL不变时内容不同也能识别

        def try_submit_on_no_question(driver):
            """
            当页面无题目时，尝试查找并点击提交按钮（兼容不同模板）
            """
            submit_selectors = [
                "#submit_button", "#ctlNext", "input[value*='提交']", "a.submitbutton", "#btnSubmit",
                ".submit-btn", ".submitbutton", ".btn-submit", ".btn-success",
                "button[type='submit']", "input[type='submit']",
                "div.submit", ".survey-submit", "button", "a"
            ]
            for sel in submit_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, sel)
                    for elem in elements:
                        if elem.is_displayed():
                            text = elem.text or elem.get_attribute("value") or ""
                            # 只要有“提交”、“完成”、“交卷”等字样就判定为提交按钮
                            if any(word in text for word in ["提交", "完成", "交卷", "确定", "submit"]):
                                try:
                                    elem.click()
                                    time.sleep(1)
                                    return True
                                except Exception:
                                    continue
                except Exception:
                    continue
            return False

        while current_page <= max_pages and self.running:
            logging.info(f"正在处理第 {current_page} 页问卷")

            # 等待题目加载
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".div_question, .field, .question"))
                )
            except TimeoutException:
                logging.warning("页面加载超时，尝试刷新")
                driver.refresh()
                time.sleep(1)
                continue
            except WebDriverException as e:
                logging.error(f"WebDriver异常: {e}")
                break

            # 获取当前页题目，只统计可见题
            questions = [
                q for q in driver.find_elements(
                    By.CSS_SELECTOR,
                    ".field.ui-field-contain, .div_question, .question, .survey-question"
                )
                if q.is_displayed()
            ]
            total_questions = len(questions)

            # ==== 用页面内容hash判重 ====
            cur_page_signature = "|".join([q.text.strip()[:30] for q in questions]) if questions else driver.current_url
            if cur_page_signature in processed_signatures:
                logging.warning("检测到重复页面，跳出循环避免死循环")
                break
            processed_signatures.add(cur_page_signature)
            # ==== END ====

            # 如果没有题目，优先尝试提交
            if total_questions == 0:
                logging.info("本页无可见题目，尝试提交或翻页")
                if try_submit_on_no_question(driver):
                    logging.info("无题目页已成功提交")
                    return True
                if self.auto_click_next_page(driver):
                    current_page += 1
                    continue
                else:
                    logging.warning("未检测到可见题目，也未发现可点击的下一页/继续按钮或提交按钮")
                    break

            # 计算本页答题时间
            total_time = random.randint(self.config["min_duration"], self.config["max_duration"])
            start_time = time.time()
            avg_time_per_question = total_time / total_questions
            remaining_time = total_time
            already_filled = set()

            # 填写本页所有题目
            for i, q in enumerate(questions):
                if not self.running:
                    break

                q_id = q.get_attribute("id") or f"q_{i}_{current_page}"
                if q_id in already_filled:
                    continue

                current_question = i + 1
                # 局部刷新题目进度条和状态文本
                self.question_progress_var.set(int((current_question / total_questions) * 100))
                self.question_status_var.set(f"第{current_page}页 题目:{current_question}/{total_questions}")

                # 计算每题时间
                if i == total_questions - 1:
                    question_time = remaining_time
                else:
                    question_time = min(
                        random.uniform(avg_time_per_question * 0.5, avg_time_per_question * 1.5),
                        remaining_time - (total_questions - i - 1)
                    )

                question_start = time.time()

                try:
                    q_type = q.get_attribute("type")
                    q_num = q_id.replace("div", "") if q_id else str(current_question)

                    # 主动填写
                    if q_type == "1" or q_type == "2":
                        self.fill_text(driver, q, q_num)
                    elif q_type == "3":
                        self.fill_single(driver, q, q_num)
                    elif q_type == "4":
                        self.fill_multiple(driver, q, q_num)
                    elif q_type == "5":
                        self.fill_scale(driver, q, q_num)
                    elif q_type == "6":
                        self.fill_matrix(driver, q, q_num)
                    elif q_type == "7":
                        self.fill_droplist(driver, q, q_num)
                    elif q_type == "11":
                        self.fill_reorder(driver, q, q_num)
                    else:
                        self.auto_detect_question_type(driver, q, q_num)

                    # 填写后检测
                    if self.is_filled(q):
                        already_filled.add(q_id)
                    else:
                        if q_type != "11":  # 排序题不需要重试
                            self.auto_detect_question_type(driver, q, q_num)
                            if self.is_filled(q):
                                already_filled.add(q_id)

                    elapsed = time.time() - question_start
                    if elapsed < question_time:
                        time.sleep(question_time - elapsed)
                    remaining_time -= time.time() - question_start

                except WebDriverException as e:
                    if 'no such window' in str(e).lower():
                        logging.error("浏览器窗口已关闭或失效，停止本线程填充")
                        return False
                    logging.error(f"填写第{q_num}题时WebDriver出错: {str(e)}")
                    break
                except Exception as e:
                    logging.error(f"填写第{q_num}题时出错: {str(e)}")
                    continue

            # 补填本页未填题目
            questions2 = [
                q for q in driver.find_elements(
                    By.CSS_SELECTOR,
                    ".field.ui-field-contain, .div_question, .question, .survey-question"
                )
                if q.is_displayed()
            ]
            for q in questions2:
                q_id = q.get_attribute("id") or ""
                if q_id in already_filled:
                    continue

                is_required = False
                try:
                    if q.find_element(By.CSS_SELECTOR, ".required, .star, .necessary, .wjxnecessary"):
                        is_required = True
                except:
                    if "必答" in q.text or q.get_attribute("data-required") == "1":
                        is_required = True

                if not is_required and self.is_filled(q):
                    continue

                if not self.is_filled(q):
                    q_num = q_id.replace("div", "") if q_id else ""
                    try:
                        self.auto_detect_question_type(driver, q, q_num)
                        if self.is_filled(q):
                            already_filled.add(q_id)
                    except WebDriverException as e:
                        if 'no such window' in str(e).lower():
                            logging.error("浏览器窗口已关闭或失效，停止本线程填充")
                            return False
                        logging.warning(f"补填题目{q_num}时WebDriver出错: {e}")
                    except Exception as e:
                        logging.warning(f"补填题目{q_num}时出错: {e}")

            # 确保本页答题时间
            elapsed_total = time.time() - start_time
            if elapsed_total < total_time:
                time.sleep(total_time - elapsed_total)

            # 尝试点击下一页
            if self.auto_click_next_page(driver):
                current_page += 1
                continue

            # 如果没有下一页按钮，检查是否真的到最后一页
            submit_button = driver.find_elements(By.CSS_SELECTOR,
                                                 "#submit_button, #ctlNext, input[value*='提交'], a.submitbutton, #btnSubmit")
            if not submit_button:
                # 再次尝试无题目提交
                if try_submit_on_no_question(driver):
                    logging.info("最后一页无题目已成功提交")
                    return True
                logging.warning("未找到提交按钮，可能不是最后一页，尝试刷新")
                driver.refresh()
                time.sleep(2)
                continue

            logging.info("没有下一页，准备提交问卷")
            return self.submit_survey(driver)

    def auto_detect_question_type(self, driver, question, q_num):
        """
        自动检测题型并填写 - 填空/多项填空统一用 fill_text(driver, question, q_num)
        """
        import random
        import time
        from selenium.webdriver.common.by import By

        try:
            sort_lis = question.find_elements(By.CSS_SELECTOR,
                                              ".sort-ul li, .sortable li, .wjx-sortable li, .ui-sortable li, .sort-container li, ul.sort-ul > li, ul.sortable > li"
                                              )
            if sort_lis and len(sort_lis) >= 2:
                self.fill_reorder(driver, question, q_num)
                return

            try:
                title_elem = question.find_element(By.CSS_SELECTOR,
                                                   ".div_title_question, .question-title, .field-label")
                title_text = title_elem.text.strip()
                if "排序" in title_text or "顺序" in title_text or "拖动" in title_text:
                    self.fill_reorder(driver, question, q_num)
                    return
            except Exception:
                pass

            radio_btns = question.find_elements(By.CSS_SELECTOR, ".ui-radio, input[type='radio']")
            if radio_btns:
                self.fill_single(driver, question, q_num)
                return

            checkboxes = question.find_elements(By.CSS_SELECTOR, ".ui-checkbox, input[type='checkbox']")
            if checkboxes:
                self.fill_multiple(driver, question, q_num)
                return

            # 填空题/多项填空，span或input/textarea都统一调用fill_text(driver, question, q_num)
            spans = question.find_elements(By.CSS_SELECTOR, "span.textCont[contenteditable='true']")
            text_inputs = question.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
            if spans or (text_inputs and len(text_inputs) >= 1):
                self.fill_text(driver, question, q_num)
                return

            scale_items = question.find_elements(By.CSS_SELECTOR, ".scale-ul li, .scale-item")
            if scale_items:
                self.fill_scale(driver, question, q_num)
                return

            matrix_rows = question.find_elements(By.CSS_SELECTOR, ".matrix tr, .matrix-row")
            if matrix_rows:
                self.fill_matrix(driver, question, q_num)
                return

            dropdowns = question.find_elements(By.CSS_SELECTOR, "select")
            if dropdowns:
                self.fill_droplist(driver, question, q_num)
                return

            clickable = question.find_elements(By.CSS_SELECTOR, "li, label, button")
            for elem in clickable:
                if elem.is_displayed() and elem.is_enabled():
                    try:
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                              elem)
                        elem.click()
                        self.random_delay(*self.config.get("per_question_delay", (1.0, 3.0)))
                        return
                    except Exception:
                        continue

            text_inputs = question.find_elements(By.CSS_SELECTOR, "input, textarea")
            for inp in text_inputs:
                if inp.is_displayed() and not inp.get_attribute("value"):
                    try:
                        inp.send_keys("自动填写内容")
                        self.random_delay(*self.config.get("per_question_delay", (1.0, 3.0)))
                        return
                    except Exception:
                        continue

            import logging
            logging.warning(f"无法自动检测题目 {q_num} 的类型，尝试通用方法")
        except Exception as e:
            import logging
            logging.error(f"自动检测题目类型时出错: {str(e)}")

    def fill_text(self, driver, question, q_num):
        """填空题/多项填空题自动填写 - 优化日志版"""
        import random
        import time
        import logging
        from selenium.webdriver.common.by import By

        q_key = str(q_num)
        # 获取所有可填写的控件
        editable_spans = question.find_elements(By.CSS_SELECTOR, "span.textCont[contenteditable='true']")
        visible_inputs = [el for el in question.find_elements(By.CSS_SELECTOR, "input[type='text']") if
                          el.is_displayed()]
        visible_textareas = [el for el in question.find_elements(By.CSS_SELECTOR, "textarea") if el.is_displayed()]
        all_fields = editable_spans + visible_inputs + visible_textareas
        if not all_fields:
            all_fields = [el for el in question.find_elements(By.CSS_SELECTOR, "input") if el.is_displayed()]

        if not all_fields:
            logging.debug(f"题目 {q_num} 未找到可填写的输入框")
            return

        # ==== AI自动答题优先 ====
        answers = []
        ai_enabled = self.config.get("ai_fill_enabled", False)
        api_key = self.config.get("openai_api_key", "")
        prompt_template = self.config.get("ai_prompt_template", "请用简洁、自然的中文回答：{question}")
        question_text = self.config.get("question_texts", {}).get(q_key, "")

        if ai_enabled and api_key and question_text:
            try:
                service = self.config.get("ai_service", "质谱清言")
                if service == "OpenAI":
                    # 使用OpenAI接口
                    ai_answer = self.ai_generate_answer(question_text, api_key, prompt_template)
                else:
                    # 使用质谱清言接口
                    ai_answer = self.zhipu_generate_answer(question_text, api_key, prompt_template)
                answers = [ai_answer] * len(all_fields)
                logging.info(f"使用{service}生成答案: {ai_answer[:20]}...")
            except Exception as e:
                logging.warning(f"AI答题失败: {str(e)}")
                answers = [self.get_identity_answer("", question_text)] * len(all_fields)

        elif q_key in self.config.get("multiple_texts", {}):
            ans_lists = self.config["multiple_texts"][q_key]
            for i in range(len(all_fields)):
                if i < len(ans_lists) and ans_lists[i]:
                    chosen = random.choice(ans_lists[i])
                    answers.append(chosen)
                else:
                    answers.append("自动填写内容")
        elif q_key in self.config.get("texts", {}):
            ans_list = self.config["texts"][q_key]
            for i in range(len(all_fields)):
                chosen = random.choice(ans_list) if ans_list else "自动填写内容"
                answers.append(chosen)
        else:
            answers = ["自动填写内容"] * len(all_fields)

        # ==== 填写答案 ====
        for idx, field in enumerate(all_fields):
            val = (field.tag_name == "span" and field.text.strip()) or (field.get_attribute("value"))
            if val:
                continue  # 已有内容不覆盖

            answer = answers[idx] if idx < len(answers) else "自动填写内容"

            if field.tag_name == "span" and field.get_attribute("contenteditable") == "true":
                try:
                    driver.execute_script("arguments[0].innerText = '';", field)
                    for ch in answer:
                        field.send_keys(ch)
                        time.sleep(random.uniform(0.01, 0.03))
                except Exception:
                    driver.execute_script("arguments[0].innerText = arguments[1];", field, answer)
                try:
                    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", field)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", field)
                except Exception:
                    pass
            else:
                try:
                    field.clear()
                except Exception:
                    pass
                try:
                    for ch in answer:
                        field.send_keys(ch)
                        time.sleep(random.uniform(0.01, 0.03))
                except Exception:
                    driver.execute_script("arguments[0].value = arguments[1];", field, answer)
                try:
                    driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", field)
                    driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", field)
                except Exception:
                    pass

        self.random_delay(*self.config.get("per_question_delay", (1.0, 3.0)))
        logging.info(f"已填写题目 {q_num}")

    def repair_required_questions(self, driver):
        """
        检查所有必答项，自动补全未填写项，包括“其他”多选题下的必答填空。
        """
        try:
            questions = driver.find_elements(By.CSS_SELECTOR, ".div_question, .field, .question")
            for q in questions:
                is_required = False
                # 判断必答标记
                try:
                    if q.find_element(By.CSS_SELECTOR, ".required, .star, .necessary, .wjxnecessary"):
                        is_required = True
                except:
                    if "必答" in q.text or q.get_attribute("data-required") == "1":
                        is_required = True
                if not is_required:
                    continue

                all_inputs = q.find_elements(By.CSS_SELECTOR, "input, textarea, select")
                any_filled = False
                for inp in all_inputs:
                    typ = inp.get_attribute("type")
                    if typ in ("checkbox", "radio"):
                        if inp.is_selected():
                            any_filled = True
                            # 检查“其他”选项的填空
                            if "其他" in inp.get_attribute("value") or "other" in (inp.get_attribute("id") or ""):
                                try:
                                    other_text = q.find_element(By.CSS_SELECTOR, "input[type='text'], textarea")
                                    if not other_text.get_attribute("value"):
                                        other_text.send_keys("自动补全内容")
                                except:
                                    pass
                    elif typ in ("text", None):
                        if inp.get_attribute("value"):
                            any_filled = True
                    elif typ == "select-one":
                        if inp.get_attribute("value"):
                            any_filled = True
                # 未填写自动补全
                if not any_filled:
                    self.auto_fill_question(driver, q)
        except Exception as e:
            logging.warning(f"自动修复必答题时出错: {e}")

    def auto_fill_question(self, driver, question):
        """
        自动补全问题 - 修复版，确保多选题中的'其他'文本必填
        """
        import random
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import StaleElementReferenceException

        try:
            # 1. 单选题
            try:
                radios = question.find_elements(By.CSS_SELECTOR, "input[type='radio']")
                if radios:
                    random.choice(radios).click()
                    return
            except StaleElementReferenceException:
                pass

            # 2. 多选题
            try:
                checks = question.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
                if checks:
                    # 随机勾选一个
                    chosen = random.choice(checks)
                    try:
                        chosen.click()
                    except:
                        driver.execute_script("arguments[0].click();", chosen)

                    # 获取选项文本
                    option_labels = []
                    label_elems = question.find_elements(By.CSS_SELECTOR, "label")
                    for el in label_elems:
                        try:
                            txt = el.text.strip()
                            if not txt:
                                spans = el.find_elements(By.CSS_SELECTOR, "span")
                                if spans:
                                    txt = spans[0].text.strip()
                            option_labels.append(txt)
                        except StaleElementReferenceException:
                            option_labels.append("")

                    # 检查是否有"其他"选项被选中
                    chose_other = False
                    for idx, chk in enumerate(checks):
                        try:
                            if chk.is_selected() and idx < len(option_labels):
                                label_text = option_labels[idx]
                                if "其他" in label_text or "other" in label_text.lower():
                                    chose_other = True
                                    break
                        except:
                            continue

                    # 如果选中了"其他"选项，填写文本框
                    if chose_other:
                        # 增强定位策略
                        locator_strategies = [
                            (By.XPATH, f".//input[preceding-sibling::label[contains(., '其他')]]"),
                            (By.CSS_SELECTOR, "input[placeholder*='其他'], input[placeholder*='请填写']"),
                            (By.CLASS_NAME, "OtherText"),
                            (By.XPATH, ".//div[contains(@class, 'other')]//input"),
                            (By.CSS_SELECTOR, "input[type='text'], textarea")
                        ]

                        other_inputs = []
                        for strategy in locator_strategies:
                            try:
                                found_inputs = question.find_elements(strategy[0], strategy[1])
                                if found_inputs:
                                    other_inputs = found_inputs
                                    break
                            except:
                                continue

                        # 全局查找
                        if not other_inputs:
                            for strategy in locator_strategies:
                                try:
                                    found_inputs = driver.find_elements(strategy[0], strategy[1])
                                    if found_inputs:
                                        other_inputs = found_inputs
                                        break
                                except:
                                    continue

                        # 填写找到的第一个可见文本框
                        for inp in other_inputs:
                            try:
                                if inp.is_displayed() and not inp.get_attribute("value"):
                                    try:
                                        inp.send_keys("自动补全内容")
                                        logging.info("成功补全'其他'文本框")
                                        break
                                    except:
                                        try:
                                            driver.execute_script("arguments[0].value = '自动补全内容';", inp)
                                            logging.info("通过JS补全'其他'文本框")
                                            break
                                        except:
                                            pass
                            except:
                                continue
                    return
            except StaleElementReferenceException:
                pass

            # 3. 填空题
            try:
                texts = question.find_elements(By.CSS_SELECTOR, "input[type='text'], textarea")
                if texts:
                    for t in texts:
                        if not t.get_attribute("value") and t.is_displayed():
                            try:
                                t.send_keys("自动补全内容")
                            except:
                                try:
                                    driver.execute_script("arguments[0].value = '自动补全内容';", t)
                                except:
                                    pass
                    return
            except StaleElementReferenceException:
                pass

            # 4. 下拉框
            try:
                selects = question.find_elements(By.CSS_SELECTOR, "select")
                if selects:
                    for sel in selects:
                        options = sel.find_elements(By.TAG_NAME, "option")
                        for op in options:
                            try:
                                if op.get_attribute("value") and not op.get_attribute("disabled"):
                                    sel.send_keys(op.get_attribute("value"))
                                    break
                            except:
                                continue
                    return
            except StaleElementReferenceException:
                pass

            # 5. 最后尝试：点击任何可点击元素
            try:
                clickable_elements = question.find_elements(By.CSS_SELECTOR,
                                                            "li, label, div[onclick], span[onclick], .option")
                if clickable_elements:
                    element = random.choice(clickable_elements)
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                          element)
                    time.sleep(0.2)
                    element.click()
                    return
            except StaleElementReferenceException:
                pass

            logging.warning("无法自动补全问题")
        except Exception as e:
            logging.error(f"自动补全题目时出错: {str(e)}")

    def submit_survey(self, driver):

        import time
        import random
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException, NoSuchElementException

        # 内部工具函数
        def is_submit_success():
            """判断问卷是否已提交成功"""
            try:
                if hasattr(self, '_original_url') and driver.current_url != self._original_url:
                    return True
                page = driver.page_source.lower()
                success_texts = [
                    "感谢", "提交成功", "问卷已完成", "谢谢您的参与", "再次填写",
                    "thank", "success", "complete", "finished"
                ]
                if any(t in page for t in success_texts):
                    return True
                selectors = [
                    "div.complete", ".survey-success", ".end-page",
                    ".finish-container", ".thank-you-page"
                ]
                for sel in selectors:
                    if driver.find_elements(By.CSS_SELECTOR, sel):
                        return True
                return False
            except Exception:
                return False

        def smart_click(element):
            """多方式尝试点击元素"""
            try:
                if not element.is_displayed() or not element.is_enabled():
                    return False
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'auto', block: 'center'});", element
                )
                time.sleep(0.2)
                try:
                    element.click()
                    return True
                except Exception:
                    driver.execute_script("arguments[0].click();", element)
                    return True
            except Exception:
                return False

        def find_and_click_submit():
            """智能查找并点击提交按钮"""
            selectors = [
                "#ctlNext", "#submit_button", ".submit-btn", ".submitbutton",
                "a[id*='submit']", "button[type='submit']", "input[type='submit']",
                "div.submit", ".btn-submit", ".btn-success", "#submit_btn",
                "#next_button", ".next-button"
            ]
            for sel in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, sel)
                    for elem in elements:
                        if smart_click(elem):
                            return True
                except Exception:
                    continue
            # 尝试文本查找
            texts = ["提交", "submit", "完成", "交卷", "提交问卷", "确定"]
            for txt in texts:
                try:
                    elements = driver.find_elements(By.XPATH, f"//*[contains(text(),'{txt}')]")
                    for elem in elements:
                        if smart_click(elem):
                            return True
                except Exception:
                    continue
            return False

        def solve_slider():
            """全自动滑块验证码处理"""
            try:
                # 多种滑块兼容
                slider = None
                selectors = [
                    "#nc_1_n1z",
                    "//div[contains(@class,'nc_slider_btn')]",
                    ".yidun_slider",
                    ".slider-btn"
                ]
                for sel in selectors:
                    try:
                        if sel.startswith("//"):
                            slider = driver.find_element(By.XPATH, sel)
                        else:
                            slider = driver.find_element(By.CSS_SELECTOR, sel)
                        if slider:
                            break
                    except NoSuchElementException:
                        continue
                if not slider:
                    return False

                bar = slider.find_element(By.XPATH, "../..")
                bar_width = bar.size['width']
                slider_width = slider.size['width']
                distance = bar_width - slider_width - random.randint(6, 12)

                def get_tracks(total, duration=1.7):
                    """生成拟人化轨迹"""
                    tracks = []
                    v = 0
                    t = 0.18
                    current = 0
                    mid = total * 0.8
                    while current < total:
                        if current < mid:
                            a = random.uniform(2, 4)
                        else:
                            a = -random.uniform(3, 5)
                        v0 = v
                        v = v0 + a * t
                        move = v0 * t + 0.5 * a * t * t
                        move = int(max(1, round(move)))
                        if current + move > total:
                            move = total - current
                        tracks.append(move)
                        current += move
                    for _ in range(3):
                        tracks.append(-random.randint(1, 2))
                        tracks.append(random.randint(1, 2))
                    return tracks

                tracks = get_tracks(distance)
                action = ActionChains(driver)
                action.click_and_hold(slider).perform()
                for x in tracks:
                    y = random.randint(-2, 2)
                    action.move_by_offset(xoffset=x, yoffset=y).perform()
                    time.sleep(random.uniform(0.012, 0.034))
                for _ in range(2):
                    action.move_by_offset(1, 0).perform()
                    time.sleep(0.09)
                    action.move_by_offset(-1, 0).perform()
                    time.sleep(0.09)
                action.release().perform()
                time.sleep(1.2)
                return True
            except Exception as e:
                print(f"[滑块拖动失败] {e}")
                return False

        def handle_dialogs():
            """自动关闭常见弹窗"""
            dialog_selectors = [
                '//*[@id="layui-layer1"]/div[3]/a',
                '//*[@id="SM_BTN_1"]',
                "//a[contains(text(),'确定')]",
                "//button[contains(text(),'好的')]"
            ]
            for sel in dialog_selectors:
                try:
                    elements = driver.find_elements(By.XPATH, sel)
                    for elem in elements:
                        if elem.is_displayed():
                            smart_click(elem)
                            time.sleep(0.3)
                except Exception:
                    continue

        def repair_and_submit():
            """自动修复必填和验证码相关问题"""
            try:
                hints = driver.find_elements(
                    By.XPATH, "//*[contains(text(),'必答题') or contains(text(),'请填写')]"
                )
                if hints:
                    self.repair_required_questions(driver)
                    return True
                if "验证码" in driver.page_source or "请完成验证" in driver.page_source:
                    for _ in range(3):
                        if solve_slider():
                            break
                        time.sleep(1)
                    return True
                return False
            except Exception:
                return False

        # 主流程
        try:
            self._original_url = driver.current_url
        except Exception:
            self._original_url = None

        max_attempts = 8
        for attempt in range(max_attempts):
            try:
                if not find_and_click_submit():
                    print(f"第{attempt + 1}次尝试：未找到可用的提交按钮")
                    continue
                time.sleep(1.1)
                handle_dialogs()
                time.sleep(0.8)
                for _ in range(3):  # 验证码最多尝试3次
                    if solve_slider():
                        break
                    time.sleep(1)
                for _ in range(10):
                    if is_submit_success():
                        print("问卷提交成功！")
                        return True
                    time.sleep(1)
                if repair_and_submit():
                    continue
                print(f"第{attempt + 1}次提交未成功，刷新重试...")
                driver.refresh()
                time.sleep(2)
            except Exception as e:
                print(f"提交过程异常: {e}")
                driver.refresh()
                time.sleep(2)
        print("达到最大重试次数，提交失败")
        return False

    def fill_droplist(self, driver, question, q_num):
        """
        增强版下拉框题目填写方法 - 支持原生select和自定义下拉框
        """
        import random
        import time
        import logging
        import datetime
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import Select
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.common.exceptions import (NoSuchElementException,
                                                ElementNotInteractableException,
                                                StaleElementReferenceException)

        logging.info(f"开始处理下拉框题目 {q_num}")
        try:
            q_key = str(q_num)
            # 获取配置的概率
            probs = self.config.get("droplist_prob", {}).get(q_key, None)

            # 尝试定位原生select元素
            try:
                select_elem = question.find_element(By.CSS_SELECTOR, "select")
                logging.info(f"找到原生select元素")

                # 创建Select对象
                select = Select(select_elem)
                options = select.options

                # 过滤无效选项
                valid_options = []
                for idx, op in enumerate(options):
                    try:
                        # 跳过禁用项和"请选择"选项
                        if op.get_attribute("disabled") or op.text.strip() in ["请选择", "Select", "--请选择--"]:
                            continue
                        # 如果value为空但文本有效，也算有效选项
                        if not op.get_attribute("value") and op.text.strip():
                            valid_options.append((idx, op))
                        elif op.get_attribute("value") and op.get_attribute("value").strip():
                            valid_options.append((idx, op))
                    except StaleElementReferenceException:
                        continue

                if not valid_options:
                    logging.warning(f"题目 {q_num} 未找到有效下拉选项")
                    return

                logging.info(f"题目 {q_num} 有 {len(valid_options)} 个有效选项")

                # 处理概率配置
                if probs and isinstance(probs, list) and len(probs) == len(valid_options):
                    try:
                        weights = [float(p) for p in probs]
                        total = sum(weights)
                        if total > 0:
                            weights = [w / total for w in weights]
                            selected_idx = np.random.choice(range(len(valid_options)), p=weights)
                            logging.info(f"使用概率选择: 索引 {selected_idx}")
                        else:
                            selected_idx = random.randint(0, len(valid_options) - 1)
                            logging.info(f"概率总和为零，随机选择: 索引 {selected_idx}")
                    except Exception as e:
                        logging.warning(f"概率处理失败，使用随机选择: {str(e)}")
                        selected_idx = random.randint(0, len(valid_options) - 1)
                else:
                    selected_idx = random.randint(0, len(valid_options) - 1)
                    logging.info(f"无有效概率配置，随机选择: 索引 {selected_idx}")

                # 获取选中的选项
                idx, op = valid_options[selected_idx]
                option_text = op.text.strip()
                option_value = op.get_attribute("value") or option_text

                # 使用Select类进行选择
                try:
                    logging.info(f"尝试通过索引选择: {idx}")
                    select.select_by_index(idx)
                    logging.info(f"选择选项: {option_text}")
                except Exception as e:
                    try:
                        logging.info(f"索引选择失败，尝试按值选择: {option_value}")
                        select.select_by_value(option_value)
                    except:
                        try:
                            logging.info(f"值选择失败，尝试按文本选择: {option_text}")
                            select.select_by_visible_text(option_text)
                        except Exception as e2:
                            logging.error(f"所有选择方式失败: {str(e2)}")
                            # 使用JS直接设置值
                            js = f"""
                            var select = arguments[0];
                            select.selectedIndex = {idx};
                            var event = new Event('change', {{ bubbles: true }});
                            select.dispatchEvent(event);
                            """
                            driver.execute_script(js, select_elem)
                            logging.info("使用JS设置下拉框值")

                self.random_delay(*self.config.get("per_question_delay", (1.0, 3.0)))
                return
            except NoSuchElementException:
                logging.info("未找到原生select元素，尝试自定义下拉框")
            except Exception as e:
                logging.warning(f"原生select处理失败: {str(e)}")

            # 处理自定义下拉框
            try:
                # 查找自定义下拉框触发器
                triggers = question.find_elements(By.CSS_SELECTOR,
                                                  ".custom-select, .dropdown-toggle, .select-box, .ant-select-selection")
                if not triggers:
                    logging.info("未找到自定义下拉框触发器")
                    return

                trigger = triggers[0]
                logging.info(f"找到自定义下拉框触发器: {trigger.get_attribute('outerHTML')[:100]}")

                # 滚动到元素并点击展开
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", trigger)
                time.sleep(0.3)

                # 确保元素可见
                if not trigger.is_displayed():
                    logging.info("触发器不可见，尝试滚动页面")
                    actions = ActionChains(driver)
                    actions.move_to_element(trigger).perform()
                    time.sleep(0.5)

                try:
                    trigger.click()
                    logging.info("点击展开下拉框")
                except ElementNotInteractableException:
                    logging.info("点击失败，使用JS点击")
                    driver.execute_script("arguments[0].click();", trigger)

                time.sleep(0.8)  # 等待下拉框展开

                # 获取所有选项 - 使用更广泛的CSS选择器
                option_selectors = [
                    ".option",
                    ".dropdown-item",
                    ".select-item",
                    ".ant-select-dropdown-menu-item",
                    ".menu-item",
                    ".item",
                    "li"
                ]

                option_elems = []
                for selector in option_selectors:
                    try:
                        found = driver.find_elements(By.CSS_SELECTOR, selector)
                        if found:
                            option_elems = found
                            logging.info(f"使用选择器 '{selector}' 找到 {len(option_elems)} 个选项")
                            break
                    except:
                        continue

                if not option_elems:
                    logging.warning("未找到下拉选项")
                    return

                # 过滤无效选项
                valid_options = []
                for op in option_elems:
                    try:
                        if not op.is_displayed():
                            continue
                        text = op.text.strip()
                        if not text or "请选择" in text:
                            continue
                        if op.get_attribute("disabled") or op.get_attribute("aria-disabled") == "true":
                            continue
                        valid_options.append(op)
                    except StaleElementReferenceException:
                        continue

                if not valid_options:
                    logging.warning("未找到有效选项")
                    return

                logging.info(f"找到 {len(valid_options)} 个有效选项")

                # 处理概率配置
                if probs and isinstance(probs, list) and len(probs) == len(valid_options):
                    try:
                        weights = [float(p) for p in probs]
                        total = sum(weights)
                        if total > 0:
                            weights = [w / total for w in weights]
                            selected = np.random.choice(valid_options, p=weights)
                        else:
                            selected = random.choice(valid_options)
                    except Exception as e:
                        logging.warning(f"概率处理失败，使用随机选择: {str(e)}")
                        selected = random.choice(valid_options)
                else:
                    selected = random.choice(valid_options)

                # 点击选中
                try:
                    logging.info(f"尝试点击选项: {selected.text[:20]}...")
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                          selected)
                    time.sleep(0.2)
                    selected.click()
                    time.sleep(0.5)
                except Exception as e:
                    logging.warning(f"点击选项失败: {str(e)}，使用JS点击")
                    driver.execute_script("arguments[0].click();", selected)

                self.random_delay(*self.config.get("per_question_delay", (1.0, 3.0)))
                return
            except Exception as e:
                logging.error(f"自定义下拉框处理失败: {str(e)}")

            # 最终尝试：直接使用JavaScript设置值
            try:
                logging.info("尝试最终方案：JS设置值")
                # 获取选项文本列表
                option_texts = self.config.get("option_texts", {}).get(q_key, [])
                if not option_texts:
                    logging.warning("无选项文本配置")
                    return

                # 随机选择一个选项
                selected_text = random.choice(option_texts)
                logging.info(f"随机选择文本: {selected_text}")

                # 查找所有select元素
                selects = driver.find_elements(By.CSS_SELECTOR, "select")
                if not selects:
                    logging.info("无select元素")
                    return

                for sel in selects:
                    # 使用JS设置值
                    js = f"""
                    var select = arguments[0];
                    var found = false;
                    for (var i = 0; i < select.options.length; i++) {{
                        if (select.options[i].text === '{selected_text}') {{
                            select.selectedIndex = i;
                            found = true;
                            break;
                        }}
                    }}
                    if (!found) {{
                        for (var i = 0; i < select.options.length; i++) {{
                            if (select.options[i].text.includes('{selected_text}')) {{
                                select.selectedIndex = i;
                                found = true;
                                break;
                            }}
                        }}
                    }}
                    if (found) {{
                        var event = new Event('change', {{ bubbles: true }});
                        select.dispatchEvent(event);
                    }}
                    """
                    driver.execute_script(js, sel)
                    logging.info("执行JS设置下拉框值")

                self.random_delay(*self.config.get("per_question_delay", (1.0, 3.0)))
            except Exception as e:
                logging.error(f"最终JS设置下拉框值失败: {str(e)}")

        except Exception as e:
            logging.error(f"填写下拉框题 {q_num} 时出错: {str(e)}")
            # 截图保存当前页面状态
            try:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                screenshot_path = f"error_droplist_q{q_num}_{timestamp}.png"
                driver.save_screenshot(screenshot_path)
                logging.info(f"已保存错误截图: {screenshot_path}")
            except:
                logging.error("无法保存截图")

    def verify_submission(self, driver):
        """多维度验证提交是否成功"""
        # 1. 检查URL特征
        current_url = driver.current_url
        if any(keyword in current_url for keyword in ["complete", "success", "finish", "end", "thank"]):
            return True

        # 2. 检查页面关键元素
        success_selectors = [
            "div.complete",
            "div.survey-complete",
            "div.text-success",
            "img[src*='success']",
            ".survey-success",
            ".end-page",
            ".endtext",
            ".finish-container",
            ".thank-you-page"
        ]

        for selector in success_selectors:
            try:
                if driver.find_element(By.CSS_SELECTOR, selector):
                    return True
            except:
                continue

        # 3. 检查关键文本
        success_phrases = [
            "提交成功", "问卷已完成", "感谢参与",
            "success", "completed", "thank you",
            "问卷提交成功", "提交成功", "已完成",
            "感谢您的参与", "提交完毕", "finish",
            "问卷结束", "谢谢您的参与"
        ]

        page_text = driver.page_source.lower()
        if any(phrase.lower() in page_text for phrase in success_phrases):
            return True

        # 4. 检查错误消息缺失
        error_phrases = [
            "验证码", "错误", "失败", "未提交",
            "error", "fail", "captcha", "未完成",
            "请检查", "不正确", "需要验证"
        ]

        if not any(phrase in page_text for phrase in error_phrases):
            return True

        return False

    # ================== 增强验证码处理 ==================
    def handle_captcha(self, driver):
        """增强的验证码处理"""
        try:
            # 检查多种验证码形式
            captcha_selectors = [
                "div.captcha-container",
                "div.geetest_panel",
                "iframe[src*='captcha']",
                "div#captcha",
                ".geetest_holder",
                ".nc-container",
                ".captcha-modal"
            ]

            # 检查验证码是否存在
            for selector in captcha_selectors:
                try:
                    captcha = driver.find_element(By.CSS_SELECTOR, selector)
                    if captcha.is_displayed():
                        logging.warning("检测到验证码，尝试自动处理")
                        self.pause_for_captcha()
                        return True
                except:
                    continue

            # 检查页面是否有验证码文本提示
            captcha_phrases = ["验证码", "captcha", "验证", "请完成验证"]
            page_text = driver.page_source.lower()
            if any(phrase in page_text for phrase in captcha_phrases):
                logging.warning("页面检测到验证码提示，暂停程序")
                self.pause_for_captcha()
                return True

        except Exception as e:
            logging.error(f"验证码处理出错: {str(e)}")

        return False

    def pause_for_captcha(self):
        """暂停程序并提醒用户处理验证码"""
        self.paused = True
        self.pause_btn.config(text="继续")

        # 创建提醒窗口
        alert = tk.Toplevel(self.root)
        alert.title("需要验证码")
        alert.geometry("400x200")
        alert.resizable(False, False)

        msg = ttk.Label(alert, text="检测到验证码，请手动处理并点击继续", font=("Arial", 12))
        msg.pack(pady=20)

        # 添加倒计时
        countdown_var = tk.StringVar(value="窗口将在 60 秒后自动继续")
        countdown_label = ttk.Label(alert, textvariable=countdown_var, font=("Arial", 10))
        countdown_label.pack(pady=10)

        def resume_after_timeout(seconds=60):
            if seconds > 0:
                countdown_var.set(f"窗口将在 {seconds} 秒后自动继续")
                alert.after(1000, lambda: resume_after_timeout(seconds - 1))
            else:
                self.paused = False
                self.pause_btn.config(text="暂停")
                alert.destroy()

        # 手动继续按钮
        continue_btn = ttk.Button(alert, text="我已处理验证码",
                                  command=lambda: [alert.destroy(), self.toggle_pause()])
        continue_btn.pack(pady=10)

        # 开始倒计时
        resume_after_timeout()

        # 置顶窗口
        alert.attributes('-topmost', True)
        alert.update()
        alert.attributes('-topmost', False)

    def create_multiple_text_settings(self, frame):
        """
        多项填空题配置tab页——每空一个entry，支持逗号分隔多个可选答案。
        保存时遍历 self.multiple_text_entries，按顺序写入 self.config["multiple_texts"]。
        """
        padx, pady = 4, 2
        desc_frame = ttk.LabelFrame(frame, text="多项填空配置说明")
        desc_frame.pack(fill=tk.X, padx=padx, pady=pady)
        ttk.Label(desc_frame, text="• 每空的所有可选答案用逗号分隔，自动随机选一个填写", font=("Arial", 9)).pack(
            anchor=tk.W)

        table_frame = ttk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        headers = ["题号", "题目预览", "每空答案配置"]
        for col, header in enumerate(headers):
            ttk.Label(table_frame, text=header, font=("Arial", 9, "bold")).grid(row=0, column=col, padx=padx, pady=pady,
                                                                                sticky=tk.W)

        self.multiple_text_entries = []  # 清空，防止重复累积

        # 遍历所有多项填空题
        for row_idx, (q_num, answers_list) in enumerate(self.config.get("multiple_texts", {}).items(), start=1):
            base_row = row_idx * 2
            q_text = self.config.get("question_texts", {}).get(q_num, f"多项填空 {q_num}")
        空数 = len(answers_list)
        ttk.Label(table_frame, text=f"第{q_num}题", font=("Arial", 10)).grid(row=base_row, column=0, padx=padx,
                                                                             pady=pady, sticky=tk.NW)
        preview_text = q_text
        ttk.Label(table_frame, text=preview_text, width=20, anchor="w", wraplength=300).grid(row=base_row, column=1,
                                                                                             padx=padx, pady=pady,
                                                                                             sticky=tk.NW)
        answer_line = ttk.Frame(table_frame)
        answer_line.grid(row=base_row, column=2, padx=padx, pady=pady, sticky=tk.W)
        entry_row = []
        for i in range(空数):
            entry = ttk.Entry(answer_line, width=18)
            # 预填已有内容
            answer_str = ", ".join(answers_list[i]) if i < len(answers_list) else ""
            entry.insert(0, answer_str)
            entry.pack(side=tk.LEFT, padx=(0, 2))
            entry_row.append(entry)
        self.multiple_text_entries.append(entry_row)
        # 重置按钮
        reset_btn = ttk.Button(answer_line, text="重置", width=6,
                               command=lambda e=entry_row: [ent.delete(0, tk.END) or ent.insert(0, "示例答案") for ent
                                                            in e])
        reset_btn.pack(side=tk.LEFT, padx=(6, 0))
        ttk.Separator(table_frame, orient='horizontal').grid(
            row=base_row + 1, column=0, columnspan=3, sticky='ew', pady=10
        )

    def fill_single(self, driver, question, q_num):
        """
        单选题自动填写，兼容新版问卷星自定义UI，优先点击label或外层div，保证前端能识别选中。
        并自动填写被选中选项关联的弹出文本框（AI优先）。
        """
        import random, time
        from selenium.webdriver.common.by import By
        import logging

        # 1. 先找所有可见input[type=radio]
        radios = question.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        if not radios:
            return

        q_key = str(q_num)
        probs = self.config.get("single_prob", {}).get(q_key, -1)

        # 2. 确定要选哪个
        if probs == -1:
            selected_idx = random.randint(0, len(radios) - 1)
        elif isinstance(probs, list):
            probs = probs[:len(radios)] if len(probs) > len(radios) else probs + [0] * (len(radios) - len(probs))
            total = sum(probs)
            if total > 0:
                norm_probs = [p / total for p in probs]
                selected_idx = int(np.random.choice(range(len(radios)), p=norm_probs))
            else:
                selected_idx = random.randint(0, len(radios) - 1)
        else:
            selected_idx = random.randint(0, len(radios) - 1)

        selected_radio = radios[selected_idx]

        # 3. 优先找label[for=id]，否则点父节点，最后才点input本身
        input_id = selected_radio.get_attribute("id")
        label = None
        if input_id:
            try:
                label = question.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
            except:
                label = None
        if not label:
            try:
                label = selected_radio.find_element(By.XPATH, "./..")
            except:
                label = None
        if not label:
            try:
                label = selected_radio.find_element(By.XPATH, "../..")
            except:
                label = None

        clicked = False
        for elem in [label, selected_radio]:
            if elem is not None:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", elem)
                    if elem.is_displayed() and elem.is_enabled():
                        elem.click()
                        clicked = True
                        break
                except Exception:
                    continue

        # 强制触发change/input事件
        try:
            driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", selected_radio)
            driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));", selected_radio)
        except Exception:
            pass

        # 检查input是否变为选中，否则再强制用JS选中并触发事件
        try:
            is_checked = selected_radio.is_selected() or selected_radio.get_attribute("checked")
            if not is_checked:
                driver.execute_script("arguments[0].checked = true;", selected_radio)
                driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));",
                                      selected_radio)
                driver.execute_script("arguments[0].dispatchEvent(new Event('change', { bubbles: true }));",
                                      selected_radio)
        except Exception:
            pass

        # ==== 新增：点选后自动填写该题下所有空白文本框（AI优先） ====
        time.sleep(0.5)  # 等待弹框动画
        self.fill_associated_textbox(
            driver, question, selected_radio,
            ai_enabled=self.config.get("ai_fill_enabled", False),
            ai_api_key=self.config.get("openai_api_key", ""),
            ai_prompt_template=self.config.get("ai_prompt_template", "请用简洁、自然的中文回答：{question}"),
            question_text=self.config.get("question_texts", {}).get(str(q_num), "")
        )

        self.random_delay(*self.config.get("per_question_delay", (1.0, 3.0)))

    def fill_multiple(self, driver, question, q_num):
        """
        问卷星多选题自动填写（增强版）：优先点击label/div，自动填写所有被选中选项关联的文本框（不仅仅是“其他”），
        保证最少/最多选择数严格生效。AI自动填补充文本。
        """
        import random
        import time
        from selenium.webdriver.common.by import By

        # 1. 查找所有checkbox选项
        checkboxes = question.find_elements(By.CSS_SELECTOR, "input[type='checkbox']")
        option_labels = []
        for box in checkboxes:
            label_text = ""
            try:
                label_for = box.get_attribute("id")
                if label_for:
                    label = question.find_element(By.CSS_SELECTOR, f"label[for='{label_for}']")
                    label_text = label.text.strip()
                if not label_text:
                    label_text = box.find_element(By.XPATH, "./following-sibling::*[1]").text.strip()
            except:
                pass
            if not label_text:
                try:
                    label_text = box.find_element(By.XPATH, "../..").text.strip()
                except:
                    pass
            option_labels.append(label_text or "未知")

        if not checkboxes:
            import logging
            logging.warning(f"多选题{q_num}未找到选项，跳过")
            return

        # 2. 读取配置并修正概率长度
        q_key = str(q_num)
        conf = self.config.get("multiple_prob", {}).get(q_key, {"prob": [50] * len(checkboxes), "min_selection": 1,
                                                                "max_selection": len(checkboxes)})
        probs = conf.get("prob", [50] * len(checkboxes))
        min_selection = conf.get("min_selection", 1)
        max_selection = conf.get("max_selection", len(checkboxes))
        if max_selection > len(checkboxes): max_selection = len(checkboxes)
        if min_selection > max_selection: min_selection = max_selection
        # 修正概率长度
        probs = probs[:len(checkboxes)] if len(probs) > len(checkboxes) else probs + [50] * (
                len(checkboxes) - len(probs))

        # 3. 选项选择逻辑(严格保证最少和最多选择数)
        must_indices = [i for i, prob in enumerate(probs) if prob >= 100]
        selected = set(must_indices)
        for i, prob in enumerate(probs):
            if i not in selected and random.random() * 100 < prob:
                selected.add(i)
        # 补足最少选择数
        while len(selected) < min_selection:
            left = [i for i in range(len(checkboxes)) if i not in selected]
            if not left:
                break
            selected.add(random.choice(left))
        # 裁剪到最大数
        while len(selected) > max_selection:
            removable = [i for i in selected if i not in must_indices]
            if not removable:
                break
            selected.remove(random.choice(removable))

        # 4. 勾选选项（优先点击label/div，避免element not interactable）
        for idx in selected:
            try:
                if idx >= len(checkboxes):
                    continue
                input_box = checkboxes[idx]
                label = None
                input_id = input_box.get_attribute("id")
                # 1) label[for=id]
                if input_id:
                    try:
                        label = question.find_element(By.CSS_SELECTOR, f"label[for='{input_id}']")
                    except:
                        label = None
                # 2) 兄弟span
                if not label:
                    try:
                        label = input_box.find_element(By.XPATH, "./following-sibling::*[1]")
                    except:
                        label = None
                # 3) 父div（如.ui-checkbox、option等）
                if not label:
                    try:
                        label = input_box.find_element(By.XPATH, "../..")
                    except:
                        label = None

                clicked = False
                for elem in [label, input_box]:
                    if elem is not None:
                        try:
                            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                                  elem)
                            if elem.is_displayed() and elem.is_enabled():
                                elem.click()
                                clicked = True
                                break
                        except Exception:
                            continue
                if not clicked:
                    try:
                        driver.execute_script("arguments[0].click();", input_box)
                        clicked = True
                    except Exception:
                        pass
                if not clicked:
                    import logging
                    logging.warning(f"多选题第{q_num}题第{idx + 1}选项无法点击，已跳过")
                    continue

                # ==== 自动填写被选中选项下方的所有文本框（AI优先） ====
                self.fill_associated_textbox(
                    driver, question, input_box,
                    ai_enabled=self.config.get("ai_fill_enabled", False),
                    ai_api_key=self.config.get("openai_api_key", ""),
                    ai_prompt_template=self.config.get("ai_prompt_template", "请用简洁、自然的中文回答：{question}"),
                    question_text=self.config.get("question_texts", {}).get(str(q_num), "")
                )
            except Exception as e:
                import logging
                logging.warning(f"选择选项时出错: {str(e)}")
                continue

        self.random_delay(*self.config.get("per_question_delay", (1.0, 3.0)))

    def fill_matrix(self, driver, question, q_num):
        """填写矩阵题"""
        try:
            rows = question.find_elements(By.CSS_SELECTOR, f"#divRefTab{q_num} tbody tr")
            if not rows:
                return

            q_key = str(q_num)
            probs = self.config["matrix_prob"].get(q_num, -1)

            for i, row in enumerate(rows[1:], 1):  # 跳过表头行
                cols = row.find_elements(By.CSS_SELECTOR, "td")
                if not cols:
                    continue

                if probs == -1:  # 随机选择
                    selected_col = random.randint(1, len(cols) - 1)
                elif isinstance(probs, list):  # 按概率选择
                    # 确保概率列表长度匹配
                    col_probs = probs[:len(cols) - 1] if len(probs) > len(cols) - 1 else probs + [0] * (
                            len(cols) - 1 - len(probs))
                    # 归一化概率
                    total = sum(col_probs)
                    if total > 0:
                        col_probs = [p / total for p in col_probs]
                        selected_col = np.random.choice(range(1, len(cols)), p=col_probs)
                    else:
                        selected_col = random.randint(1, len(cols) - 1)
                else:  # 默认随机
                    selected_col = random.randint(1, len(cols) - 1)

                try:
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                          cols[selected_col])
                    time.sleep(0.1)
                    cols[selected_col].click()
                except:
                    # 使用JavaScript点击
                    driver.execute_script("arguments[0].click();", cols[selected_col])

                self.random_delay(0.1, 0.3)  # 每行选择后短暂延迟

            self.random_delay(*self.config["per_question_delay"])
        except Exception as e:
            logging.error(f"填写矩阵题 {q_num} 时出错: {str(e)}")

    def fill_scale(self, driver, question, q_num):
        """填写量表题"""
        try:
            options = question.find_elements(By.CSS_SELECTOR, f"#div{q_num} .scale-ul li")
            if not options:
                return

            q_key = str(q_num)
            probs = self.config["scale_prob"].get(q_key, [1] * len(options))

            # 确保概率列表长度匹配
            probs = probs[:len(options)] if len(probs) > len(options) else probs + [1] * (len(options) - len(probs))

            # 归一化概率
            total = sum(probs)
            if total > 0:
                probs = [p / total for p in probs]
                selected = np.random.choice(options, p=probs)
            else:
                selected = random.choice(options)

            try:
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", selected)
                time.sleep(0.1)
                selected.click()
            except:
                driver.execute_script("arguments[0].click();", selected)

            self.random_delay(*self.config["per_question_delay"])
        except Exception as e:
            logging.error(f"填写量表题 {q_num} 时出错: {str(e)}")

    def fill_reorder(self, driver, question, q_num):
        """
        问卷星排序题专用：只点击一轮，每个li只点一次，顺序随机，绝不补点。
        选项查找范围更广，未找到时输出结构，提升成功率。
        """
        import random
        import time
        try:
            lis = question.find_elements(
                By.CSS_SELECTOR,
                '.sort-ul li, .sortable li, .wjx-sortable li, .ui-sortable li, .sort-container li, ul li'
            )
            lis = [li for li in lis if li.is_displayed() and li.is_enabled()]
            if not lis:
                import logging
                logging.warning(f"排序题 {q_num} 未找到选项，结构为: {question.get_attribute('outerHTML')}")
                return
            idxs = list(range(len(lis)))
            random.shuffle(idxs)
            for idx in idxs:
                try:
                    lis[idx].click()
                    time.sleep(0.3)
                except Exception as e:
                    try:
                        driver.execute_script("arguments[0].click();", lis[idx])
                    except Exception:
                        import logging
                        logging.warning(f"排序题 {q_num} 第{idx + 1}项点击失败: {e}")
            # 只做一轮，绝不补点
            self.random_delay(*self.config.get("per_question_delay", (1.0, 3.0)))
        except Exception as e:
            import logging
            logging.error(f"填写排序题 {q_num} 时出错: {str(e)}")



    # 调用方法示例（比如在auto_detect_question_type或fill_text内）：
    # 假设你判断到是多项填空题型(q_type == "2")，这样调用：
    # self.fill_multiple_text(driver, question, q_num)

    def bind_mousewheel_to_scrollbar(self, canvas):
        """将鼠标滚轮事件绑定到指定的画布上"""

        def _on_mousewheel(event):
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        def _bind_mousewheel(event):
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.bind_all("<Button-4>", _on_mousewheel)
            canvas.bind_all("<Button-5>", _on_mousewheel)

        def _unbind_mousewheel(event):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        canvas.bind("<Enter>", _bind_mousewheel)
        canvas.bind("<Leave>", _unbind_mousewheel)

    def update_progress(self):
        """持续刷新整体进度条和状态栏"""
        import time
        while self.running:
            try:
                # 总体进度（份数进度条）
                if self.config["target_num"] > 0:
                    progress = (self.cur_num / self.config["target_num"]) * 100
                    self.progress_var.set(progress)
                status = "暂停中..." if self.paused else "运行中..."
                status += f" 完成: {self.cur_num}/{self.config['target_num']}"
                if self.cur_fail > 0:
                    status += f" 失败: {self.cur_fail}"
                self.status_var.set(status)
                # 如果份数已完成，自动停止
                if self.cur_num >= self.config["target_num"]:
                    self.stop_filling()
                    import tkinter.messagebox
                    tkinter.messagebox.showinfo("完成", "问卷填写完成！")
                    break
                # 保证界面刷新
                if hasattr(self, "root"):
                    self.root.update_idletasks()
            except Exception as e:
                import logging
                logging.error(f"更新进度时出错: {str(e)}")
            time.sleep(0.5)

    def is_filled(self, question):
        """检查问题是否已填写"""
        try:
            # 检查排序题
            if question.find_elements(By.CSS_SELECTOR,
                                      ".sort-ul, .sortable, .wjx-sortable, .ui-sortable, .sort-container"):
                return True
            # 检查 input/textarea/select
            inputs = question.find_elements(By.CSS_SELECTOR, "input, textarea, select")
            for inp in inputs:
                typ = inp.get_attribute("type")
                if typ in ("checkbox", "radio"):
                    if inp.is_selected():
                        return True
                elif typ in ("text", None):
                    if inp.get_attribute("value"):
                        return True
                elif typ == "select-one":
                    v = inp.get_attribute("value")
                    if v and v != "" and v != "请选择":
                        return True
            # 检查 contenteditable span
            spans = question.find_elements(By.CSS_SELECTOR, "span[contenteditable='true']")
            for span in spans:
                if span.text.strip():
                    return True
                try:
                    inner = driver.execute_script("return arguments[0].innerText;", span)
                    if inner and inner.strip():
                        return True
                except Exception:
                    continue
            return False
        except Exception:
            return False

    def toggle_pause(self):
        """切换暂停/继续状态"""
        self.paused = not self.paused
        if self.paused:
            self.pause_event.clear()
            self.pause_btn.config(text="继续")
            logging.info("已暂停")
            self.status_indicator.config(foreground="orange")
        else:
            self.pause_event.set()
            self.pause_btn.config(text="暂停")
            logging.info("已继续")
            self.status_indicator.config(foreground="green")

    def stop_filling(self):
        """停止填写"""
        self.running = False
        self.pause_event.set()  # 确保所有线程都能退出
        self.start_btn.config(state=tk.NORMAL, text="▶ 开始填写")
        self.pause_btn.config(state=tk.DISABLED, text="⏸ 暂停")
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("已停止")
        self.status_indicator.config(foreground="red")
        logging.info("已停止")

    def reset_defaults(self):
        """重置为默认配置"""
        result = messagebox.askyesno("确认", "确定要重置所有设置为默认值吗？")
        if result:
            self.config = DEFAULT_CONFIG.copy()
            # 全局设置
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, self.config["url"])
            self.target_entry.set(self.config["target_num"])
            self.ratio_scale.set(self.config["weixin_ratio"])
            self.ratio_var.set(f"{self.config['weixin_ratio'] * 100:.0f}%")
            self.min_duration.set(self.config["min_duration"])
            self.max_duration.set(self.config["max_duration"])
            self.min_delay.set(self.config["min_delay"])
            self.max_delay.set(self.config["max_delay"])
            self.min_q_delay.set(self.config["per_question_delay"][0])
            self.max_q_delay.set(self.config["per_question_delay"][1])
            self.min_p_delay.set(self.config["per_page_delay"][0])
            self.max_p_delay.set(self.config["per_page_delay"][1])
            self.submit_delay.set(self.config["submit_delay"])
            self.num_threads.set(self.config["num_threads"])
            self.use_ip_var.set(self.config["use_ip"])
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, self.config["ip_api"])
            self.ip_change_mode.set(self.config.get("ip_change_mode", "per_submit"))
            self.ip_change_batch.set(self.config.get("ip_change_batch", 5))
            self.headless_var.set(self.config["headless"])
            # 智能提交间隔/批量休息
            self.enable_smart_gap_var.set(self.config.get("enable_smart_gap", True))
            self.min_submit_gap.set(self.config.get("min_submit_gap", 10))
            self.max_submit_gap.set(self.config.get("max_submit_gap", 20))
            self.batch_size.set(self.config.get("batch_size", 5))
            self.batch_pause.set(self.config.get("batch_pause", 15))
            # 重新加载题型设置
            self.ai_service.set(DEFAULT_CONFIG["ai_service"])
            self.ai_fill_var.set(DEFAULT_CONFIG["ai_fill_enabled"])
            self.openai_api_key_entry.delete(0, tk.END)
            self.openai_api_key_entry.insert(0, DEFAULT_CONFIG.get("openai_api_key", ""))
            self.qingyan_api_key_entry.delete(0, tk.END)
            self.qingyan_api_key_entry.insert(0, DEFAULT_CONFIG.get("qingyan_api_key", ""))
            self.ai_prompt_combobox.set(DEFAULT_CONFIG["ai_prompt_template"])
            self.reload_question_settings()
            logging.info("已重置为默认配置")

    @staticmethod
    def safe_get(widget, cast_type=int, default=None):
        """
        通用安全型取值，适用于Spinbox、Entry、Scale等，统一异常处理。
        支持直接数值和get方法。
        """
        try:
            val = widget.get() if hasattr(widget, "get") else widget
            return cast_type(val)
        except Exception:
            return default

    def save_config(self):
        import logging
        from tkinter import messagebox

        # === 全局保险：所有题型相关配置的key统一转为字符串，包括question_texts/option_texts ===
        for key in [
            "single_prob", "multiple_prob", "matrix_prob", "texts", "multiple_texts",
            "reorder_prob", "droplist_prob", "scale_prob", "other_texts",
            "question_texts", "option_texts"
        ]:
            if key in self.config:
                self.config[key] = {str(k): v for k, v in self.config[key].items()}

        try:
            # ====== 1. 全局基础配置 ======
            self.config["url"] = self.url_entry.get().strip()
            self.config["target_num"] = int(self.target_entry.get())
            self.config["weixin_ratio"] = self.ratio_scale.get()
            self.config["min_duration"] = int(self.min_duration.get())
            self.config["max_duration"] = int(self.max_duration.get())
            self.config["min_delay"] = float(self.min_delay.get())
            self.config["max_delay"] = float(self.max_delay.get())
            self.config["per_question_delay"] = (float(self.min_q_delay.get()), float(self.max_q_delay.get()))
            self.config["per_page_delay"] = (float(self.min_p_delay.get()), float(self.max_p_delay.get()))
            self.config["submit_delay"] = int(self.submit_delay.get())
            self.config["num_threads"] = int(self.num_threads.get())
            self.config["use_ip"] = self.use_ip_var.get()
            self.config["ip_api"] = self.ip_entry.get().strip()
            self.config["ip_change_mode"] = self.ip_change_mode.get()
            self.config["ip_change_batch"] = int(self.ip_change_batch.get())
            self.config["headless"] = self.headless_var.get()
            self.config["enable_smart_gap"] = self.enable_smart_gap_var.get()
            self.config["min_submit_gap"] = int(self.min_submit_gap.get())
            self.config["max_submit_gap"] = int(self.max_submit_gap.get())
            self.config["batch_size"] = int(self.batch_size.get())
            self.config["batch_pause"] = int(self.batch_pause.get())
            self.config["ai_service"] = self.ai_service.get()
            self.config["ai_fill_enabled"] = self.ai_fill_var.get()
            self.config["openai_api_key"] = self.openai_api_key_entry.get().strip()
            self.config["qingyan_api_key"] = self.qingyan_api_key_entry.get().strip()
            self.config["ai_prompt_template"] = self.ai_prompt_combobox.get()
            # ====== 2. 题型配置 ======
            # 单选题配置
            for i, entry_row in enumerate(self.single_entries):
                q_num = list(self.config["single_prob"].keys())[i]
                probs = []
                all_random = False  # 新增标志，判断是否有选项是-1

                for entry in entry_row:
                    val = entry.get().strip()
                    if val == "-1":
                        all_random = True
                        # 不立即退出，继续检查其他选项
                    else:
                        try:
                            probs.append(float(val))
                        except:
                            probs.append(1.0)

                # 如果有任何一个选项是-1，整个题目设置为随机
                if all_random:
                    self.config["single_prob"][q_num] = -1
                else:
                    self.config["single_prob"][q_num] = probs

            # 多选题配置
            for i, entry_row in enumerate(self.multi_entries):
                q_num = list(self.config["multiple_prob"].keys())[i]
                min_selection = int(self.min_selection_entries[i].get())
                max_selection = int(self.max_selection_entries[i].get())
                option_count = len(self.config["option_texts"][q_num])
                min_selection = max(1, min(min_selection, option_count))
                max_selection = max(min_selection, min(max_selection, option_count))

                probs = []
                for entry in entry_row:
                    try:
                        val = int(entry.get().strip())
                        val = max(0, min(100, val))
                        probs.append(val)
                    except:
                        probs.append(50)

                # 检查是否有其他文本框
                other_val = None
                if q_num in self.other_entries:
                    other_entry = self.other_entries[q_num]
                    other_val = other_entry.get().strip()
                    if other_val:
                        self.config["other_texts"][q_num] = [x.strip() for x in other_val.split(",")]

                self.config["multiple_prob"][q_num] = {
                    "prob": probs,
                    "min_selection": min_selection,
                    "max_selection": max_selection
                }

            # 矩阵题配置
            for i, entry_row in enumerate(self.matrix_entries):
                q_num = list(self.config["matrix_prob"].keys())[i]
                probs = []
                all_random = False  # 新增标志，判断是否有选项是-1

                for entry in entry_row:
                    val = entry.get().strip()
                    if val == "-1":
                        all_random = True
                        # 不立即退出，继续检查其他选项
                    else:
                        try:
                            probs.append(float(val))
                        except:
                            probs.append(1.0)

                # 如果有任何一个选项是-1，整个题目设置为随机
                if all_random:
                    self.config["matrix_prob"][q_num] = -1
                else:
                    self.config["matrix_prob"][q_num] = probs

            # 排序题配置
            for i, entry_row in enumerate(self.reorder_entries):
                q_num = list(self.config["reorder_prob"].keys())[i]
                probs = []
                for entry in entry_row:
                    try:
                        probs.append(float(entry.get().strip()))
                    except:
                        probs.append(0.25)
                self.config["reorder_prob"][q_num] = probs

            # 下拉框题配置
            for i, entry in enumerate(self.droplist_entries):
                q_num = list(self.config["droplist_prob"].keys())[i]
                val = entry.get().strip()
                if val:
                    try:
                        # 使用逗号分隔，转换为浮点数列表
                        prob_list = [float(x.strip()) for x in val.split(",")]
                    except:
                        # 获取默认选项数量
                        option_count = len(self.config["option_texts"].get(q_num, []))
                        prob_list = [0.3] * option_count
                else:
                    # 获取默认选项数量
                    option_count = len(self.config["option_texts"].get(q_num, []))
                    prob_list = [0.3] * option_count

                # 确保概率列表长度与选项数量一致
                option_texts = self.config["option_texts"].get(q_num, [])
                if len(prob_list) > len(option_texts):
                    prob_list = prob_list[:len(option_texts)]
                elif len(prob_list) < len(option_texts):
                    prob_list += [0.3] * (len(option_texts) - len(prob_list))

                self.config["droplist_prob"][q_num] = prob_list

            # 量表题配置
            for i, entry_row in enumerate(self.scale_entries):
                q_num = list(self.config["scale_prob"].keys())[i]
                probs = []
                for entry in entry_row:
                    try:
                        probs.append(float(entry.get().strip()))
                    except:
                        probs.append(0.2)
                self.config["scale_prob"][q_num] = probs

            # 填空题配置
            for i, entry_row in enumerate(self.text_entries):
                q_num = list(self.config["texts"].keys())[i]
                answers = []
                for entry in entry_row:
                    val = entry.get().strip()
                    if val:
                        answers = [x.strip() for x in val.split(",")]
                        break  # 填空题只有一个输入框
                self.config["texts"][q_num] = answers

            # 多项填空配置
            for i, entry_row in enumerate(self.multiple_text_entries):
                q_num = list(self.config["multiple_texts"].keys())[i]
                answers_list = []
                for j, entry in enumerate(entry_row):
                    val = entry.get().strip()
                    if val:
                        answers_list.append([x.strip() for x in val.split(",")])
                    else:
                        answers_list.append(["示例答案"])
                self.config["multiple_texts"][q_num] = answers_list

            # 保存成功
            logging.info("配置保存成功")
            return True
        except Exception as e:
            logging.error(f"保存配置时出错: {str(e)}")
            messagebox.showerror("错误", f"保存配置时出错: {str(e)}")
            return False


    def get_new_proxy(self):
        """拉取代理IP，返回如 http://ip:port 或 http://user:pwd@ip:port"""
        try:
            url = self.config["ip_api"]
            resp = requests.get(url, timeout=8)
            ip = resp.text.strip()
            if ip and "://" not in ip:
                ip = "http://" + ip
            return ip
        except Exception as e:
            logging.error(f"拉取代理失败: {e}")
            return None

    def random_delay(self, min_time=None, max_time=None):
        """生成随机延迟时间"""
        if min_time is None:
            min_time = self.config["min_delay"]
        if max_time is None:
            max_time = self.config["max_delay"]
        delay = random.uniform(min_time, max_time)
        time.sleep(delay)

    def set_blank_texts(self, qid, answers):
        """
        设置指定填空题的答案池，并同步更新对应UI控件（如存在）。
        :param qid: 题目编号（int或str）
        :param answers: 答案列表（list of str）
        """
        qid_str = str(qid)
        # 更新数据
        if "texts" not in self.config:
            self.config["texts"] = {}
        self.config["texts"][qid_str] = answers

        # 如果有UI控件，自动同步显示
        if hasattr(self, 'blank_text_widget') and qid_str in self.blank_text_widget:
            widget = self.blank_text_widget[qid_str]
            widget.delete("1.0", "end")
            for ans in answers:
                widget.insert("end", ans + "\n")
        # 可选：通知其它模块或刷新
        # self.refresh_some_ui_if_needed()
    def generate_sample_answers(self, num):
        """
        批量生成num份问卷模拟答案，返回文本或保存到文件。
        支持AI生成和本地随机生成，自动推断题型和配置。
        """
        import random
        import json

        answers_list = []
        for _ in range(num):
            answer = {}
            for qid, qtext in self.config.get("question_texts", {}).items():
                # 优先选题型
                qid_str = str(qid)
                # 单选题
                if qid_str in self.config.get("single_prob", {}):
                    options = self.config.get("option_texts", {}).get(qid_str, [])
                    probs = self.config["single_prob"][qid_str]
                    if probs == -1 or not isinstance(probs, list):
                        idx = random.randint(0, len(options) - 1)
                    else:
                        total = sum(probs)
                        weights = [p / total for p in probs] if total > 0 else [1 / len(options)] * len(options)
                        idx = random.choices(range(len(options)), weights=weights)[0]
                    answer[qtext] = options[idx] if idx < len(options) else ""
                # 多选题
                elif qid_str in self.config.get("multiple_prob", {}):
                    options = self.config.get("option_texts", {}).get(qid_str, [])
                    conf = self.config["multiple_prob"][qid_str]
                    probs = conf.get("prob", [50] * len(options))
                    min_sel = conf.get("min_selection", 1)
                    max_sel = conf.get("max_selection", max(1, len(options)))
                    sel = []
                    for i, p in enumerate(probs):
                        if random.random() < p / 100:
                            sel.append(options[i] if i < len(options) else "")
                    if len(sel) < min_sel:
                        left = [o for i, o in enumerate(options) if o not in sel]
                        sel += random.sample(left, min(min_sel - len(sel), len(left)))
                    if len(sel) > max_sel:
                        sel = random.sample(sel, max_sel)
                    answer[qtext] = ",".join(sel)
                # 下拉框
                elif qid_str in self.config.get("droplist_prob", {}):
                    options = self.config.get("option_texts", {}).get(qid_str, [])
                    probs = self.config["droplist_prob"][qid_str]
                    total = sum(probs)
                    weights = [p / total for p in probs] if total > 0 else [1 / len(options)] * len(options)
                    idx = random.choices(range(len(options)), weights=weights)[0]
                    answer[qtext] = options[idx] if idx < len(options) else ""
                # 填空题
                elif qid_str in self.config.get("texts", {}):
                    texts = self.config["texts"][qid_str]
                    answer[qtext] = random.choice(texts) if texts else ""
                # 多项填空
                elif qid_str in self.config.get("multiple_texts", {}):
                    ans_lists = self.config["multiple_texts"][qid_str]
                    ans = [random.choice(a) if a else "" for a in ans_lists]
                    answer[qtext] = ";".join(ans)
                # 排序题
                elif qid_str in self.config.get("reorder_prob", {}):
                    options = self.config.get("option_texts", {}).get(qid_str, [])
                    order = options[:]
                    random.shuffle(order)
                    answer[qtext] = "->".join(order)
                # 量表题、矩阵题等
                elif qid_str in self.config.get("scale_prob", {}):
                    options = self.config.get("option_texts", {}).get(qid_str, [])
                    probs = self.config["scale_prob"][qid_str]
                    total = sum(probs)
                    weights = [p / total for p in probs] if total > 0 else [1 / len(options)] * len(options)
                    idx = random.choices(range(len(options)), weights=weights)[0]
                    answer[qtext] = options[idx] if idx < len(options) else ""
                elif qid_str in self.config.get("matrix_prob", {}):
                    options = self.config.get("option_texts", {}).get(qid_str, [])
                    answer[qtext] = random.choice(options) if options else ""
                else:
                    answer[qtext] = ""
            answers_list.append(answer)
        # 可选：保存到文件/返回
        try:
            with open("sample_answers.json", "w", encoding="utf-8") as f:
                json.dump(answers_list, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        return answers_list

    def check_params(self):
        """
        检查当前参数设置的合理性，返回建议和自动修复提示。
        """
        tips = []
        # 目标份数
        try:
            target = int(self.config.get("target_num", 0))
            if target <= 0:
                tips.append("目标份数应大于0。")
        except Exception:
            tips.append("目标份数设置异常。")
        # 微信比例
        ratio = self.config.get("weixin_ratio", 0.5)
        if not (0 <= ratio <= 1):
            tips.append("微信比例应为0~1之间。")
        # 时间区间
        min_d, max_d = self.config.get("min_duration", 1), self.config.get("max_duration", 20)
        if min_d > max_d:
            tips.append("最短时长不能大于最长时长。")
        # 线程数
        threads = self.config.get("num_threads", 4)
        if threads < 1 or threads > 20:
            tips.append("线程数应在1~20之间，建议4~8。")
        # 延迟
        min_delay, max_delay = self.config.get("min_delay", 1), self.config.get("max_delay", 2)
        if min_delay > max_delay:
            tips.append("最小延迟应小于最大延迟。")
        # 批量/休息
        batch_size = self.config.get("batch_size", 5)
        batch_pause = self.config.get("batch_pause", 15)
        if batch_size < 1:
            tips.append("批量份数应≥1。")
        if batch_pause < 0:
            tips.append("批量休息时间应≥0分钟。")
        # 题型/概率检查
        for qid, qtext in self.config.get("question_texts", {}).items():
            qid_str = str(qid)
            if qid_str in self.config.get("single_prob", {}):
                probs = self.config["single_prob"][qid_str]
                if isinstance(probs, list) and abs(sum(probs) - 1) > 0.01 and all(p >= 0 for p in probs):
                    tips.append(f"第{qid}题单选概率和不为1，建议调整。")
            if qid_str in self.config.get("multiple_prob", {}):
                conf = self.config["multiple_prob"][qid_str]
                min_sel = conf.get("min_selection", 1)
                max_sel = conf.get("max_selection", 1)
                if min_sel > max_sel:
                    tips.append(f"第{qid}题多选最小选择数大于最大选择数，请检查。")
        if not tips:
            return "参数设置正常，无需优化。"
        return "\n".join(tips)
    def ai_generate_structure(self):
        """
        本地+AI双重题型识别，AI辅助判别，自动清洗AI返回的非标准JSON，解决‘AI解析失败’弹窗，支持一键修正量表题。
        """
        import logging
        import tkinter.messagebox as messagebox
        import re
        import json
        from ai_questionnaire_parser import ai_parse_questionnaire

        def extract_json(text):
            """更健壮的AI JSON清洗，兼容注释/代码块/多余逗号"""
            text = str(text)
            # 去除所有行首为//的注释
            text = re.sub(r'^\s*//.*$', '', text, flags=re.MULTILINE)
            # 去除代码块标识
            text = text.replace('```json', '').replace('```', '')
            # 只保留第一个完整的大括号包裹内容
            m = re.search(r'\{[\s\S]*\}', text)
            if not m:
                return None
            pure = m.group(0)
            # 去除行尾多余逗号（兼容AI输出的json）
            pure = re.sub(r',\s*([\]}])', r'\1', pure)
            try:
                return json.loads(pure)
            except Exception as e:
                logging.warning(f"[AI解析] JSON解析失败: {e}")
                return None

        api_key = self.qingyan_api_key_entry.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请先填写质谱清言API Key")
            return

        # 本地解析所有题目及类型
        local_types = {}  # qid: 本地类型
        local_type_map = {
            "single_prob": "单选题",
            "multiple_prob": "多选题",
            "matrix_prob": "矩阵题",
            "texts": "填空题",
            "multiple_texts": "多项填空",
            "reorder_prob": "排序题",
            "droplist_prob": "下拉框",
            "scale_prob": "量表题"
        }
        for config_key, type_name in local_type_map.items():
            for qid in self.config.get(config_key, {}):
                local_types[str(qid)] = type_name

        # AI分析一遍所有题，输出AI理解的类型
        questions = []
        for qid, qtext in self.config.get("question_texts", {}).items():
            opts = self.config["option_texts"].get(qid, [])
            questions.append({"id": int(qid), "text": qtext, "options": opts})

        self.status_var.set("AI结构识别中...")
        self.status_indicator.config(foreground="orange")
        self.root.update()

        try:
            ai_raw_result = ai_parse_questionnaire(questions, api_key)

            # --- 自动清洗AI返回的非标准JSON ---
            ai_result = ai_raw_result
            # 如果不是dict或没有questions字段就自动提取纯净JSON
            if not isinstance(ai_raw_result, dict) or "questions" not in ai_raw_result:
                ai_result = extract_json(ai_raw_result)

            if not ai_result or "questions" not in ai_result:
                # 失败弹窗中显示原始AI内容
                messagebox.showerror(
                    "AI解析失败",
                    f"AI返回内容无法解析结构。\n\n建议：\n1. 检查API Key和网络。\n2. 升级AI Prompt确保只输出标准JSON。\n3. 联系开发者。\n\nAI原始返回：\n{str(ai_raw_result)[:800]}"
                )
                self.status_var.set("AI结构识别失败")
                self.status_indicator.config(foreground="red")
                return

            # 比对同一题号本地类型和AI类型
            ai_type_map = {
                "填空": "填空题",
                "多项填空": "多项填空",
                "单选": "单选题",
                "多选": "多选题",
                "量表": "量表题",
                "矩阵": "矩阵题",
                "下拉": "下拉框",
                "排序": "排序题"
            }
            ai_types = {}
            for q in ai_result["questions"]:
                qid = str(q.get("id"))
                ai_type = ai_type_map.get(q.get("type", ""), q.get("type", ""))
                ai_types[qid] = ai_type

            # 标记疑似量表题（本地为单选，AI为量表）
            suspect_scale_qids = [
                qid for qid in local_types
                if local_types[qid] == "单选题" and ai_types.get(qid) == "量表题"
            ]

            # 日志栏/弹窗提示，允许一键修正
            if suspect_scale_qids:
                msg = "检测到以下题目本地判为【单选题】，AI认为是【量表题】：\n"
                for qid in suspect_scale_qids:
                    qtext = self.config["question_texts"].get(qid, "")
                    msg += f"第{qid}题：{qtext[:30]}\n"
                msg += "\n是否将这些题型自动改为量表题？（建议采纳，如内容确实为Likert量表）"
                logging.warning("疑似量表题：" + "、".join(suspect_scale_qids))
                if messagebox.askyesno("AI建议", msg):
                    # 应用修正
                    for qid in suspect_scale_qids:
                        # 移除单选题配置
                        if qid in self.config["single_prob"]:
                            del self.config["single_prob"][qid]
                        # 添加量表题配置
                        opts = self.config["option_texts"].get(qid, [])
                        self.config["scale_prob"][qid] = [0.2] * len(opts)
                    logging.info(f"已将{len(suspect_scale_qids)}道题型改为量表题。")
                    self.reload_question_settings()
                    messagebox.showinfo("修正完成", "已自动修正疑似量表题，题型设置已刷新。")
                else:
                    logging.info("用户未采纳AI量表修正建议。")
            else:
                logging.info("未检测到需修正的疑似量表题。")

            # 输出AI题型统计
            type_count = {name: 0 for name in ai_type_map.values()}
            for typ in ai_types.values():
                if typ in type_count:
                    type_count[typ] += 1
            stats = "，".join(f"{k}:{v}" for k, v in type_count.items())
            logging.info(f"AI题型统计：{stats}")

            self.status_var.set("AI结构识别完成")
            self.status_indicator.config(foreground="green")

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("AI解析失败", f"{e}")
            self.status_var.set("AI结构识别失败")
            self.status_indicator.config(foreground="red")

    def set_param(self, key, value):
        """
        设置全局参数如目标份数，并同步刷新主UI控件和显示。
        支持AI助手Tab指令后自动刷新对应控件。
        """
        if key in self.config:
            self.config[key] = value
            # 刷新UI控件
            try:
                if key == "target_num":
                    # 目标份数（Spinbox）
                    self.target_entry.set(value)
                elif key == "weixin_ratio":
                    # 微信作答比率（Scale/Label）
                    self.ratio_scale.set(float(value))
                    self.ratio_var.set(f"{float(value) * 100:.0f}%")
                elif key == "min_duration":
                    self.min_duration.set(int(value))
                elif key == "max_duration":
                    self.max_duration.set(int(value))
                elif key == "min_delay":
                    self.min_delay.set(float(value))
                elif key == "max_delay":
                    self.max_delay.set(float(value))
                elif key == "per_question_delay":
                    # value为元组或列表
                    self.min_q_delay.set(float(value[0]))
                    self.max_q_delay.set(float(value[1]))
                elif key == "per_page_delay":
                    self.min_p_delay.set(float(value[0]))
                    self.max_p_delay.set(float(value[1]))
                elif key == "submit_delay":
                    self.submit_delay.set(int(value))
                elif key == "num_threads":
                    self.num_threads.set(int(value))
                elif key == "use_ip":
                    self.use_ip_var.set(bool(value))
                elif key == "ip_api":
                    self.ip_entry.delete(0, "end")
                    self.ip_entry.insert(0, str(value))
                elif key == "ip_change_mode":
                    self.ip_change_mode.set(value)
                elif key == "ip_change_batch":
                    self.ip_change_batch.set(int(value))
                elif key == "headless":
                    self.headless_var.set(bool(value))
                elif key == "enable_smart_gap":
                    self.enable_smart_gap_var.set(bool(value))
                elif key == "min_submit_gap":
                    self.min_submit_gap.set(int(value))
                elif key == "max_submit_gap":
                    self.max_submit_gap.set(int(value))
                elif key == "batch_size":
                    self.batch_size.set(int(value))
                elif key == "batch_pause":
                    self.batch_pause.set(int(value))
                elif key == "ai_service":
                    self.ai_service.set(value)
                elif key == "ai_fill_enabled":
                    self.ai_fill_var.set(bool(value))
                elif key == "openai_api_key":
                    self.openai_api_key_entry.delete(0, "end")
                    self.openai_api_key_entry.insert(0, str(value))
                elif key == "qingyan_api_key":
                    self.qingyan_api_key_entry.delete(0, "end")
                    self.qingyan_api_key_entry.insert(0, str(value))
                elif key == "ai_prompt_template":
                    self.ai_prompt_combobox.set(str(value))
            except Exception as e:
                import logging
                logging.warning(f"set_param({key})时同步控件出错: {e}")

            # 题型参数变化时刷新题型设置
            if key in [
                "single_prob", "multiple_prob", "matrix_prob", "texts", "multiple_texts",
                "reorder_prob", "droplist_prob", "scale_prob", "other_texts",
                "question_texts", "option_texts"
            ]:
                self.reload_question_settings()
            return True, f"{key} 已修改为 {value}"
        return False, f"参数 {key} 不存在"

    def set_question_type(self, q_num, q_type):
        """设置指定题号的题型"""
        q_num = str(q_num)
        if q_num not in self.config["question_texts"]:
            return False, f"题目 {q_num} 不存在"
        # 清除该题在所有题型配置里的记录
        for config_key in [
            "single_prob", "multiple_prob", "matrix_prob", "texts", "multiple_texts",
            "reorder_prob", "droplist_prob", "scale_prob"
        ]:
            if q_num in self.config[config_key]:
                del self.config[config_key][q_num]
        # 加入新题型
        type_map = {
            "单选题": "single_prob",
            "多选题": "multiple_prob",
            "矩阵题": "matrix_prob",
            "填空题": "texts",
            "多项填空": "multiple_texts",
            "排序题": "reorder_prob",
            "下拉框": "droplist_prob",
            "量表题": "scale_prob"
        }
        q_type_key = type_map.get(q_type)
        if not q_type_key:
            return False, f"不支持的类型: {q_type}"
        option_count = len(self.config["option_texts"].get(q_num, []))
        if q_type_key == "single_prob":
            self.config["single_prob"][q_num] = -1
        elif q_type_key == "multiple_prob":
            self.config["multiple_prob"][q_num] = {
                "prob": [50] * option_count,
                "min_selection": 1,
                "max_selection": max(1, option_count)
            }
        elif q_type_key == "texts":
            self.config["texts"][q_num] = ["自动填写内容"]
        elif q_type_key == "multiple_texts":
            self.config["multiple_texts"][q_num] = [["自动填写内容"]] * option_count
        elif q_type_key == "matrix_prob":
            self.config["matrix_prob"][q_num] = -1
        elif q_type_key == "reorder_prob":
            self.config["reorder_prob"][q_num] = [0.25] * option_count
        elif q_type_key == "droplist_prob":
            self.config["droplist_prob"][q_num] = [0.3] * option_count
        elif q_type_key == "scale_prob":
            self.config["scale_prob"][q_num] = [0.2] * option_count
        self.reload_question_settings()
        return True, f"第{q_num}题已修改为{q_type}"

    def set_question_prob(self, q_num, probs):
        """设置题目选项概率"""
        q_num = str(q_num)
        for config_key in [
            "single_prob", "multiple_prob", "matrix_prob",
            "reorder_prob", "droplist_prob", "scale_prob"
        ]:
            if q_num in self.config[config_key]:
                if config_key == "multiple_prob":
                    if isinstance(self.config[config_key][q_num]["prob"], list):
                        self.config[config_key][q_num]["prob"] = probs
                else:
                    self.config[config_key][q_num] = probs
                self.reload_question_settings()
                return True, f"第{q_num}题概率已设置为: {probs}"
        return False, f"未找到题目 {q_num} 的概率配置"

    def get_param(self, key):
        """获取参数值"""
        if key in self.config:
            return True, f"{key} = {self.config[key]}"
        return False, f"参数 {key} 不存在"

    def get_question_type(self, q_num):
        """获取题目类型"""
        q_num = str(q_num)
        type_map = {
            "single_prob": "单选题",
            "multiple_prob": "多选题",
            "matrix_prob": "矩阵题",
            "texts": "填空题",
            "multiple_texts": "多项填空",
            "reorder_prob": "排序题",
            "droplist_prob": "下拉框",
            "scale_prob": "量表题"
        }
        for key, name in type_map.items():
            if q_num in self.config[key]:
                return True, f"第{q_num}题是{name}"
        return False, f"未找到题目 {q_num} 的类型"

    def update_ui_from_config(self):
        """根据配置更新UI控件"""
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, self.config["url"])
        self.target_entry.delete(0, tk.END)
        self.target_entry.insert(0, str(self.config["target_num"]))
        self.ratio_scale.set(self.config["weixin_ratio"])
        self.update_ratio_display()
        self.reload_question_settings()


if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    root.geometry("1280x900")  # 增大初始窗口尺寸，宽度≥1200
    app = WJXAutoFillApp(root)
    root.mainloop()
