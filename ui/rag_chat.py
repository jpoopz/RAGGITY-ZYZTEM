import json
import threading
import requests
import tkinter as tk
import customtkinter as ctk


class RAGChat(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color="#101214")
        self.app = app

        # Header
        ctk.CTkLabel(self, text="RAG Chat", font=("Segoe UI", 18, "bold")).pack(padx=16, pady=(16,8), anchor="w")

        # History view
        self.history = ctk.CTkTextbox(self, state="disabled")
        self.history.pack(fill="both", expand=True, padx=16, pady=(0,8))

        # Settings mini-row
        opts = ctk.CTkFrame(self)
        opts.pack(fill="x", padx=16, pady=(0,8))
        self.stream_var = tk.BooleanVar(value=True)
        ctk.CTkSwitch(opts, text="Stream", variable=self.stream_var).pack(side="left")
        ctk.CTkLabel(opts, text="top_k").pack(side="left", padx=(12,4))
        self.k_var = tk.StringVar(value="5")
        ctk.CTkEntry(opts, textvariable=self.k_var, width=60).pack(side="left")
        ctk.CTkLabel(opts, text="temperature").pack(side="left", padx=(12,4))
        self.temp_var = tk.DoubleVar(value=0.2)
        ctk.CTkSlider(opts, from_=0.0, to=1.0, number_of_steps=20, variable=self.temp_var, width=140).pack(side="left", padx=(0,12))

        # Input row (multiline up to ~3 lines height)
        input_row = ctk.CTkFrame(self)
        input_row.pack(fill="x", padx=16, pady=(0,12))
        self.input = ctk.CTkTextbox(input_row, height=64)
        self.input.pack(side="left", fill="x", expand=True)
        self.input.bind("<Control-Return>", lambda _e: self._send())
        btns = ctk.CTkFrame(input_row)
        btns.pack(side="left", padx=(8,0))
        ctk.CTkButton(btns, text="Send", command=self._send, width=90).pack(pady=(0,6))
        ctk.CTkButton(btns, text="Clear", command=self._clear, width=90, fg_color="#374151").pack()

        self._sending = False

    def _append(self, who: str, text: str):
        self.history.configure(state="normal")
        self.history.insert("end", f"[{who}] {text}\n")
        self.history.configure(state="disabled")
        self.history.see("end")

    def _append_sources(self, contexts):
        chips = []
        for c in contexts or []:
            title = c.get("title") or c.get("source") or "doc"
            page = c.get("page") or c.get("page_number")
            if page is not None:
                chips.append(f"{title}:page {page}")
            else:
                chips.append(title)
        if chips:
            self._append("sources", " | ".join(chips))

    def _clear(self):
        self.history.configure(state="normal")
        self.history.delete("1.0", "end")
        self.history.configure(state="disabled")

    def _send(self):
        if self._sending:
            return
        q = self.input.get("1.0", "end").strip()
        if not q:
            return
        self._append("you", q)
        self.input.delete("1.0", "end")
        self._sending = True

        def run():
            try:
                k = int(self.k_var.get() or "5")
            except Exception:
                k = 5
            if self.stream_var.get():
                try:
                    with requests.get("http://127.0.0.1:8000/query_stream", params={"q": q, "k": k}, stream=True, timeout=120) as r:
                        if r.status_code != 200:
                            self._append("error", f"HTTP {r.status_code}")
                        else:
                            acc = []
                            for line in r.iter_lines(decode_unicode=True):
                                if not line:
                                    continue
                                if line.startswith("data: "):
                                    payload = line[6:]
                                    if payload == "[DONE]":
                                        continue
                                    try:
                                        obj = json.loads(payload)
                                    except Exception:
                                        # Treat as token
                                        self._append("model", payload)
                                        acc.append(payload)
                                        continue
                                    if obj.get("type") == "token":
                                        token = obj.get("text", "")
                                        if token:
                                            self._append("model", token)
                                            acc.append(token)
                                    elif obj.get("type") == "sources":
                                        self._append_sources(obj.get("contexts", []))
                except Exception as e:
                    self._append("error", f"stream failed: {e}")
            else:
                try:
                    r = requests.get("http://127.0.0.1:8000/query", params={"q": q, "k": k}, timeout=120)
                    if r.ok:
                        data = r.json()
                        self._append("model", data.get("answer", ""))
                        self._append_sources(data.get("contexts", []))
                    else:
                        self._append("error", f"HTTP {r.status_code}")
                except Exception as e:
                    self._append("error", f"request failed: {e}")
            self._sending = False

        threading.Thread(target=run, daemon=True).start()


