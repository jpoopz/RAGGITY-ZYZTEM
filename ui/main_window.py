"""
RAGGITY ZYZTEM 2.0 - Main UI Window
Premium dark UI with app bar, icon sidebar, and card-based layout
"""

import customtkinter as ctk
import threading
import requests
import time
import os
import sys
from pathlib import Path

# Add parent to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from ui.theme import (
    apply_theme, heading, subheading, body, mono, Card, StatusLabel,
    ACCENT, TEXT, TEXT_SECONDARY, STATUS_OK, STATUS_WARN, STATUS_ERROR, DARK_BG
)
from core.gpu import get_gpu_status
from core.config import CFG
from logger import log

# Import cloud bridge
try:
    from core.cloud_bridge import bridge
    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False


class RaggityUI(ctk.CTk):
    """Main application window with app bar and icon sidebar"""
    
    def __init__(self):
        super().__init__()
        self.title("RAGGITY ZYZTEM 2.0")
        self.geometry("1200x750")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Network operation counter for spinner
        self.active_operations = 0
        
        # Create layout
        self.create_app_bar()
        
        # Main container with sidebar + content
        main_container = ctk.CTkFrame(self, fg_color=DARK_BG)
        main_container.pack(fill="both", expand=True)
        
        self.sidebar = Sidebar(self, main_container)
        self.sidebar.pack(side="left", fill="y")
        
        self.content = ContentArea(self, main_container)
        self.content.pack(side="right", fill="both", expand=True)
        
        # Start status updates
        self.after(2000, self.update_status)
        self.after(500, self.update_spinner)

    def create_app_bar(self):
        """Create top app bar with status indicators"""
        self.app_bar = ctk.CTkFrame(self, height=50, fg_color="#0a0a0c")
        self.app_bar.pack(fill="x", padx=0, pady=0)
        self.app_bar.pack_propagate(False)
        
        # App title
        title = ctk.CTkLabel(
            self.app_bar,
            text="⚙️ RAGGITY ZYZTEM 2.0",
            font=heading(),
            text_color=ACCENT
        )
        title.pack(side="left", padx=20)
        
        # Spinner (shown during network ops)
        self.spinner_label = ctk.CTkLabel(
            self.app_bar,
            text="",
            font=body(),
            text_color=STATUS_INFO
        )
        self.spinner_label.pack(side="left", padx=10)
        
        # Status indicators on right
        status_frame = ctk.CTkFrame(self.app_bar, fg_color="transparent")
        status_frame.pack(side="right", padx=20)
        
        # API Status
        self.api_status = StatusLabel(status_frame, status="info", text="API: Checking...")
        self.api_status.pack(side="left", padx=10)
        
        # GPU Status
        self.gpu_status = ctk.CTkLabel(
            status_frame,
            text="GPU: ...",
            font=body(),
            text_color=TEXT_SECONDARY
        )
        self.gpu_status.pack(side="left", padx=10)

    def update_status(self):
        """Update API and GPU status (non-blocking)"""
        def check_status():
            # Check API
            try:
                r = requests.get("http://localhost:8000/health", timeout=1)
                if r.ok:
                    self.after(0, lambda: self.api_status.set_status("ok", "API: ✓ Online"))
                else:
                    self.after(0, lambda: self.api_status.set_status("error", "API: ✗ Down"))
            except Exception:
                self.after(0, lambda: self.api_status.set_status("error", "API: ✗ Offline"))
            
            # Check GPU
            try:
                gpu = get_gpu_status()
                if gpu["available"]:
                    name = gpu.get("name", "Unknown")[:20]
                    util = gpu.get("utilization", 0)
                    text = f"GPU: {name} ({util:.0f}%)"
                    color = STATUS_OK if util < 80 else STATUS_WARN
                else:
                    text = "GPU: CPU Only"
                    color = TEXT_SECONDARY
                
                self.after(0, lambda: self.gpu_status.configure(text=text, text_color=color))
            except Exception:
                pass
        
        threading.Thread(target=check_status, daemon=True).start()
        self.after(5000, self.update_status)

    def update_spinner(self):
        """Update spinner animation"""
        if self.active_operations > 0:
            spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            current = getattr(self, '_spinner_idx', 0)
            self.spinner_label.configure(text=spinner_chars[current % len(spinner_chars)])
            self._spinner_idx = current + 1
        else:
            self.spinner_label.configure(text="")
        
        self.after(100, self.update_spinner)

    def on_close(self):
        """Handle window close"""
        log("UI: Window closing", "UI")
        self.destroy()


