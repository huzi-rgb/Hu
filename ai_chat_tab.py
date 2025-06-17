import tkinter as tk
from tkinter import ttk, messagebox
import threading
import requests
import markdown
from tkhtmlview import HTMLLabel

class ChatHtmlArea(tk.Frame):
    """只显示html，排版100%原生，还原网页风格，支持鼠标滚轮区域滚动"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self, bg="#f5f5f5", bd=0, highlightthickness=0, width=1000, height=480)
        self.scrollbar = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg="#f5f5f5")
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.inner.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        # 只绑定canvas区域，不要bind_all
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel) # Linux
        self.canvas.bind("<Button-5>", self._on_mousewheel)

    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event=None):
        self.canvas.itemconfig(self.inner_id, width=event.width)

    def _on_mousewheel(self, event):
        # Windows/macOS
        if hasattr(event, 'delta') and event.delta:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        elif hasattr(event, 'num'):
            if event.num == 4:
                self.canvas.yview_scroll(-3, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(3, "units")

    def add_ai_html(self, html_code):
        """直接插入HTML，不做任何外包裹，100%还原网页格式"""
        widget = HTMLLabel(self.inner, html=html_code, background="#e3f7fb", font=("微软雅黑", 18), width=110, padx=8, pady=12)
        widget.pack(anchor="w", fill="both", expand=False, pady=10, padx=10)
        self.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def add_user(self, text):
        """用户提问：右侧绿色大字"""
        label = tk.Label(self.inner, text=text, bg="#c8e6c9", fg="#222", font=("微软雅黑", 18, "bold"),
                         wraplength=820, justify="left", anchor="e", padx=22, pady=12)
        label.pack(anchor="e", pady=10, padx=(220, 20))
        self.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def clear_all(self):
        for widget in self.inner.winfo_children():
            widget.destroy()

class AIChatTab(ttk.Frame):
    def __init__(self, master, api_key_getter, api_service_getter, model_name="gpt-3.5-turbo"):
        super().__init__(master)
        self.api_key_getter = api_key_getter
        self.api_service_getter = api_service_getter
        self.model_name = model_name
        self.history = []
        self.build_ui()

    def build_ui(self):
        self.html_area = ChatHtmlArea(self, width=1000, height=480)
        self.html_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, padx=5, pady=7)
        self.input_var = tk.StringVar()
        self.input_entry = tk.Entry(input_frame, textvariable=self.input_var, font=("微软雅黑", 16))
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 7), ipady=6)
        self.input_entry.bind("<Return>", self.on_send)
        self.send_btn = tk.Button(input_frame, text="发送", font=("微软雅黑", 14), bg="#4caf50", fg="white",
                                  relief="flat", command=self.on_send, width=10)
        self.send_btn.pack(side=tk.LEFT)

    def on_send(self, event=None):
        question = self.input_var.get().strip()
        if not question:
            return
        self.html_area.add_user(question)
        self.history.append({"role": "user", "content": question})
        self.input_var.set("")
        self.send_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.ask_ai, args=(question,), daemon=True).start()

    def add_ai_html(self, text):
        html_code = markdown.markdown(text)
        self.html_area.add_ai_html(html_code)

    def ask_ai(self, question):
        self.add_ai_html("（思考中...）")
        api_key = self.api_key_getter()
        service = self.api_service_getter()
        messages = [{"role": "system", "content": "你是问卷自动化专家，请用网页格式美观地展示你的回答。"}]
        for msg in self.history[-6:]:
            messages.append(msg)
        messages.append({"role": "user", "content": question})

        try:
            if service == "OpenAI":
                resp = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "model": self.model_name,
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 800
                    }, timeout=60
                )
                resp.raise_for_status()
                data = resp.json()
                answer = data["choices"][0]["message"]["content"].strip()
            else:
                resp = requests.post(
                    "https://open.bigmodel.cn/api/paas/v4/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "glm-4",
                        "messages": messages,
                        "temperature": 0.7,
                        "max_tokens": 800
                    }, timeout=60
                )
                resp.raise_for_status()
                data = resp.json()
                answer = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip() or "（无回答）"
            self.history.append({"role": "assistant", "content": answer})
            self.html_area.clear_all()
            # 回放聊天历史（用户+AI均以原格式显示）
            for msg in self.history:
                if msg["role"] == "user":
                    self.html_area.add_user(msg["content"])
                else:
                    html_code = markdown.markdown(msg["content"])
                    self.html_area.add_ai_html(html_code)
        except Exception as e:
            self.html_area.add_ai_html(f"<b>出错了:</b> {e}")
        finally:
            self.send_btn.config(state=tk.NORMAL)