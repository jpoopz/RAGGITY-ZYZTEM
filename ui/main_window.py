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
    """Dashboard with quick actions and live status"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        
        # Title
        title = ctk.CTkLabel(self, text="Dashboard", font=heading())
        title.pack(pady=20)
        
        # Two-column layout
        columns_frame = ctk.CTkFrame(self, fg_color="transparent")
        columns_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Left column: Quick Actions
        left_col = ctk.CTkFrame(columns_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        # Right column: Status
        right_col = ctk.CTkFrame(columns_frame, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))
        
        self.create_quick_actions(left_col)
        self.create_status_panel(right_col)

    def create_quick_actions(self, parent):
        """Create quick actions card"""
        actions_card = Card(parent)
        actions_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(actions_card, text="Quick Actions", font=subheading()).pack(pady=15, padx=20)
        
        # Open Data Folder
        open_data_btn = ctk.CTkButton(
            actions_card,
            text="📁 Open Data Folder",
            command=self.open_data_folder,
            height=45,
            font=body(),
            fg_color=ACCENT,
            anchor="w"
        )
        open_data_btn.pack(pady=5, padx=20, fill="x")
        
        # Rebuild Index
        self.rebuild_btn = ctk.CTkButton(
            actions_card,
            text="🔄 Rebuild Index",
            command=self.rebuild_index,
            height=45,
            font=body(),
            fg_color=ACCENT,
            anchor="w"
        )
        self.rebuild_btn.pack(pady=5, padx=20, fill="x")
        
        # Troubleshoot
        self.troubleshoot_btn = ctk.CTkButton(
            actions_card,
            text="🔧 Run Troubleshoot",
            command=self.run_troubleshoot,
            height=45,
            font=body(),
            fg_color=ACCENT,
            anchor="w"
        )
        self.troubleshoot_btn.pack(pady=5, padx=20, fill="x")
        
        # Action output
        ctk.CTkLabel(actions_card, text="Output", font=body(), text_color=TEXT_SECONDARY).pack(pady=5, padx=20)
        
        self.action_output = ctk.CTkTextbox(actions_card, font=mono(), height=200)
        self.action_output.pack(fill="both", expand=True, padx=20, pady=10)
        self.action_output.insert("1.0", "Ready for actions.\n")

    def create_status_panel(self, parent):
        """Create live status panel"""
        status_card = Card(parent)
        status_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(status_card, text="System Status", font=subheading()).pack(pady=15, padx=20)
        
        # Status display
        self.status_text = ctk.CTkTextbox(status_card, font=mono())
        self.status_text.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Start live updates
        self.after(500, self.update_status_panel)

    def open_data_folder(self):
        """Open data directory in Explorer"""
        try:
            data_dir = CFG.data_dir
            
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)
                self.action_output.insert("end", f"[+] Created: {data_dir}\n")
            
            # Open in Explorer (Windows)
            if sys.platform == "win32":
                os.startfile(data_dir)
                self.action_output.insert("end", f"[→] Opened: {data_dir}\n")
                log(f"UI: Opened data folder: {data_dir}", "UI")
            else:
                # macOS/Linux
                import subprocess
                subprocess.run(["xdg-open", data_dir])
                self.action_output.insert("end", f"[→] Opened: {data_dir}\n")
        except Exception as e:
            self.action_output.insert("end", f"[x] Error: {e}\n")
            log(f"UI: Failed to open data folder: {e}", "UI")

    def rebuild_index(self):
        """Rebuild vector index from data directory"""
        self.rebuild_btn.configure(state="disabled")
        self.action_output.insert("end", "\n[→] Starting index rebuild...\n")
        self.app.active_operations += 1
        
        def run():
            try:
                data_dir = CFG.data_dir
                
                if not os.path.exists(data_dir):
                    def update_ui():
                        self.app.active_operations -= 1
                        self.action_output.insert("end", f"[!] Data directory not found: {data_dir}\n")
                        self.rebuild_btn.configure(state="normal")
                    
                    self.after(0, update_ui)
                    return
                
                # Trigger ingestion
                r = requests.post(
                    "http://localhost:8000/ingest-path",
                    json={"path": data_dir},
                    timeout=120
                )
                
                def update_ui():
                    self.app.active_operations -= 1
                    if r.ok:
                        result = r.json()
                        self.action_output.insert("end", f"[+] Index rebuilt: {result.get('message', 'Success')}\n")
                        log(f"UI: Index rebuilt from {data_dir}", "UI")
                    else:
                        self.action_output.insert("end", f"[x] Error {r.status_code}: {r.text}\n")
                    
                    self.rebuild_btn.configure(state="normal")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: Rebuild index exception: {e}", "UI")
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.action_output.insert("end", f"[x] Error: {e}\n")
                    self.rebuild_btn.configure(state="normal")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()

    def run_troubleshoot(self):
        """Run system troubleshooter"""
        self.troubleshoot_btn.configure(state="disabled")
        self.action_output.insert("end", "\n[→] Running diagnostics...\n")
        self.app.active_operations += 1
        
        def run():
            try:
                r = requests.get(
                    "http://localhost:8000/troubleshoot",
                    params={"hours": 24},
                    timeout=30
                )
                
                def update_ui():
                    self.app.active_operations -= 1
                    if r.ok:
                        result = r.json()
                        summary = result.get("summary", {})
                        
                        self.action_output.insert("end", f"\n=== Diagnostic Results ===\n")
                        self.action_output.insert("end", f"Total Issues: {summary.get('total_issues', 0)}\n")
                        self.action_output.insert("end", f"  Errors: {summary.get('errors', 0)}\n")
                        self.action_output.insert("end", f"  Warnings: {summary.get('warnings', 0)}\n")
                        self.action_output.insert("end", f"  Missing Deps: {summary.get('missing_dependencies', 0)}\n")
                        self.action_output.insert("end", f"Recommendations: {summary.get('recommendations', 0)}\n\n")
                        
                        # Show top 3 recommendations
                        recommendations = result.get("recommendations", [])
                        if recommendations:
                            self.action_output.insert("end", "Top Recommendations:\n")
                            for i, rec in enumerate(recommendations[:3], 1):
                                self.action_output.insert("end", f"  {i}. {rec.get('description', 'N/A')}\n")
                        
                        self.action_output.insert("end", "\n[+] Diagnostics complete\n")
                        log(f"UI: Troubleshoot complete: {summary.get('total_issues', 0)} issues", "UI")
                    else:
                        self.action_output.insert("end", f"[x] Error {r.status_code}\n")
                    
                    self.troubleshoot_btn.configure(state="normal")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: Troubleshoot exception: {e}", "UI")
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.action_output.insert("end", f"[x] Error: {e}\n")
                    self.troubleshoot_btn.configure(state="normal")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()

    def update_status_panel(self):
        """Update status panel with live data"""
        def fetch():
            try:
                status_lines = []
                
                # API Health
                try:
                    r = requests.get("http://localhost:8000/health", timeout=1)
                    if r.ok:
                        status_lines.append("API: ✓ Online\n")
                    else:
                        status_lines.append("API: ✗ Down\n")
                except Exception:
                    status_lines.append("API: ✗ Offline\n")
                
                # GPU Status
                try:
                    gpu = get_gpu_status()
                    if gpu["available"]:
                        name = gpu.get("name", "Unknown")
                        util = gpu.get("utilization", 0)
                        status_lines.append(f"GPU: {name} ({util:.0f}%)\n")
                    else:
                        status_lines.append("GPU: CPU Only\n")
                except Exception:
                    status_lines.append("GPU: Error\n")
                
                status_lines.append("\n")
                
                # Vector Index Size
                try:
                    chunks_file = os.path.join(BASE_DIR, "vector_store", "chunks.json")
                    if os.path.exists(chunks_file):
                        import json
                        with open(chunks_file, 'r', encoding='utf-8') as f:
                            chunks = json.load(f)
                        status_lines.append(f"Vector Index: {len(chunks)} chunks\n")
                    else:
                        status_lines.append("Vector Index: Not built\n")
                except Exception:
                    status_lines.append("Vector Index: Unknown\n")
                
                # Ollama Status
                try:
                    r = requests.get("http://localhost:8000/system-stats", timeout=1)
                    if r.ok:
                        data = r.json()
                        ollama = "Running" if data.get('ollama_running') else "Stopped"
                        status_lines.append(f"Ollama: {ollama}\n")
                except Exception:
                    status_lines.append("Ollama: Unknown\n")
                
                status_lines.append(f"\nVector Store: {CFG.vector_store.upper()}\n")
                status_lines.append(f"Provider: {CFG.provider.upper()}\n")
                status_lines.append(f"Model: {CFG.model_name}\n")
                
                # Latest log lines
                status_lines.append("\n─" * 30 + "\nRecent Logs:\n\n")
                try:
                    log_file = os.path.join(BASE_DIR, "Logs", "app.log")
                    if os.path.exists(log_file):
                        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()[-5:]
                        status_lines.extend(lines)
                except Exception:
                    status_lines.append("No logs available\n")
                
                # Update UI
                content = "".join(status_lines)
                self.after(0, lambda: self.status_text.delete("1.0", "end"))
                self.after(0, lambda: self.status_text.insert("1.0", content))
                
            except Exception as e:
                log(f"UI: Dashboard status update failed: {e}", "UI")
        
        threading.Thread(target=fetch, daemon=True).start()
        self.after(3000, self.update_status_panel)


class IngestTab(ctk.CTkFrame):
    """File ingestion tab with browse, drag-drop, and progress tracking"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        
        # Title
        title = ctk.CTkLabel(self, text="Ingest Documents", font=heading())
        title.pack(pady=20)
        
        # Ingest card
        ingest_card = Card(self)
        ingest_card.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Path entry with drag-drop hint
        ctk.CTkLabel(
            ingest_card,
            text="File or Directory Path",
            font=subheading()
        ).pack(pady=10, padx=20, anchor="w")
        
        # Path entry (drag-drop area)
        self.path_entry = ctk.CTkEntry(
            ingest_card,
            placeholder_text="Paste path or drop file here...",
            height=50,
            font=body()
        )
        self.path_entry.pack(padx=20, pady=10, fill="x")
        
        # Button row
        button_frame = ctk.CTkFrame(ingest_card, fg_color="transparent")
        button_frame.pack(pady=10)
        
        # Browse button
        self.browse_btn = ctk.CTkButton(
            button_frame,
            text="📂 Browse...",
            command=self.browse_file,
            width=130,
            height=40,
            font=body(),
            fg_color=ACCENT
        )
        self.browse_btn.grid(row=0, column=0, padx=5)
        
        # Ingest Path button
        self.ingest_path_btn = ctk.CTkButton(
            button_frame,
            text="📥 Ingest Path",
            command=self.ingest_path,
            width=130,
            height=40,
            font=body(),
            fg_color=ACCENT
        )
        self.ingest_path_btn.grid(row=0, column=1, padx=5)
        
        # Ingest File button
        self.ingest_file_btn = ctk.CTkButton(
            button_frame,
            text="📄 Ingest File",
            command=self.ingest_file,
            width=130,
            height=40,
            font=body(),
            fg_color=ACCENT
        )
        self.ingest_file_btn.grid(row=0, column=2, padx=5)
        
        # Status and index size
        status_frame = ctk.CTkFrame(ingest_card, fg_color="transparent")
        status_frame.pack(pady=10)
        
        self.status = StatusLabel(status_frame, status="info", text="Ready")
        self.status.pack(side="left", padx=10)
        
        self.index_size_label = ctk.CTkLabel(
            status_frame,
            text="Index: 0 chunks",
            font=body(),
            text_color=TEXT_SECONDARY
        )
        self.index_size_label.pack(side="left", padx=10)
        
        # Progress output
        ctk.CTkLabel(
            ingest_card,
            text="Progress Log",
            font=body(),
            text_color=TEXT_SECONDARY
        ).pack(pady=5, padx=20, anchor="w")
        
        self.output = ctk.CTkTextbox(ingest_card, font=mono(), wrap="word")
        self.output.pack(fill="both", expand=True, padx=20, pady=10)
        self.output.insert("1.0", "Ready to ingest documents.\n")
        
        # Update index size on init
        self.after(500, self.update_index_size)

    def browse_file(self):
        """Open file/folder browser dialog"""
        from tkinter import filedialog
        
        # Ask if file or folder
        choice = filedialog.askdirectory(title="Select Folder to Ingest")
        
        if not choice:
            # Try file dialog instead
            choice = filedialog.askopenfilename(
                title="Select File to Ingest",
                filetypes=[
                    ("Text files", "*.txt"),
                    ("PDF files", "*.pdf"),
                    ("All files", "*.*")
                ]
            )
        
        if choice:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, choice)
            self.log_progress(f"Selected: {choice}")

    def ingest_path(self):
        """Ingest path (file or directory)"""
        path = self.path_entry.get().strip('" ')
        
        if not path or not os.path.exists(path):
            self.log_progress(f"[!] Invalid path: {path}", is_error=True)
            self.status.set_status("error", "✗ Invalid Path")
            return
        
        self._do_ingest(path, is_file=False)

    def ingest_file(self):
        """Ingest single file via upload"""
        path = self.path_entry.get().strip('" ')
        
        if not path or not os.path.isfile(path):
            self.log_progress(f"[!] Not a file: {path}", is_error=True)
            self.status.set_status("error", "✗ Not a File")
            return
        
        self._do_ingest(path, is_file=True)

    def _do_ingest(self, path: str, is_file: bool = False):
        """Common ingestion logic"""
        # Disable buttons
        self.ingest_path_btn.configure(state="disabled")
        self.ingest_file_btn.configure(state="disabled")
        self.browse_btn.configure(state="disabled")
        
        self.status.set_status("info", "⏳ Ingesting...")
        self.log_progress(f"[→] Starting ingestion: {path}")
        self.app.active_operations += 1
        
        def run():
            try:
                if is_file:
                    # Upload file
                    with open(path, 'rb') as f:
                        files = {'f': (os.path.basename(path), f)}
                        r = requests.post(
                            "http://localhost:8000/ingest-file",
                            files=files,
                            timeout=120
                        )
                else:
                    # Ingest path
                    r = requests.post(
                        "http://localhost:8000/ingest-path",
                        json={"path": path},
                        timeout=120
                    )
                
                def update_ui():
                    self.app.active_operations -= 1
                    if r.ok:
                        result = r.json()
                        self.log_progress(f"[+] Success! {result.get('message', 'Ingested')}")
                        self.status.set_status("ok", "✓ Complete")
                        
                        # Update index size
                        self.update_index_size()
                    else:
                        self.log_progress(f"[x] Error {r.status_code}: {r.text[:100]}", is_error=True)
                        self.status.set_status("error", "✗ Failed")
                    
                    # Re-enable buttons
                    self.ingest_path_btn.configure(state="normal")
                    self.ingest_file_btn.configure(state="normal")
                    self.browse_btn.configure(state="normal")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: Ingestion exception: {e}", "UI")
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.log_progress(f"[x] Error: {e}", is_error=True)
                    self.status.set_status("error", "✗ Error")
                    
                    # Re-enable buttons
                    self.ingest_path_btn.configure(state="normal")
                    self.ingest_file_btn.configure(state="normal")
                    self.browse_btn.configure(state="normal")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()

    def log_progress(self, message: str, is_error: bool = False):
        """Append timestamped message to progress log"""
        timestamp = time.strftime("%H:%M:%S")
        prefix = "[ERROR]" if is_error else "[INFO]"
        self.output.insert("end", f"[{timestamp}] {prefix} {message}\n")
        self.output.see("end")  # Auto-scroll to bottom

    def update_index_size(self):
        """Update index size display"""
        def fetch():
            try:
                chunks_file = os.path.join(BASE_DIR, "vector_store", "chunks.json")
                if os.path.exists(chunks_file):
                    import json
                    with open(chunks_file, 'r', encoding='utf-8') as f:
                        chunks = json.load(f)
                    
                    count = len(chunks)
                    self.after(0, lambda: self.index_size_label.configure(
                        text=f"Index: {count:,} chunks"
                    ))
                else:
                    self.after(0, lambda: self.index_size_label.configure(
                        text="Index: Not built"
                    ))
            except Exception as e:
                log(f"UI: Failed to read index size: {e}", "UI")
        
        threading.Thread(target=fetch, daemon=True).start()