class Sidebar(ctk.CTkFrame):
    """Icon-based sidebar navigation"""
    
    def __init__(self, app, parent):
        super().__init__(parent, width=180, fg_color="#0a0a0c")
        self.pack_propagate(False)
        self.app = app
        
        # Navigation items with icons
        self.nav_items = [
            ("📊", "Dashboard"),
            ("📥", "Ingest"),
            ("💬", "Query"),
            ("🖥️", "System"),
            ("📜", "Logs"),
            ("☁️", "Bridge"),
            ("👗", "CLO3D")
        ]
        
        self.buttons = []
        self.active_button = None
        
        # Add spacing at top
        ctk.CTkLabel(self, text="", height=20).pack()
        
        for icon, name in self.nav_items:
            btn = ctk.CTkButton(
                self,
                text=f"{icon}  {name}",
                command=lambda n=name: self.select_tab(n),
                fg_color="transparent",
                text_color=TEXT_SECONDARY,
                hover_color="#1a1a1e",
                anchor="w",
                font=body(),
                height=45
            )
            btn.pack(pady=3, padx=10, fill="x")
            self.buttons.append((name, btn))
        
        # Select Dashboard by default
        self.select_tab("Dashboard")

    def select_tab(self, name):
        """Select a tab and update button styling"""
        # Reset all buttons
        for tab_name, btn in self.buttons:
            if tab_name == name:
                btn.configure(fg_color=ACCENT, text_color="white")
                self.active_button = btn
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY)
        
        # Show tab in content area
        self.app.content.show_tab(name)


class ContentArea(ctk.CTkFrame):
    """Main content area with tabs"""
    
    def __init__(self, app, parent):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        
        # Create all tabs
        self.tabs = {
            "Dashboard": DashboardTab(self, app),
            "Ingest": IngestTab(self, app),
            "Query": QueryTab(self, app),
            "System": SystemTab(self, app),
            "Logs": LogsTab(self, app),
            "Bridge": BridgeTab(self, app),
            "CLO3D": CLO3DTab(self, app)
        }
        
        # Place all tabs
        for tab in self.tabs.values():
            tab.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        self.show_tab("Dashboard")

    def show_tab(self, name):
        """Show the specified tab"""
        for tab_name, tab in self.tabs.items():
            if tab_name == name:
                tab.lift()
            else:
                tab.lower()
        
        log(f"UI: Switched to {name} tab", "UI")


# ========== Tab Implementations ==========

