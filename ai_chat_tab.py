import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import requests
import json
import re

class AIChatTab(ttk.Frame):
    def __init__(self, master, api_key_getter, api_service_getter, app_ref=None, model_name="gpt-3.5-turbo"):
        super().__init__(master)
        self.api_key_getter = api_key_getter
        self.api_service_getter = api_service_getter
        self.app_ref = app_ref  # 主程序引用
        self.model_name = model_name
        self.history = []
        self.build_ui()
        self.add_welcome_message()

    def build_ui(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="问卷助手", font=('微软雅黑', 14, 'bold'),
                  foreground="#2c3e50").pack(side=tk.LEFT)

        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)

        self.analyze_btn = ttk.Button(
            btn_frame, text="分析问卷", command=self.analyze_questionnaire, width=10
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=5)

        self.extract_btn = ttk.Button(
            btn_frame, text="提取答案", command=self.extract_answers, width=10
        )
        self.extract_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(
            btn_frame, text="清除记录", command=self.clear_chat, width=10
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        self.chat_history = scrolledtext.ScrolledText(
            main_frame, wrap=tk.WORD, state='disabled', font=('微软雅黑', 11),
            bg='#f9f9f9', padx=15, pady=15, height=18, relief=tk.FLAT,
            highlightthickness=1, highlightbackground="#e0e0e0"
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.chat_history.tag_configure("user", foreground="#1565c0", font=('微软雅黑', 11, 'bold'))
        self.chat_history.tag_configure("ai", foreground="#2e7d32", font=('微软雅黑', 11, 'bold'))
        self.chat_history.tag_configure("system", foreground="#7b1fa2", font=('微软雅黑', 11, 'bold'))
        self.chat_history.tag_configure("error", foreground="#c62828", font=('微软雅黑', 11, 'bold'))
        self.chat_history.tag_configure("action", foreground="#e65100", font=('微软雅黑', 11, 'bold'))

        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X)

        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(
            input_frame, textvariable=self.input_var, font=('微软雅黑', 12)
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_entry.bind("<Return>", self.on_send)
        self.input_entry.focus_set()

        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(side=tk.LEFT)

        self.send_btn = ttk.Button(
            btn_frame, text="发送", command=self.on_send, width=8
        )
        self.send_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.export_btn = ttk.Button(
            btn_frame, text="导出", command=self.export_chat, width=8
        )
        self.export_btn.pack(side=tk.LEFT)

    def add_welcome_message(self):
        welcome = (
            "我是问卷助手，您可以通过自然语言指令控制问卷参数，例如：\n"
            "• 目标份数改为200\n"
            "• 微信比例设为30%\n"
            "• 最短时长设为5\n"
            "• 最大延迟为2\n"
            "• 线程数改为8\n"
            "• 批量休息为20\n"
            "• 无头模式启用\n"
            "• OpenAI Key设为sk-xxx\n"
            "• 第3题改为多选题\n"
            "• 第1题概率设为0.7,0.3\n"
            "• 查询目标份数\n"
            "• 第2题是什么题型\n"
            "请输入您的指令或问题..."
        )
        self.add_message("助手", welcome, "assistant")

    def add_message(self, sender, message, tag=None):
        if not tag:
            tag = "user" if sender == "用户" else "ai"
        self.chat_history.config(state='normal')
        prefix = f"{sender}: " if sender else ""
        self.chat_history.insert(tk.END, prefix, tag)
        self.chat_history.insert(tk.END, message + "\n\n")
        self.chat_history.see(tk.END)
        self.chat_history.config(state='disabled')

    def on_send(self, event=None):
        message = self.input_var.get().strip()
        if not message:
            return
        self.add_message("您", message, "user")
        self.input_var.set("")
        if self.try_handle_param_command(message):
            return
        self.add_message("AI助手", "正在处理您的请求，请稍候...", "system")
        threading.Thread(target=self.get_ai_response, daemon=True).start()

    def try_handle_param_command(self, message):
        if not self.app_ref:
            return False

        # 中文数字转阿拉伯数字
        def chinese2digits(s):
            zh_digit_map = {'零':0, '一':1, '二':2, '三':3, '四':4, '五':5, '六':6, '七':7, '八':8, '九':9, '十':10}
            if s.isdigit():
                return int(s)
            if s in zh_digit_map:
                return zh_digit_map[s]
            if '十' in s:
                parts = s.split('十')
                if len(parts) == 2:
                    left = zh_digit_map.get(parts[0], 1) if parts[0] else 1
                    right = zh_digit_map.get(parts[1], 0) if parts[1] else 0
                    return left*10+right
            return None

        # 通用参数映射
        param_map = {
            "问卷链接": "url",
            "目标份数": "target_num",
            "微信比例": "weixin_ratio",
            "最短时长": "min_duration",
            "最长时长": "max_duration",
            "最小延迟": "min_delay",
            "最大延迟": "max_delay",
            "提交延迟": "submit_delay",
            "线程数": "num_threads",
            "启用代理": "use_ip",
            "代理地址": "ip_api",
            "代理切换方式": "ip_change_mode",
            "代理切换份数": "ip_change_batch",
            "无头模式": "headless",
            "智能间隔": "enable_smart_gap",
            "单份最小间隔": "min_submit_gap",
            "单份最大间隔": "max_submit_gap",
            "批量份数": "batch_size",
            "批量休息": "batch_pause",
            "AI服务": "ai_service",
            "AI自动答题": "ai_fill_enabled",
            "OpenAI Key": "openai_api_key",
            "清言Key": "qingyan_api_key",
            "Prompt模板": "ai_prompt_template",
        }

        # 1. 通用参数修改，支持“XX设为YY”“把XX改成YY”“XX用YY”“XX等于YY”“XX为YY”
        for zh_name, key in param_map.items():
            m = re.search(rf"{zh_name}[：: ]*(设为|改为|设置为|=|为|等于|用|改成)?[ ]*([\w\.\-@%/]+)", message)
            if m:
                value = m.group(2)
                # 自动类型转换
                if value.lower() in ("true", "on", "yes", "启用"):
                    value = True
                elif value.lower() in ("false", "off", "no", "禁用"):
                    value = False
                elif key in ["weixin_ratio"]:
                    value = float(value)
                    if value > 1: value = value / 100.0
                elif re.match(r"^\d+\.\d+$", value):
                    value = float(value)
                elif value.isdigit():
                    value = int(value)
                ok, msg = self.app_ref.set_param(key, value)
                self.add_message("系统", msg, "system")
                return True

        # 2. 题型/题目相关
        match = re.search(r'(第?([一二三四五六七八九十\d]+)题)[^\n]*?(改为|改成|设为|设置为|=)\s*([多单矩填排下量选空序拉表]+题)', message)
        if match:
            num_raw = match.group(2)
            q_num = chinese2digits(num_raw)
            q_type = match.group(4)
            if q_num and q_type:
                ok, msg = self.app_ref.set_question_type(q_num, q_type)
                self.add_message("系统", msg, "system")
                return True

        # 3. 概率指令
        match = re.search(r'(第?([一二三四五六七八九十\d]+)题)[^\n]*概率[^\d]*(\d[\d,\. ]+)', message)
        if match:
            num_raw = match.group(2)
            q_num = chinese2digits(num_raw)
            probs_str = match.group(3)
            probs = [float(x) for x in re.split(r'[,， ]+', probs_str) if x]
            ok, msg = self.app_ref.set_question_prob(q_num, probs)
            self.add_message("系统", msg, "system")
            return True

        # 4. 查询题型
        match = re.search(r'(第?([一二三四五六七八九十\d]+)题)[^\n]*(什么题型|类型)', message)
        if match:
            num_raw = match.group(2)
            q_num = chinese2digits(num_raw)
            ok, msg = self.app_ref.get_question_type(q_num)
            self.add_message("系统", msg, "system")
            return True

        # 5. 查询参数
        for zh_name, key in param_map.items():
            if re.search(rf"({zh_name})[^\n]*(多少|几|是多少|现在|当前|多少份|多少个|的值)?", message):
                ok, msg = self.app_ref.get_param(key)
                self.add_message("系统", msg, "system")
                return True

        return False

    def get_ai_response(self):
        try:
            api_key = self.api_key_getter()
            if not api_key:
                raise ValueError("请先设置API密钥")
            service = self.api_service_getter()
            if not service:
                raise ValueError("请选择API服务")
            messages = [{
                "role": "system",
                "content": (
                    "你是一个专业的问卷填写助手，专门帮助用户填写各种问卷。"
                    "你的任务是理解问卷问题，提供准确、简洁、符合要求的答案。"
                    "对于开放式问题，提供2-3句完整的回答。"
                    "对于选择题，直接给出选项字母或数字。"
                    "如果用户需要分析问卷，提取关键要求并结构化展示。"
                )
            }]
            messages.extend(self.history[-8:])
            if service == "OpenAI":
                endpoint = "https://api.openai.com/v1/chat/completions"
                model = self.model_name
            else:
                endpoint = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
                model = "glm-4"
            response = requests.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 800
                },
                timeout=45
            )
            if response.status_code != 200:
                error_info = response.json().get("error", {}).get("message", "未知错误")
                raise ConnectionError(f"API错误 ({response.status_code}): {error_info}")
            answer = response.json()["choices"][0]["message"]["content"].strip()
            self.history.append({"role": "assistant", "content": answer})
            self.after(0, lambda: self.show_ai_response(answer))
        except Exception as e:
            self.after(0, lambda: self.show_error(str(e)))

    def show_ai_response(self, answer):
        self.chat_history.config(state='normal')
        self.chat_history.delete("end-3l", "end-1l")
        self.chat_history.config(state='disabled')
        self.add_message("AI助手", answer)
        self.send_btn.config(state=tk.NORMAL)
        self.input_entry.config(state=tk.NORMAL)
        self.input_entry.focus_set()

    def show_error(self, error_msg):
        self.chat_history.config(state='normal')
        self.chat_history.delete("end-3l", "end-1l")
        self.chat_history.config(state='disabled')
        self.add_message("系统错误", error_msg, "error")
        self.send_btn.config(state=tk.NORMAL)
        self.input_entry.config(state=tk.NORMAL)
        self.input_entry.focus_set()

    def analyze_questionnaire(self):
        self.add_message("系统", "请粘贴问卷内容，我将为您分析结构并提取关键要求。", "action")
        self.input_entry.focus_set()

    def extract_answers(self):
        if not self.history:
            self.add_message("系统", "暂无聊天记录可提取答案。", "system")
            return
        self.add_message("系统", "正在从对话中提取问卷答案...", "system")
        threading.Thread(target=self.process_answer_extraction, daemon=True).start()

    def process_answer_extraction(self):
        try:
            extraction_prompt = (
                "请从对话历史中提取所有问卷答案，按以下格式返回JSON：\n"
                "{\n"
                "  \"questionnaire_title\": \"问卷标题\",\n"
                "  \"answers\": [\n"
                "    {\"question\": \"问题1\", \"answer\": \"答案1\"},\n"
                "    {\"question\": \"问题2\", \"answer\": \"答案2\"}\n"
                "  ]\n"
                "}\n"
                "只返回JSON数据，不要包含其他内容。"
            )
            api_key = self.api_key_getter()
            if not api_key:
                raise ValueError("请先设置API密钥")
            service = self.api_service_getter()
            if not service:
                raise ValueError("请选择API服务")
            messages = [
                {"role": "system", "content": "你是一个问卷答案提取助手，专门从对话中提取结构化答案。"},
                {"role": "user", "content": extraction_prompt},
                {"role": "assistant", "content": "请提供对话历史以便我提取答案。"}
            ]
            for msg in self.history[-10:]:
                messages.append(msg)
            if service == "OpenAI":
                endpoint = "https://api.openai.com/v1/chat/completions"
                model = self.model_name
            else:
                endpoint = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
                model = "glm-4"
            response = requests.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"},
                    "max_tokens": 1000
                },
                timeout=60
            )
            if response.status_code != 200:
                error_info = response.json().get("error", {}).get("message", "未知错误")
                raise ConnectionError(f"API错误 ({response.status_code}): {error_info}")
            result = response.json()["choices"][0]["message"]["content"].strip()
            try:
                answers_data = json.loads(result)
                formatted_answers = self.format_answers(answers_data)
                self.after(0, lambda: self.show_extracted_answers(formatted_answers))
            except json.JSONDecodeError:
                self.after(0, lambda: self.add_message("AI助手", f"提取的答案：\n{result}", "ai"))
        except Exception as e:
            self.after(0, lambda: self.show_error(f"答案提取失败: {str(e)}"))

    def format_answers(self, answers_data):
        title = answers_data.get("questionnaire_title", "未命名问卷")
        answers = answers_data.get("answers", [])
        if not answers:
            return "未提取到有效答案"
        result = f"问卷标题: {title}\n\n答案列表:\n"
        for i, item in enumerate(answers, 1):
            question = item.get("question", f"问题{i}")
            answer = item.get("answer", "无答案")
            result += f"\n{i}. {question}\n   → {answer}\n"
        return result

    def show_extracted_answers(self, formatted_answers):
        self.chat_history.config(state='normal')
        self.chat_history.delete("end-3l", "end-1l")
        self.chat_history.config(state='disabled')
        self.add_message("AI助手", "已提取问卷答案:\n" + formatted_answers, "ai")
        self.add_message("系统", "您可以使用右上角的'导出'按钮保存这些答案。", "system")

    def clear_chat(self):
        self.history = []
        self.chat_history.config(state='normal')
        self.chat_history.delete(1.0, tk.END)
        self.chat_history.config(state='disabled')
        self.add_welcome_message()

    def export_chat(self):
        try:
            self.chat_history.config(state='normal')
            content = self.chat_history.get(1.0, tk.END)
            self.chat_history.config(state='disabled')
            from tkinter import filedialog
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                title="保存聊天记录"
            )
            if file_path:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("=== 问卷助手聊天记录 ===\n\n")
                    f.write(content)
                messagebox.showinfo("导出成功", f"聊天记录已保存到:\n{file_path}")
        except Exception as e:
            messagebox.showerror("导出错误", f"保存文件时出错:\n{str(e)}")