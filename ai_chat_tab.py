import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import requests
import time
import json
import re

class AIChatTab(ttk.Frame):
    def __init__(self, master, api_key_getter, api_service_getter, app_ref=None, model_name="gpt-3.5-turbo"):
        super().__init__(master)
        self.api_key_getter = api_key_getter
        self.api_service_getter = api_service_getter
        self.model_name = model_name
        self.history = []
        self.app_ref = app_ref  # 主程序引用，便于参数操作
        self.build_ui()
        self.add_welcome_message()

    def build_ui(self):
        # 创建主布局
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 标题栏
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(header_frame, text="问卷助手", font=('微软雅黑', 14, 'bold'),
                  foreground="#2c3e50").pack(side=tk.LEFT)

        # 添加问卷相关功能按钮
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side=tk.RIGHT)

        self.analyze_btn = ttk.Button(
            btn_frame,
            text="分析问卷",
            command=self.analyze_questionnaire,
            width=10
        )
        self.analyze_btn.pack(side=tk.LEFT, padx=5)

        self.extract_btn = ttk.Button(
            btn_frame,
            text="提取答案",
            command=self.extract_answers,
            width=10
        )
        self.extract_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = ttk.Button(
            btn_frame,
            text="清除记录",
            command=self.clear_chat,
            width=10
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        # 聊天记录区域
        self.chat_history = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            state='disabled',
            font=('微软雅黑', 11),
            bg='#f9f9f9',
            padx=15,
            pady=15,
            height=18,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground="#e0e0e0"
        )
        self.chat_history.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 添加标签样式
        self.chat_history.tag_configure("user", foreground="#1565c0", font=('微软雅黑', 11, 'bold'))
        self.chat_history.tag_configure("ai", foreground="#2e7d32", font=('微软雅黑', 11, 'bold'))
        self.chat_history.tag_configure("system", foreground="#7b1fa2", font=('微软雅黑', 11, 'bold'))
        self.chat_history.tag_configure("error", foreground="#c62828", font=('微软雅黑', 11, 'bold'))
        self.chat_history.tag_configure("action", foreground="#e65100", font=('微软雅黑', 11, 'bold'))

        # 输入区域
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X)

        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(
            input_frame,
            textvariable=self.input_var,
            font=('微软雅黑', 12)
        )
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_entry.bind("<Return>", self.on_send)
        self.input_entry.focus_set()

        btn_frame = ttk.Frame(input_frame)
        btn_frame.pack(side=tk.LEFT)

        self.send_btn = ttk.Button(
            btn_frame,
            text="发送",
            command=self.on_send,
            width=8
        )
        self.send_btn.pack(side=tk.LEFT, padx=(0, 5))

        self.export_btn = ttk.Button(
            btn_frame,
            text="导出",
            command=self.export_chat,
            width=8
        )
        self.export_btn.pack(side=tk.LEFT)

    def add_welcome_message(self):
        """添加初始欢迎消息"""
        welcome_msg = (
            "您好！我是您的问卷自动化助手。\n\n"
            "我可以帮助您：\n"
            "1. 分析问卷结构和要求\n"
            "2. 生成符合问卷要求的答案\n"
            "3. 提取关键信息并整理答案\n"
            "4. 解释问卷中的复杂问题\n"
            "5. 支持直接用自然语言控制问卷参数，比如输入：\n"
            "   - 目标份数改为200\n"
            "   - 第3题改成多选题\n"
            "   - 第2题概率改成0.3,0.7\n"
            "   - 第4题是什么题型\n"
            "请将问卷内容粘贴给我，或直接提出您的问题。"
        )
        self.add_message("AI助手", welcome_msg, "ai")

    def add_message(self, sender, message, tag=None):
        """添加消息到聊天记录"""
        if not tag:
            tag = "user" if sender == "用户" else "ai"

        self.chat_history.config(state='normal')

        # 添加发送者标签
        prefix = f"{sender}: " if sender else ""
        self.chat_history.insert(tk.END, prefix, tag)

        # 添加消息内容
        self.chat_history.insert(tk.END, message + "\n\n")

        # 滚动到底部
        self.chat_history.see(tk.END)
        self.chat_history.config(state='disabled')

    def on_send(self, event=None):
        message = self.input_var.get().strip()
        if not message:
            return
        # 先尝试参数指令
        if self.try_handle_param_command(message):
            self.input_var.set("")
            return
        # 添加用户消息
        self.add_message("用户", message)
        self.history.append({"role": "user", "content": message})

        # 清空输入框
        self.input_var.set("")

        # 禁用发送按钮
        self.send_btn.config(state=tk.DISABLED)
        self.input_entry.config(state=tk.DISABLED)

        # 添加"思考中"提示
        self.add_message("AI助手", "正在处理您的请求，请稍候...", "system")

        # 启动新线程获取AI回复
        threading.Thread(target=self.get_ai_response, daemon=True).start()

    def try_handle_param_command(self, message):
        """
        检查并处理参数修改指令。
        支持的样例：
        - 目标份数改为200
        - 第3题改成多选题
        - 第2题概率改成0.3,0.7
        - 目标份数是多少
        - 第4题是什么题型
        """
        if not self.app_ref:
            return False
        # 支持的类型
        # 改目标份数
        m = re.match(r"目标[份数]*[为|改为|设置为|=](\d+)", message)
        if m:
            n = int(m.group(1))
            ok, msg = self.app_ref.set_param("target_num", n)
            self.add_message("系统", msg, "system")
            return True

        # 改题型
        m = re.match(r"第(\d+)题[型|题型|类型]*[为|改为|设置为|=](.+)", message)
        if m:
            q_num, q_type = m.group(1), m.group(2).strip()
            ok, msg = self.app_ref.set_question_type(q_num, q_type)
            self.add_message("系统", msg, "system")
            return True

        # 改概率
        m = re.match(r"第(\d+)题概率[为|改为|设置为|=]([\d\., ]+)", message)
        if m:
            q_num, value = m.group(1), m.group(2)
            probs = [float(x.strip()) for x in value.split(",") if x.strip()]
            ok, msg = self.app_ref.set_prob(q_num, probs)
            self.add_message("系统", msg, "system")
            return True

        # 查询目标份数
        m = re.match(r"目标[份数]*[多少|现在|是多少|的值]", message)
        if m:
            val = self.app_ref.get_param("target_num")
            self.add_message("系统", f"当前目标份数为：{val}", "system")
            return True

        # 查询题型
        m = re.match(r"第(\d+)题.*(题型|类型|是什么)", message)
        if m:
            q_num = str(m.group(1))
            type_map = {
                "single_prob": "单选题", "multiple_prob": "多选题", "matrix_prob": "矩阵题", "texts": "填空题",
                "multiple_texts": "多项填空", "reorder_prob": "排序题", "droplist_prob": "下拉框", "scale_prob": "量表题"
            }
            found = "未知"
            for key, name in type_map.items():
                if q_num in self.app_ref.config.get(key, {}):
                    found = name
            self.add_message("系统", f"第{q_num}题的题型为：{found}", "system")
            return True

        return False

    def get_ai_response(self):
        """获取AI回复"""
        try:
            # 获取API参数
            api_key = self.api_key_getter()
            if not api_key:
                raise ValueError("请先设置API密钥")

            service = self.api_service_getter()
            if not service:
                raise ValueError("请选择API服务")

            # 构建消息历史
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

            # 保留最近的8条历史消息
            messages.extend(self.history[-8:])

            # 调用API
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
                    "temperature": 0.3,  # 降低随机性，使回答更稳定
                    "max_tokens": 800
                },
                timeout=45
            )

            # 检查API响应
            if response.status_code != 200:
                error_info = response.json().get("error", {}).get("message", "未知错误")
                raise ConnectionError(f"API错误 ({response.status_code}): {error_info}")

            # 解析响应
            answer = response.json()["choices"][0]["message"]["content"].strip()

            # 保存到历史记录
            self.history.append({"role": "assistant", "content": answer})

            # 在UI线程中更新显示
            self.after(0, lambda: self.show_ai_response(answer))

        except Exception as e:
            # 在UI线程中显示错误
            self.after(0, lambda: self.show_error(str(e)))

    def show_ai_response(self, answer):
        """显示AI回复"""
        # 删除"思考中"提示
        self.chat_history.config(state='normal')
        self.chat_history.delete("end-3l", "end-1l")
        self.chat_history.config(state='disabled')

        # 添加AI回复
        self.add_message("AI助手", answer)

        # 重新启用控件
        self.send_btn.config(state=tk.NORMAL)
        self.input_entry.config(state=tk.NORMAL)
        self.input_entry.focus_set()

    def show_error(self, error_msg):
        """显示错误消息"""
        # 删除"思考中"提示
        self.chat_history.config(state='normal')
        self.chat_history.delete("end-3l", "end-1l")
        self.chat_history.config(state='disabled')

        # 添加错误信息
        self.add_message("系统错误", error_msg, "error")

        # 重新启用控件
        self.send_btn.config(state=tk.NORMAL)
        self.input_entry.config(state=tk.NORMAL)
        self.input_entry.focus_set()

    def analyze_questionnaire(self):
        """分析问卷内容"""
        self.add_message("系统", "请粘贴问卷内容，我将为您分析结构并提取关键要求。", "action")
        self.input_entry.focus_set()

    def extract_answers(self):
        """从对话中提取答案"""
        if not self.history:
            self.add_message("系统", "暂无聊天记录可提取答案。", "system")
            return

        self.add_message("系统", "正在从对话中提取问卷答案...", "system")

        # 创建新线程处理
        threading.Thread(target=self.process_answer_extraction, daemon=True).start()

    def process_answer_extraction(self):
        """处理答案提取逻辑"""
        try:
            # 构建提取请求
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

            # 获取API参数
            api_key = self.api_key_getter()
            if not api_key:
                raise ValueError("请先设置API密钥")

            service = self.api_service_getter()
            if not service:
                raise ValueError("请选择API服务")

            # 构建消息
            messages = [
                {"role": "system", "content": "你是一个问卷答案提取助手，专门从对话中提取结构化答案。"},
                {"role": "user", "content": extraction_prompt},
                {"role": "assistant", "content": "请提供对话历史以便我提取答案。"}
            ]

            # 添加最近的对话历史
            for msg in self.history[-10:]:
                messages.append(msg)

            # 调用API
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
                    "temperature": 0.1,  # 低随机性确保格式正确
                    "response_format": {"type": "json_object"},
                    "max_tokens": 1000
                },
                timeout=60
            )

            # 检查响应
            if response.status_code != 200:
                error_info = response.json().get("error", {}).get("message", "未知错误")
                raise ConnectionError(f"API错误 ({response.status_code}): {error_info}")

            # 解析JSON响应
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
        """格式化提取的答案"""
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
        """显示提取的答案"""
        # 删除"处理中"提示
        self.chat_history.config(state='normal')
        self.chat_history.delete("end-3l", "end-1l")
        self.chat_history.config(state='disabled')

        # 添加提取的答案
        self.add_message("AI助手", "已提取问卷答案:\n" + formatted_answers, "ai")

        # 添加导出提示
        self.add_message("系统", "您可以使用右上角的'导出'按钮保存这些答案。", "system")

    def clear_chat(self):
        """清除聊天记录"""
        self.history = []
        self.chat_history.config(state='normal')
        self.chat_history.delete(1.0, tk.END)
        self.chat_history.config(state='disabled')
        self.add_welcome_message()

    def export_chat(self):
        """导出聊天记录"""
        try:
            # 获取聊天内容
            self.chat_history.config(state='normal')
            content = self.chat_history.get(1.0, tk.END)
            self.chat_history.config(state='disabled')

            # 创建保存对话框
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