class DashboardTab(ctk.CTkFrame):
    """Dashboard overview tab"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        
        # Title
        title = ctk.CTkLabel(self, text="Dashboard", font=heading())
        title.pack(pady=20)
        
        # Welcome card
        welcome_card = Card(self)
        welcome_card.pack(padx=20, pady=10, fill="x")
        
        ctk.CTkLabel(
            welcome_card,
            text="Welcome to RAGGITY ZYZTEM 2.0",
            font=subheading()
        ).pack(pady=15, padx=20)
        
        ctk.CTkLabel(
            welcome_card,
            text="Modern RAG system with cloud integration",
            font=body(),
            text_color=TEXT_SECONDARY
        ).pack(padx=20, pady=5)
        
        # Quick stats card
        stats_card = Card(self)
        stats_card.pack(padx=20, pady=10, fill="both", expand=True)
        
        ctk.CTkLabel(stats_card, text="Quick Stats", font=subheading()).pack(pady=10)
        
        self.stats_text = ctk.CTkLabel(
            stats_card,
            text="Loading...",
            font=body(),
            justify="left"
        )
        self.stats_text.pack(pady=10, padx=20)
        
        # Start stats update
        self.after(1000, self.update_dashboard_stats)

    def update_dashboard_stats(self):
        """Update dashboard stats"""
        def fetch():
            try:
                r = requests.get("http://localhost:8000/system-stats", timeout=2)
                if r.ok:
                    data = r.json()
                    stats = f"CPU: {data.get('cpu_percent', 0):.1f}%  |  "
                    stats += f"RAM: {data.get('mem_percent', 0):.1f}%  |  "
                    stats += f"Ollama: {'Running' if data.get('ollama_running') else 'Stopped'}"
                    
                    self.after(0, lambda: self.stats_text.configure(text=stats))
            except Exception:
                pass
        
        threading.Thread(target=fetch, daemon=True).start()
        self.after(5000, self.update_dashboard_stats)


class IngestTab(ctk.CTkFrame):
    """File ingestion tab"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        
        # Title
        title = ctk.CTkLabel(self, text="Ingest Documents", font=heading())
        title.pack(pady=20)
        
        # Ingest card
        ingest_card = Card(self)
        ingest_card.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Path entry
        ctk.CTkLabel(ingest_card, text="File or Directory Path", font=subheading()).pack(pady=10, padx=20)
        
        self.entry = ctk.CTkEntry(
            ingest_card,
            placeholder_text="Enter path or drag file here...",
            height=40,
            font=body()
        )
        self.entry.pack(padx=20, pady=10, fill="x")
        
        # Ingest button
        self.ingest_btn = ctk.CTkButton(
            ingest_card,
            text="Ingest",
            command=self.do_ingest,
            height=40,
            font=subheading(),
            fg_color=ACCENT
        )
        self.ingest_btn.pack(pady=10)
        
        # Status
        self.status = StatusLabel(ingest_card, status="info", text="")
        self.status.pack(pady=5)
        
        # Output console
        self.output = ctk.CTkTextbox(ingest_card, font=mono(), wrap="word")
        self.output.pack(fill="both", expand=True, padx=20, pady=10)
        self.output.insert("1.0", "Ready to ingest documents.\n")

    def do_ingest(self):
        """Trigger file ingestion (non-blocking)"""
        path = self.entry.get().strip('"')
        
        if not path or not os.path.exists(path):
            self.output.insert("end", f"[!] Invalid path: {path}\n")
            self.status.set_status("error", "✗ Invalid Path")
            return
        
        self.ingest_btn.configure(state="disabled")
        self.status.set_status("info", "⏳ Ingesting...")
        self.output.insert("end", f"\n[→] Starting ingestion: {path}\n")
        self.app.active_operations += 1
        
        def run():
            try:
                r = requests.post(
                    "http://localhost:8000/ingest-path",
                    json={"path": path},
                    timeout=60
                )
                
                def update_ui():
                    self.app.active_operations -= 1
                    if r.ok:
                        result = r.json()
                        self.output.insert("end", f"[+] Success! {result.get('message', '')}\n")
                        self.status.set_status("ok", "✓ Complete")
                    else:
                        self.output.insert("end", f"[x] Error {r.status_code}\n")
                        self.status.set_status("error", "✗ Failed")
                    self.ingest_btn.configure(state="normal")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: Ingestion exception: {e}", "UI")
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.output.insert("end", f"[x] Error: {e}\n")
                    self.status.set_status("error", "✗ Error")
                    self.ingest_btn.configure(state="normal")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()


