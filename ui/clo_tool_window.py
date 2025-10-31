import os
import json
import socket
import threading
import random
import time
import tkinter as tk
import customtkinter as ctk
import requests


UI_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def _load_ui_config():
    try:
        with open(UI_CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_ui_config(data: dict):
    try:
        os.makedirs(os.path.dirname(UI_CONFIG_PATH), exist_ok=True)
        with open(UI_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _tcp_probe(host: str, port: int, timeout: float = 0.6):
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            s.settimeout(timeout)
            s.sendall(b'{"ping":"clo"}\n')
            data = s.recv(128)
            try:
                msg = json.loads(data.decode("utf-8", errors="ignore"))
                ok = msg.get("pong") == "clo"
                return ok, ("ok" if ok else "wrong_service")
            except Exception:
                return False, "wrong_service"
    except socket.timeout:
        return False, "timeout"
    except Exception:
        return False, "timeout"


class CLOToolWindow(ctk.CTkToplevel):
    def __init__(self, master=None):
        super().__init__(master)
        self.title("CLO3D Tool")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.resizable(True, True)

        cfg = _load_ui_config()
        self.host_var = tk.StringVar(value=str(cfg.get("clo_host", "127.0.0.1")))
        self.port_var = tk.StringVar(value=str(cfg.get("clo_port", "51235")))
        self._probing = False
        self._stop = False
        self._long_action = False

        # Header
        header = ctk.CTkLabel(self, text="CLO3D Tool", font=("Segoe UI", 18, "bold"))
        header.pack(padx=12, pady=(12, 6))

        # Status banner
        self.banner = ctk.CTkLabel(self, text="Status: idle", fg_color="#444444", corner_radius=6)
        self.banner.pack(fill="x", padx=12, pady=(0, 12))

        # Connect row
        row = ctk.CTkFrame(self)
        row.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(row, text="Host").pack(side="left", padx=(8, 4))
        host_entry = ctk.CTkEntry(row, textvariable=self.host_var, width=140)
        host_entry.pack(side="left")
        ctk.CTkLabel(row, text="Port").pack(side="left", padx=(12, 4))
        port_entry = ctk.CTkEntry(row, textvariable=self.port_var, width=90)
        port_entry.pack(side="left")
        ctk.CTkButton(row, text="Connect", command=self._connect).pack(side="left", padx=12)
        ctk.CTkButton(row, text="How to connect", fg_color="#3b82f6", command=self._show_helper).pack(side="left")
        ctk.CTkButton(row, text="Test Port Now", command=self._probe_now).pack(side="left", padx=(8,0))

        # Actions row
        actions = ctk.CTkFrame(self)
        actions.pack(fill="x", padx=12, pady=6)
        ctk.CTkButton(actions, text="Import Garment", command=lambda: self._send_cmd({"cmd": "import_garment"})).pack(side="left", padx=6)
        ctk.CTkButton(actions, text="Run Simulation 50", command=lambda: self._send_cmd({"cmd": "simulate", "steps": 50})).pack(side="left", padx=6)
        ctk.CTkButton(actions, text="Screenshot", command=lambda: self._send_cmd({"cmd": "screenshot"})).pack(side="left", padx=6)
        ctk.CTkButton(actions, text="Export…", command=lambda: self._send_cmd({"cmd": "export"})).pack(side="left", padx=6)

        # Mini chat
        chat_frame = ctk.CTkFrame(self)
        chat_frame.pack(fill="both", expand=True, padx=12, pady=6)
        self.history = ctk.CTkTextbox(chat_frame, state="disabled")
        self.history.pack(fill="both", expand=True, padx=8, pady=8)
        input_row = ctk.CTkFrame(chat_frame)
        input_row.pack(fill="x", padx=8, pady=(0,8))
        self.input = ctk.CTkEntry(input_row)
        self.input.pack(side="left", fill="x", expand=True)
        self.input.bind("<Control-Return>", lambda _e: self._send_json())
        self.bind("<Escape>", self._esc_close)
        ctk.CTkButton(input_row, text="Send", command=self._send_json).pack(side="left", padx=8)

        # Geometry restore
        geom = cfg.get("clo_geometry")
        if geom:
            try:
                self.geometry(geom)
            except Exception:
                pass

        # Start periodic probe
        self.after(250, self._schedule_probe)

    def _set_banner(self, state: str, text: str):
        colors = {
            "ok": ("#065f46", "#10b981"),    # dark, light text
            "probing": ("#78350f", "#f59e0b"),
            "down": ("#7f1d1d", "#ef4444"),
            "idle": ("#374151", "#e5e7eb"),
        }
        bg, fg = colors.get(state, ("#374151", "#e5e7eb"))
        self.banner.configure(text=text, fg_color=bg, text_color=fg)

    def _probe_http_api(self, api_host: str, api_port: int):
        try:
            r = requests.get(f"http://{api_host}:{api_port}/health/clo", timeout=0.8)
            if not r.ok:
                return False, "api_unreachable"
            j = r.json()
            return bool(j.get("ok")), j.get("handshake", "unknown")
        except Exception:
            return False, "api_error"

    def _probe(self):
        api_host, api_port = self._get_api_endpoint()
        clo_host = self.host_var.get().strip() or "127.0.0.1"
        try:
            clo_port = int(self.port_var.get().strip() or "51235")
        except Exception:
            clo_port = 51235
        ok_api, hs_api = self._probe_http_api(api_host, api_port)
        if ok_api:
            return True, f"api:{hs_api}"
        ok_tcp, hs_tcp = _tcp_probe(clo_host, clo_port)
        return ok_tcp, f"tcp:{hs_tcp}"

    def _schedule_probe(self):
        if self._stop:
            return
        jitter_ms = random.randint(300, 500)
        interval_ms = random.randint(5000, 7000) + jitter_ms
        def run():
            ok, hs = self._probe()
            clo_host, clo_port = self.host_var.get(), self.port_var.get()
            if ok:
                if hs.startswith("api:"):
                    self._set_banner("ok", f"CLO Bridge connected ✓ API✓ {hs.split(':',1)[1]} @ {clo_host}:{clo_port}")
                else:
                    self._set_banner("ok", f"CLO Bridge connected ✓ {hs} @ {clo_host}:{clo_port}")
            else:
                if hs.endswith("timeout"):
                    self._set_banner("down", "Listener not found — in CLO: Script → Run Script… → modules\\clo_companion\\clo_bridge_listener.py")
                elif hs.endswith("wrong_service"):
                    self._set_banner("down", "Port in use by another service — adjust port in config")
            if not self._stop:
                self.after(interval_ms, self._schedule_probe)
        self._set_banner("probing", "Probing CLO Bridge…")
        threading.Thread(target=run, daemon=True).start()

    def _probe_now(self):
        self._set_banner("probing", "Probing now…")
        def run():
            ok, hs = self._probe()
            clo_host, clo_port = self.host_var.get(), self.port_var.get()
            if ok:
                if hs.startswith("api:"):
                    self._set_banner("ok", f"CLO Bridge connected ✓ API✓ {hs.split(':',1)[1]} @ {clo_host}:{clo_port}")
                else:
                    self._set_banner("ok", f"CLO Bridge connected ✓ {hs} @ {clo_host}:{clo_port}")
            else:
                self._set_banner("down", "Listener not found — in CLO: Script → Run Script… → modules\\clo_companion\\clo_bridge_listener.py")
        threading.Thread(target=run, daemon=True).start()

    def _get_api_endpoint(self):
        host, port = "127.0.0.1", 8000
        try:
            with open(os.path.join("config", "academic_rag_config.json"), "r", encoding="utf-8") as f:
                j = json.load(f)
                host = j.get("host", host)
                port = int(j.get("port", port))
        except Exception:
            pass
        return host, port

    def _connect(self):
        # Persist host/port
        cfg = _load_ui_config()
        cfg["clo_host"] = self.host_var.get().strip() or "127.0.0.1"
        try:
            cfg["clo_port"] = int(self.port_var.get().strip() or "51235")
        except Exception:
            cfg["clo_port"] = 51235
        cfg["clo_geometry"] = self.geometry()
        _save_ui_config(cfg)
        self._probe_now()

    def _send_json(self):
        text = self.input.get().strip()
        if not text:
            return
        try:
            obj = json.loads(text)
        except Exception:
            obj = {"text": text}
        self._send_cmd(obj)

    def _append_history(self, who: str, msg: str):
        self.history.configure(state="normal")
        self.history.insert("end", f"[{who}] {msg}\n")
        self.history.configure(state="disabled")
        self.history.see("end")

    def _send_cmd(self, payload: dict):
        host = self.host_var.get().strip() or "127.0.0.1"
        try:
            port = int(self.port_var.get().strip() or "51235")
        except Exception:
            port = 51235
        self._append_history("you", json.dumps(payload))
        def run():
            try:
                with socket.create_connection((host, port), timeout=1.2) as s:
                    s.sendall(json.dumps(payload).encode("utf-8") + b"\n")
                    s.settimeout(1.2)
                    data = s.recv(4096)
                    self._append_history("clo", data.decode("utf-8", errors="ignore").strip())
            except Exception as e:
                self._append_history("error", f"send failed: {e}")
        threading.Thread(target=run, daemon=True).start()

    def _show_helper(self):
        top = ctk.CTkToplevel(self)
        top.title("How to connect")
        top.geometry("520x360")
        txt = (
            "1) In CLO: Script → Run Script…\n"
            "2) Select: modules\\clo_companion\\clo_bridge_listener.py\n"
            "3) Allow firewall when prompted\n"
            "4) Back here: Host=127.0.0.1, Port=51235 → Connect\n\n"
            "Troubleshoot:\n"
            "- PowerShell: Test-NetConnection 127.0.0.1 -Port 51235\n"
            "- If another app occupies the port, change it in config and restart CLO script"
        )
        box = ctk.CTkTextbox(top)
        box.pack(fill="both", expand=True, padx=12, pady=12)
        box.insert("1.0", txt)
        box.configure(state="disabled")
        ctk.CTkButton(top, text="OK", command=top.destroy).pack(pady=(0,12))

    def _esc_close(self, _e=None):
        if self._long_action:
            if not tk.messagebox.askokcancel("Close", "A long action is running. Close anyway?"):
                return
        self._on_close()

    def _on_close(self):
        self._stop = True
        # Persist geometry
        cfg = _load_ui_config()
        cfg["clo_geometry"] = self.geometry()
        _save_ui_config(cfg)
        self.destroy()