class QueryTab(ctk.CTkFrame):
    """Query interface with rich answer card and export"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        self.current_answer = ""
        self.current_question = ""
        self.current_contexts = []
        self.contexts_expanded = False
        
        # Title
        title = ctk.CTkLabel(self, text="Query Knowledge Base", font=heading())
        title.pack(pady=20)
        
        # Query card
        query_card = Card(self)
        query_card.pack(padx=20, pady=10, fill="x")
        
        # Query input
        ctk.CTkLabel(query_card, text="Ask a Question", font=subheading()).pack(pady=10, padx=20, anchor="w")
        
        # Multi-line text box for query
        self.query_input = ctk.CTkTextbox(
            query_card,
            height=80,
            font=body(),
            wrap="word"
        )
        self.query_input.pack(padx=20, pady=10, fill="x")
        self.query_input.insert("1.0", "")
        self.query_input.bind("<Control-Return>", lambda e: self.submit_query())
        
        # Hint text
        ctk.CTkLabel(
            query_card,
            text="Tip: Press Ctrl+Enter to submit",
            font=small(),
            text_color=TEXT_SECONDARY
        ).pack(padx=20, anchor="w")
        
        # Submit button
        self.query_btn = ctk.CTkButton(
            query_card,
            text="🔍 Submit Query",
            command=self.submit_query,
            height=40,
            font=subheading(),
            fg_color=ACCENT
        )
        self.query_btn.pack(pady=10)
        
        # Status
        self.status = StatusLabel(query_card, status="info", text="Ready")
        self.status.pack(pady=5)
        
        # Answer card
        answer_card = Card(self)
        answer_card.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Answer header with actions
        header_frame = ctk.CTkFrame(answer_card, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(header_frame, text="Answer", font=subheading()).pack(side="left")
        
        # Export buttons
        self.copy_btn = ctk.CTkButton(
            header_frame,
            text="📋 Copy",
            command=self.copy_answer,
            width=100,
            height=30,
            font=body(),
            state="disabled"
        )
        self.copy_btn.pack(side="right", padx=5)
        
        self.export_btn = ctk.CTkButton(
            header_frame,
            text="💾 Export MD",
            command=self.export_to_markdown,
            width=120,
            height=30,
            font=body(),
            state="disabled"
        )
        self.export_btn.pack(side="right", padx=5)
        
        # Answer text
        self.answer_box = ctk.CTkTextbox(answer_card, font=body(), wrap="word", height=200)
        self.answer_box.pack(fill="x", padx=20, pady=5)
        self.answer_box.insert("1.0", "Your answer will appear here.\n")
        
        # Contexts section
        self.contexts_toggle_btn = ctk.CTkButton(
            answer_card,
            text="▼ Show Contexts (0)",
            command=self.toggle_contexts,
            height=30,
            font=body(),
            fg_color="transparent",
            hover_color="#1a1a1e",
            state="disabled"
        )
        self.contexts_toggle_btn.pack(pady=5)
        
        # Contexts display (initially hidden)
        self.contexts_box = ctk.CTkTextbox(answer_card, font=mono(), wrap="word", height=0)
        self.contexts_box.pack(fill="both", expand=True, padx=20, pady=5)
        self.contexts_box.pack_forget()  # Hidden by default

    def submit_query(self):
        """Submit query (non-blocking)"""
        q = self.query_input.get("1.0", "end").strip()
        if not q:
            return
        
        self.current_question = q
        self.query_btn.configure(state="disabled")
        self.copy_btn.configure(state="disabled")
        self.export_btn.configure(state="disabled")
        self.contexts_toggle_btn.configure(state="disabled")
        
        self.status.set_status("info", "💭 Thinking...")
        self.answer_box.delete("1.0", "end")
        self.answer_box.insert("1.0", "⏳ Processing your question...\n\nThis may take a moment.")
        
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
                        answer_text = ans.get('answer', 'No answer')
                        contexts = ans.get("contexts", [])
                        
                        # Store for export
                        self.current_answer = answer_text
                        self.current_contexts = contexts
                        
                        # Display answer
                        self.answer_box.delete("1.0", "end")
                        self.answer_box.insert("end", answer_text)
                        
                        # Update contexts button
                        self.contexts_toggle_btn.configure(
                            text=f"▼ Show Contexts ({len(contexts)})",
                            state="normal"
                        )
                        
                        # Populate contexts (hidden)
                        self.contexts_box.delete("1.0", "end")
                        for i, ctx in enumerate(contexts, 1):
                            self.contexts_box.insert("end", f"─" * 50 + f"\nContext {i}:\n\n")
                            self.contexts_box.insert("end", f"{ctx[:400]}...\n\n")
                        
                        self.status.set_status("ok", f"✓ Answer ready ({len(contexts)} contexts)")
                        
                        # Enable export buttons
                        self.copy_btn.configure(state="normal")
                        self.export_btn.configure(state="normal")
                        
                        log(f"UI: Query successful: {q[:100]}", "UI")
                    else:
                        self.answer_box.delete("1.0", "end")
                        self.answer_box.insert("end", f"Error {r.status_code}\n\n{r.text}")
                        self.status.set_status("error", "✗ Query Failed")
                    
                    self.query_btn.configure(state="normal")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: Query exception: {e}", "UI")
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.answer_box.delete("1.0", "end")
                    self.answer_box.insert("end", f"Connection Error\n\n{str(e)}")
                    self.status.set_status("error", "✗ Connection Error")
                    self.query_btn.configure(state="normal")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()

    def toggle_contexts(self):
        """Toggle contexts panel visibility"""
        if self.contexts_expanded:
            # Collapse
            self.contexts_box.pack_forget()
            self.contexts_toggle_btn.configure(text=f"▼ Show Contexts ({len(self.current_contexts)})")
            self.contexts_expanded = False
        else:
            # Expand
            self.contexts_box.pack(fill="both", expand=True, padx=20, pady=5)
            self.contexts_toggle_btn.configure(text=f"▲ Hide Contexts ({len(self.current_contexts)})")
            self.contexts_expanded = True

    def copy_answer(self):
        """Copy answer to clipboard"""
        try:
            # Copy to clipboard
            self.clipboard_clear()
            self.clipboard_append(self.current_answer)
            
            # Show feedback
            original_text = self.copy_btn.cget("text")
            self.copy_btn.configure(text="✓ Copied!")
            
            # Reset after 2 seconds
            self.after(2000, lambda: self.copy_btn.configure(text=original_text))
            
            log("UI: Answer copied to clipboard", "UI")
        except Exception as e:
            log(f"UI: Copy failed: {e}", "UI")
            self.status.set_status("error", "✗ Copy Failed")

    def export_to_markdown(self):
        """Export Q&A to Markdown file"""
        try:
            # Create exports directory
            export_dir = os.path.join(BASE_DIR, "exports")
            os.makedirs(export_dir, exist_ok=True)
            
            # Generate filename
            timestamp = time.strftime("%Y%m%d-%H%M")
            filename = f"{timestamp}-qa.md"
            filepath = os.path.join(export_dir, filename)
            
            # Build markdown content
            md_content = f"# RAG Query Export\n\n"
            md_content += f"**Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            md_content += f"---\n\n"
            md_content += f"## Question\n\n{self.current_question}\n\n"
            md_content += f"## Answer\n\n{self.current_answer}\n\n"
            
            if self.current_contexts:
                md_content += f"---\n\n## Contexts ({len(self.current_contexts)})\n\n"
                for i, ctx in enumerate(self.current_contexts, 1):
                    md_content += f"### Context {i}\n\n```\n{ctx}\n```\n\n"
            
            md_content += f"---\n\n"
            md_content += f"*Generated by RAGGITY ZYZTEM 2.0*\n"
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            # Show feedback
            original_text = self.export_btn.cget("text")
            self.export_btn.configure(text="✓ Exported!")
            self.after(2000, lambda: self.export_btn.configure(text=original_text))
            
            # Log with clickable path
            self.status.set_status("ok", f"✓ Saved to exports/{filename}")
            log(f"UI: Exported to {filepath}", "UI")
            
        except Exception as e:
            log(f"UI: Export failed: {e}", "UI")
            self.status.set_status("error", "✗ Export Failed")


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