class QueryTab(ctk.CTkFrame):
    """Query interface tab"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        
        # Title
        title = ctk.CTkLabel(self, text="Query Knowledge Base", font=heading())
        title.pack(pady=20)
        
        # Query card
        query_card = Card(self)
        query_card.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Query input
        ctk.CTkLabel(query_card, text="Ask a Question", font=subheading()).pack(pady=10, padx=20)
        
        self.query_entry = ctk.CTkEntry(
            query_card,
            placeholder_text="Enter your question...",
            height=40,
            font=body()
        )
        self.query_entry.pack(padx=20, pady=10, fill="x")
        self.query_entry.bind("<Return>", lambda e: self.submit_query())
        
        # Query button
        self.query_btn = ctk.CTkButton(
            query_card,
            text="Submit Query",
            command=self.submit_query,
            height=40,
            font=subheading(),
            fg_color=ACCENT
        )
        self.query_btn.pack(pady=10)
        
        # Status
        self.status = StatusLabel(query_card, status="info", text="")
        self.status.pack(pady=5)
        
        # Answer display
        self.answer_box = ctk.CTkTextbox(query_card, font=body(), wrap="word")
        self.answer_box.pack(fill="both", expand=True, padx=20, pady=10)
        self.answer_box.insert("1.0", "Enter a question to get started.\n")

    def submit_query(self):
        """Submit query (non-blocking)"""
        q = self.query_entry.get().strip()
        if not q:
            return
        
        self.query_btn.configure(state="disabled")
        self.status.set_status("info", "⏳ Querying...")
        self.answer_box.delete("1.0", "end")
        self.answer_box.insert("1.0", "⏳ Fetching answer...\n")
        self.app.active_operations += 1
        
        def run():
            try:
                r = requests.get(
                    "http://localhost:8000/query",
                    params={"q": q, "k": 5},
                    timeout=60
                )
                
                def update_ui():
                    self.app.active_operations -= 1
                    if r.ok:
                        ans = r.json()
                        self.answer_box.delete("1.0", "end")
                        self.answer_box.insert("end", f"Q: {q}\n\n", "question")
                        self.answer_box.insert("end", f"A: {ans['answer']}\n\n", "answer")
                        
                        contexts = ans.get("contexts", [])
                        if contexts:
                            self.answer_box.insert("end", "─" * 50 + "\nContexts:\n\n")
                            for i, ctx in enumerate(contexts[:3], 1):
                                self.answer_box.insert("end", f"[{i}] {ctx[:250]}...\n\n")
                        
                        self.status.set_status("ok", f"✓ Found {len(contexts)} contexts")
                    else:
                        self.answer_box.delete("1.0", "end")
                        self.answer_box.insert("end", f"Error {r.status_code}: {r.text}\n")
                        self.status.set_status("error", "✗ Error")
                    
                    self.query_btn.configure(state="normal")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: Query exception: {e}", "UI")
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.answer_box.delete("1.0", "end")
                    self.answer_box.insert("end", f"Error: {e}\n")
                    self.status.set_status("error", "✗ Connection Error")
                    self.query_btn.configure(state="normal")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()


class SystemTab(ctk.CTkFrame):
    """System statistics tab"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        
        # Title
        title = ctk.CTkLabel(self, text="System Monitor", font=heading())
        title.pack(pady=20)
        
        # Stats card
        stats_card = Card(self)
        stats_card.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Status
        self.status = StatusLabel(stats_card, status="info", text="⏳ Loading...")
        self.status.pack(pady=10)
        
        # Stats display
        self.stats_text = ctk.CTkTextbox(stats_card, font=mono())
        self.stats_text.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.after(500, self.update_stats)

    def update_stats(self):
        """Update system statistics (non-blocking)"""
        def fetch():
            try:
                r = requests.get("http://localhost:8000/system-stats", timeout=3)
                if r.ok:
                    data = r.json()
                    
                    stats = "=== System Statistics ===\n\n"
                    stats += f"CPU: {data.get('cpu_percent', 0):.1f}%\n"
                    stats += f"Memory: {data.get('mem_percent', 0):.1f}% "
                    stats += f"({data.get('mem_used_mb', 0)} / {data.get('mem_total_mb', 0)} MB)\n\n"
                    
                    gpu = data.get("gpu", {})
                    if gpu.get("available"):
                        stats += f"GPU: {gpu.get('name', 'Unknown')}\n"
                        stats += f"GPU Utilization: {gpu.get('utilization', 0):.1f}%\n"
                        stats += f"GPU Memory: {gpu.get('memory_percent', 0):.1f}%\n"
                        if gpu.get('temperature'):
                            stats += f"GPU Temp: {gpu.get('temperature')}°C\n"
                    else:
                        stats += "GPU: Not Available\n"
                    
                    stats += f"\nOllama: {'✓ Running' if data.get('ollama_running') else '✗ Stopped'}\n"
                    stats += f"\nVector Store: {CFG.vector_store.upper()}\n"
                    stats += f"Provider: {CFG.provider.upper()}\n"
                    stats += f"Model: {CFG.model_name}\n"
                    
                    def update_ui():
                        self.stats_text.delete("1.0", "end")
                        self.stats_text.insert("end", stats)
                        self.status.set_status("ok", "✓ Updated")
                    
                    self.after(0, update_ui)
                else:
                    self.after(0, lambda: self.status.set_status("error", "✗ API Error"))
            except Exception:
                self.after(0, lambda: self.status.set_status("error", "✗ Connection Error"))
        
        threading.Thread(target=fetch, daemon=True).start()
        self.after(4000, self.update_stats)


class LogsTab(ctk.CTkFrame):
    """Live logs viewer tab"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        
        # Title
        title = ctk.CTkLabel(self, text="Live Logs", font=heading())
        title.pack(pady=20)
        
        # Logs card
        logs_card = Card(self)
        logs_card.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Status
        self.status = StatusLabel(logs_card, status="info", text="")
        self.status.pack(pady=10)
        
        # Log viewer
        self.log_viewer = ctk.CTkTextbox(logs_card, font=mono(), wrap="word")
        self.log_viewer.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.after(1000, self.refresh)

    def refresh(self):
        """Refresh logs (non-blocking)"""
        log_file = os.path.join(BASE_DIR, "Logs", "app.log")
        
        def read():
            try:
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()[-50:]
                    
                    content = "".join(lines) if lines else "No logs yet.\n"
                    
                    def update_ui():
                        self.log_viewer.delete("1.0", "end")
                        self.log_viewer.insert("end", content)
                        self.status.set_status("ok", f"✓ {len(lines)} lines")
                    
                    self.after(0, update_ui)
                else:
                    self.after(0, lambda: self.status.set_status("warn", "⚠ Log file not found"))
            except Exception:
                pass
        
        threading.Thread(target=read, daemon=True).start()
        self.after(4000, self.refresh)


class BridgeTab(ctk.CTkFrame):
    """Cloud Bridge tab"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        
        # Title
        title = ctk.CTkLabel(self, text="Cloud Bridge", font=heading())
        title.pack(pady=20)
        
        if not BRIDGE_AVAILABLE:
            Card(self).pack(padx=20, pady=20)
            ctk.CTkLabel(
                self,
                text="⚠️ Cloud Bridge not available",
                font=subheading(),
                text_color=STATUS_WARN
            ).pack(pady=50)
            return
        
        # Bridge card
        bridge_card = Card(self)
        bridge_card.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Config display
        cloud_url = os.getenv("CLOUD_URL", "Not configured")
        ctk.CTkLabel(
            bridge_card,
            text=f"URL: {cloud_url}",
            font=body(),
            text_color=TEXT_SECONDARY
        ).pack(pady=10)
        
        # Status
        self.status = StatusLabel(bridge_card, status="info", text="⏳ Checking...")
        self.status.pack(pady=10)
        
        # Buttons
        btn_frame = ctk.CTkFrame(bridge_card, fg_color="transparent")
        btn_frame.pack(pady=15)
        
        self.test_btn = ctk.CTkButton(
            btn_frame,
            text="Send Test Event",
            command=self.send_test,
            width=150,
            fg_color=ACCENT
        )
        self.test_btn.grid(row=0, column=0, padx=5)
        
        self.backup_btn = ctk.CTkButton(
            btn_frame,
            text="Push Backup",
            command=self.push_backup,
            width=150,
            fg_color=ACCENT
        )
        self.backup_btn.grid(row=0, column=1, padx=5)
        
        # Output
        self.output = ctk.CTkTextbox(bridge_card, font=mono())
        self.output.pack(fill="both", expand=True, padx=20, pady=10)
        self.output.insert("1.0", "Cloud Bridge Ready\n")
        
        self.after(1000, self.check_health)

    def check_health(self):
        """Check bridge health"""
        def check():
            try:
                health = bridge.health()
                if health.get("status") == "ok":
                    self.after(0, lambda: self.status.set_status("ok", "🟢 Cloud Online"))
                else:
                    self.after(0, lambda: self.status.set_status("warn", "🟡 Degraded"))
            except Exception:
                self.after(0, lambda: self.status.set_status("error", "🔴 Offline"))
        
        threading.Thread(target=check, daemon=True).start()
        self.after(5000, self.check_health)

    def send_test(self):
        """Send test event"""
        self.test_btn.configure(state="disabled")
        self.app.active_operations += 1
        
        def run():
            try:
                result = bridge.send_event("ui_test", {"ts": time.time()})
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.output.insert("end", f"[+] Test event sent: {result.get('ack')}\n")
                    self.test_btn.configure(state="normal")
                
                self.after(0, update_ui)
            except Exception as e:
                def update_ui():
                    self.app.active_operations -= 1
                    self.output.insert("end", f"[x] Failed: {e}\n")
                    self.test_btn.configure(state="normal")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()

    def push_backup(self):
        """Push vector backup"""
        self.backup_btn.configure(state="disabled")
        self.app.active_operations += 1
        
        def run():
            try:
                vector_path = os.path.join(BASE_DIR, "vector_store", "faiss.index")
                if not os.path.exists(vector_path):
                    def update_ui():
                        self.app.active_operations -= 1
                        self.output.insert("end", "[!] No index found\n")
                        self.backup_btn.configure(state="normal")
                    
                    self.after(0, update_ui)
                    return
                
                result = bridge.push_vector_backup(vector_path)
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.output.insert("end", f"[+] Backup complete: {result.get('size')} bytes\n")
                    self.backup_btn.configure(state="normal")
                
                self.after(0, update_ui)
            except Exception as e:
                def update_ui():
                    self.app.active_operations -= 1
                    self.output.insert("end", f"[x] Failed: {e}\n")
                    self.backup_btn.configure(state="normal")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()


class CLO3DTab(ctk.CTkFrame):
    """CLO 3D module placeholder"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        
        title = ctk.CTkLabel(self, text="CLO 3D Integration", font=heading())
        title.pack(pady=20)
        
        card = Card(self)
        card.pack(padx=20, pady=20)
        
        ctk.CTkLabel(
            card,
            text="CLO 3D module features coming soon",
            font=subheading(),
            text_color=TEXT_SECONDARY
        ).pack(pady=50, padx=50)


def exception_hook(exc_type, exc_value, exc_traceback):
    """Top-level exception hook to log uncaught errors"""
    import traceback
    
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_text = "".join(tb_lines)
    
    # Log to file
    log_file = os.path.join(BASE_DIR, "Logs", "app.log")
    try:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, "a", encoding="utf-8") as f:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n{'='*60}\n")
            f.write(f"[{timestamp}] [UNCAUGHT_EXCEPTION]\n")
            f.write(tb_text)
            f.write(f"{'='*60}\n\n")
    except Exception:
        pass
    
    log(f"Uncaught exception: {exc_type.__name__}: {exc_value}", "UI")
    print(f"\n{'='*60}", file=sys.stderr)
    print(f"UNCAUGHT EXCEPTION", file=sys.stderr)
    print(tb_text, file=sys.stderr)
    print(f"{'='*60}\n", file=sys.stderr)


if __name__ == "__main__":
    sys.excepthook = exception_hook
    apply_theme()
    log("UI: Starting RAGGITY ZYZTEM 2.0", "UI")
    
    try:
        app = RaggityUI()
        app.mainloop()
    except Exception as e:
        log(f"UI: Fatal error: {e}", "UI")
        import traceback
        traceback.print_exc()
        sys.exit(1)
