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
    apply_theme, heading, subheading, body, mono, small, Card, StatusLabel,
    ACCENT, TEXT, TEXT_SECONDARY, STATUS_OK, STATUS_WARN, STATUS_ERROR, STATUS_WARNING,
    STATUS_INFO, DARK_BG, CARD_BG
)
from ui.toast import ToastManager
from ui.palette import CommandPalette
from core.gpu import get_gpu_status
from core.config import CFG
from logger import log

# Import version
try:
    from version import __version__, CODENAME
except ImportError:
    __version__ = "2.0.0"
    CODENAME = "Luxe Edition"

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
        # Load UI config
        try:
            import json, os
            self._ui_cfg_path = os.path.join(os.path.dirname(__file__), "config.json")
            if os.path.exists(self._ui_cfg_path):
                with open(self._ui_cfg_path, "r", encoding="utf-8") as f:
                    self._ui_cfg = json.load(f)
            else:
                self._ui_cfg = {}
        except Exception:
            self._ui_cfg = {}

        self.geometry(self._ui_cfg.get("main_geometry", "1200x750"))
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Network operation counter for spinner
        self.active_operations = 0
        
        # Toast notification manager
        self.toast = ToastManager(self)
        
        # Create layout
        self.create_app_bar()
        
        # Main container with sidebar + content
        main_container = ctk.CTkFrame(self, fg_color=DARK_BG)
        main_container.pack(fill="both", expand=True)
        
        self.sidebar = Sidebar(self, main_container)
        self.sidebar.pack(side="left", fill="y")
        
        self.content = ContentArea(self, main_container)
        self.content.pack(side="right", fill="both", expand=True)
        
        # Now select the default tab (after both sidebar and content are created)
        self.sidebar.select_tab("Dashboard")
        
        # Bind command palette
        self.bind("<Control-k>", lambda e: self.open_command_palette())
        self.bind("<Control-K>", lambda e: self.open_command_palette())
        
        # Start status updates
        self.after(2000, self.update_status)
        self.after(500, self.update_spinner)

        # External windows
        self._clo_window = None

        # Restore last tab
        last_tab = self._ui_cfg.get("last_open_tab", "Dashboard")
        try:
            self.sidebar.select_tab(last_tab)
        except Exception:
            self.sidebar.select_tab("Dashboard")

    def open_clo_tool(self):
        try:
            # Lazy import to avoid hard dependency at startup
            from ui.clo_tool_window import CLOToolWindow
        except Exception as e:
            self.toast.show("CLO tool not available", "error")
            return
        if self._clo_window and self._clo_window.winfo_exists():
            try:
                self._clo_window.focus()
                self._clo_window.lift()
            except Exception:
                pass
            return
        self._clo_window = CLOToolWindow(self)
        try:
            self._clo_window.lift()
            self._clo_window.focus()
        except Exception:
            pass

    def _save_ui_cfg(self):
        try:
            os.makedirs(os.path.dirname(self._ui_cfg_path), exist_ok=True)
            with open(self._ui_cfg_path, "w", encoding="utf-8") as f:
                json.dump(self._ui_cfg, f, indent=2)
        except Exception:
            pass
    def create_app_bar(self):
        """Create top app bar with status indicators"""
        self.app_bar = ctk.CTkFrame(self, height=50, fg_color="#0a0a0c")
        self.app_bar.pack(fill="x", padx=0, pady=0)
        self.app_bar.pack_propagate(False)
        
        # App title with version
        title = ctk.CTkLabel(
            self.app_bar,
            text=f"⚙️ RAGGITY ZYZTEM {__version__}",
            font=heading(),
            text_color=ACCENT
        )
        title.pack(side="left", padx=20)
        
        # Codename subtitle
        codename_label = ctk.CTkLabel(
            self.app_bar,
            text=f"// {CODENAME}",
            font=small(),
            text_color=TEXT_SECONDARY
        )
        codename_label.pack(side="left", padx=(0, 20))
        
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

    def open_command_palette(self):
        """Open command palette with Ctrl+K - grouped by category"""
        commands = [
            # General actions
            {
                "name": "Open Data Folder",
                "action": self.open_data_folder,
                "category": "General",
                "description": "Browse data directory in file explorer"
            },
            {
                "name": "Open Logs Folder",
                "action": self.open_logs_folder,
                "category": "General",
                "description": "Browse logs directory"
            },
            {
                "name": "Open Exports Folder",
                "action": self.open_exports_folder,
                "category": "General",
                "description": "Browse exported files"
            },
            
            # RAG operations
            {
                "name": "Ingest Documents",
                "action": lambda: self.sidebar.select_tab("Ingest"),
                "category": "RAG",
                "description": "Add documents to knowledge base"
            },
            {
                "name": "Query Knowledge Base",
                "action": lambda: self.sidebar.select_tab("Query"),
                "category": "RAG",
                "description": "Ask questions about documents"
            },
            {
                "name": "Rebuild Index",
                "action": self.rebuild_index,
                "category": "RAG",
                "description": "Reindex all documents from scratch"
            },
            {
                "name": "Clear Vector Store",
                "action": self.clear_vector_store,
                "category": "RAG",
                "description": "Delete all indexed data (destructive)"
            },
            
            # CLO3D
            {
                "name": "Connect to CLO3D",
                "action": lambda: self.sidebar.select_tab("CLO3D"),
                "category": "CLO3D",
                "description": "Manage CLO 3D bridge connection"
            },
            {
                "name": "CLO3D Help",
                "action": self.show_clo_help,
                "category": "CLO3D",
                "description": "View CLO integration setup guide"
            },
            
            # Cloud Bridge
            {
                "name": "Cloud Bridge Status",
                "action": lambda: self.sidebar.select_tab("Bridge"),
                "category": "Bridge",
                "description": "View cloud connection and backups"
            },
            {
                "name": "Push Vector Backup",
                "action": self.push_backup,
                "category": "Bridge",
                "description": "Backup vector store to cloud"
            },
            
            # System & Diagnostics
            {
                "name": "System Monitor",
                "action": lambda: self.sidebar.select_tab("System"),
                "category": "System",
                "description": "View CPU/RAM/GPU metrics"
            },
            {
                "name": "Take System Snapshot",
                "action": self.take_snapshot,
                "category": "System",
                "description": "Save current metrics to JSON"
            },
            {
                "name": "Run Troubleshooter",
                "action": self.run_troubleshooter,
                "category": "System",
                "description": "Analyze logs for errors and fixes"
            },
            {
                "name": "View Logs",
                "action": lambda: self.sidebar.select_tab("Logs"),
                "category": "System",
                "description": "View application logs"
            },
            
            # Settings & Help
            {
                "name": "Settings",
                "action": lambda: self.sidebar.select_tab("Settings"),
                "category": "Settings",
                "description": "Configure vector store, models, theme"
            },
            {
                "name": "Migrate Legacy Settings",
                "action": self.migrate_settings,
                "category": "Settings",
                "description": "Import settings from old config files"
            },
            {
                "name": "View README",
                "action": self.open_readme,
                "category": "Help",
                "description": "Open documentation in browser"
            },
        ]
        
        CommandPalette(self, commands)
    
    def open_data_folder(self):
        """Open data folder in file explorer"""
        try:
            data_dir = CFG.data_dir
            os.makedirs(data_dir, exist_ok=True)
            
            if os.name == 'nt':
                os.startfile(data_dir)
            elif os.name == 'posix':
                import subprocess
                if sys.platform == 'darwin':
                    subprocess.Popen(['open', data_dir])
                else:
                    subprocess.Popen(['xdg-open', data_dir])
            
            self.toast.show("Data folder opened", "success")
        except Exception as e:
            log(f"UI: Failed to open data folder: {e}", "UI")
            self.toast.show("Failed to open data folder", "error")
    
    def open_logs_folder(self):
        """Open logs folder in file explorer"""
        try:
            logs_dir = os.path.join(BASE_DIR, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            if os.name == 'nt':
                os.startfile(logs_dir)
            elif os.name == 'posix':
                import subprocess
                if sys.platform == 'darwin':
                    subprocess.Popen(['open', logs_dir])
                else:
                    subprocess.Popen(['xdg-open', logs_dir])
            
            self.toast.show("Logs folder opened", "success")
        except Exception as e:
            log(f"UI: Failed to open logs folder: {e}", "UI")
            self.toast.show("Failed to open logs folder", "error")
    
    def rebuild_index(self):
        """Trigger index rebuild"""
        try:
            data_dir = CFG.data_dir
            
            def run():
                try:
                    r = requests.post(
                        "http://localhost:8000/ingest-path",
                        params={"path": data_dir},
                        timeout=120
                    )
                    
                    def update_ui():
                        if r.ok:
                            self.toast.show("Index rebuild started", "success")
                        else:
                            self.toast.show("Rebuild failed", "error")
                    
                    self.after(0, update_ui)
                except Exception as e:
                    log(f"UI: Rebuild error: {e}", "UI")
                    self.after(0, lambda: self.toast.show("Rebuild error", "error"))
            
            threading.Thread(target=run, daemon=True).start()
        except Exception as e:
            log(f"UI: Failed to start rebuild: {e}", "UI")
            self.toast.show("Failed to start rebuild", "error")
    
    def run_troubleshooter(self):
        """Run troubleshooter"""
        try:
            def run():
                try:
                    r = requests.get("http://localhost:8000/troubleshoot", timeout=30)
                    
                    def update_ui():
                        if r.ok:
                            self.toast.show("Troubleshooter complete", "success")
                            # Switch to logs to see results
                            self.sidebar.select_tab("Logs")
                        else:
                            self.toast.show("Troubleshooter failed", "error")
                    
                    self.after(0, update_ui)
                except Exception as e:
                    log(f"UI: Troubleshooter error: {e}", "UI")
                    self.after(0, lambda: self.toast.show("Troubleshooter error", "error"))
            
            threading.Thread(target=run, daemon=True).start()
        except Exception as e:
            log(f"UI: Failed to run troubleshooter: {e}", "UI")
            self.toast.show("Failed to run troubleshooter", "error")
    
    def open_exports_folder(self):
        """Open exports folder"""
        try:
            exports_dir = os.path.join(BASE_DIR, "exports")
            os.makedirs(exports_dir, exist_ok=True)
            
            if os.name == 'nt':
                os.startfile(exports_dir)
            else:
                import subprocess
                subprocess.Popen(['xdg-open' if sys.platform != 'darwin' else 'open', exports_dir])
            
            self.toast.show("Exports folder opened", "success")
        except Exception as e:
            log(f"UI: Failed to open exports folder: {e}", "UI")
            self.toast.show("Failed to open exports folder", "error")
    
    def clear_vector_store(self):
        """Clear vector store (destructive)"""
        # TODO: Add confirmation dialog
        self.toast.show("Feature not yet implemented", "warn")
    
    def show_clo_help(self):
        """Show CLO3D help"""
        try:
            readme_path = os.path.join(BASE_DIR, "modules", "clo_companion", "README.md")
            if os.path.exists(readme_path):
                if os.name == 'nt':
                    os.startfile(readme_path)
                else:
                    import subprocess
                    subprocess.Popen(['xdg-open' if sys.platform != 'darwin' else 'open', readme_path])
                self.toast.show("CLO help opened", "success")
            else:
                self.toast.show("CLO README not found", "error")
        except Exception as e:
            log(f"UI: Failed to open CLO help: {e}", "UI")
            self.toast.show("Failed to open help", "error")
    
    def push_backup(self):
        """Push vector backup via palette"""
        self.sidebar.select_tab("Bridge")
        self.toast.show("Go to Bridge tab to push backup", "info")
    
    def take_snapshot(self):
        """Take system snapshot via palette"""
        self.sidebar.select_tab("System")
        self.toast.show("Go to System tab to take snapshot", "info")
    
    def migrate_settings(self):
        """Migrate legacy settings"""
        # TODO: Call /settings/migrate endpoint
        self.sidebar.select_tab("Settings")
        self.toast.show("Go to Settings tab for migration", "info")
    
    def open_readme(self):
        """Open README in browser"""
        try:
            readme_path = os.path.join(BASE_DIR, "README.md")
            if os.path.exists(readme_path):
                if os.name == 'nt':
                    os.startfile(readme_path)
                else:
                    import subprocess
                    subprocess.Popen(['xdg-open' if sys.platform != 'darwin' else 'open', readme_path])
                self.toast.show("README opened", "success")
            else:
                self.toast.show("README not found", "error")
        except Exception as e:
            log(f"UI: Failed to open README: {e}", "UI")
            self.toast.show("Failed to open README", "error")
    
    def on_close(self):
        """Handle window close"""
        log("UI: Window closing", "UI")
        try:
            self._ui_cfg["main_geometry"] = self.geometry()
            self._save_ui_cfg()
        except Exception:
            pass
        self.destroy()


class Sidebar(ctk.CTkFrame):
    """Icon-based sidebar navigation with collapse support"""
    
    def __init__(self, app, parent):
        super().__init__(parent, width=180, fg_color="#0a0a0c")
        self.pack_propagate(False)
        self.app = app
        self.collapsed = False
        self.expanded_width = 180
        self.collapsed_width = 60
        
        # Navigation items with icons
        self.nav_items = [
            ("📊", "Dashboard"),
            ("📥", "Ingest"),
            ("💬", "Query"),
            ("🖥️", "System"),
            ("⚙️", "Settings"),
            ("📜", "Logs"),
            ("☁️", "Bridge"),
            ("👗", "CLO3D")
        ]
        
        self.buttons = []
        self.active_button = None
        
        # Collapse/expand toggle button at top
        self.toggle_btn = ctk.CTkButton(
            self,
            text="◀",
            command=self.toggle_collapse,
            width=40,
            height=30,
            fg_color="transparent",
            hover_color="#1a1a1e",
            font=("Segoe UI", 16)
        )
        self.toggle_btn.pack(pady=10, padx=5, anchor="e")
        
        # Add spacing
        ctk.CTkLabel(self, text="", height=10).pack()
        
        # Create navigation buttons
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
            self.buttons.append((name, btn, icon))
        
        # Note: Default tab selection happens in RaggityUI.__init__ after content is created
    
    def toggle_collapse(self):
        """Toggle sidebar between collapsed and expanded"""
        self.collapsed = not self.collapsed
        
        if self.collapsed:
            # Collapse to icon-only
            self.configure(width=self.collapsed_width)
            self.toggle_btn.configure(text="▶")
            
            # Update buttons to icon-only
            for tab_name, btn, icon in self.buttons:
                btn.configure(text=icon, width=40)
        else:
            # Expand to full width
            self.configure(width=self.expanded_width)
            self.toggle_btn.configure(text="◀")
            
            # Update buttons to icon + text
            for tab_name, btn, icon in self.buttons:
                btn.configure(text=f"{icon}  {tab_name}", width=None)
    
    def select_tab(self, name):
        """Select a tab and update button styling"""
        # Reset all buttons
        for tab_name, btn, icon in self.buttons:
            if tab_name == name:
                btn.configure(fg_color=ACCENT, text_color="white")
                self.active_button = btn
            else:
                btn.configure(fg_color="transparent", text_color=TEXT_SECONDARY)
        
        # Show tab in content area
        self.app.content.show_tab(name)
        # Persist last open tab
        try:
            self.app._ui_cfg["last_open_tab"] = name
            self.app._ui_cfg["main_geometry"] = self.app.geometry()
            self.app._save_ui_cfg()
        except Exception:
            pass




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
            "Settings": SettingsTab(self, app),
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
        
        # Simple landing: three primary cards
        title = ctk.CTkLabel(self, text="Dashboard", font=heading())
        title.pack(pady=(20,10))
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=20, pady=10)

        self._card_rag = Card(grid)
        self._card_rag.pack(fill="x", padx=4, pady=8)
        ctk.CTkLabel(self._card_rag, text="RAG Chat", font=subheading()).pack(anchor="w", padx=16, pady=(14,0))
        ctk.CTkLabel(self._card_rag, text="Ask your knowledge base with sources.", font=body(), text_color=TEXT_SECONDARY).pack(anchor="w", padx=16, pady=(2,10))
        self._rag_badge = ctk.CTkLabel(self._card_rag, text="Status: …", font=small(), text_color=TEXT_SECONDARY)
        self._rag_badge.pack(anchor="w", padx=16)
        ctk.CTkButton(self._card_rag, text="Open RAG Chat", height=44, command=lambda: self.app.sidebar.select_tab("Query")).pack(padx=16, pady=14)

        self._card_clo = Card(grid)
        self._card_clo.pack(fill="x", padx=4, pady=8)
        ctk.CTkLabel(self._card_clo, text="CLO3D Tool", font=subheading()).pack(anchor="w", padx=16, pady=(14,0))
        ctk.CTkLabel(self._card_clo, text="Control the CLO Bridge and run actions.", font=body(), text_color=TEXT_SECONDARY).pack(anchor="w", padx=16, pady=(2,10))
        self._clo_badge = ctk.CTkLabel(self._card_clo, text="Status: …", font=small(), text_color=TEXT_SECONDARY)
        self._clo_badge.pack(anchor="w", padx=16)
        ctk.CTkButton(self._card_clo, text="Open CLO3D Tool", height=44, command=self.app.open_clo_tool).pack(padx=16, pady=14)

        self._card_diag = Card(grid)
        self._card_diag.pack(fill="x", padx=4, pady=8)
        ctk.CTkLabel(self._card_diag, text="Diagnostics", font=subheading()).pack(anchor="w", padx=16, pady=(14,0))
        ctk.CTkLabel(self._card_diag, text="Check health and run quick checks.", font=body(), text_color=TEXT_SECONDARY).pack(anchor="w", padx=16, pady=(2,10))
        self._diag_badge = ctk.CTkLabel(self._card_diag, text="Status: …", font=small(), text_color=TEXT_SECONDARY)
        self._diag_badge.pack(anchor="w", padx=16)
        link = ctk.CTkButton(self._card_diag, text="Run quick check", height=34, fg_color=ACCENT, command=self._run_quick_check)
        link.pack(padx=16, pady=14)

        # Start polling unified health
        self.after(1000, self._poll_health_full)

    def _run_quick_check(self):
        try:
            threading.Thread(target=lambda: requests.get("http://127.0.0.1:8000/troubleshoot", timeout=10), daemon=True).start()
            self.app.toast.show("Diagnostics started", "info")
        except Exception:
            self.app.toast.show("Diagnostics failed to start", "error")

    def _poll_health_full(self):
        def run():
            try:
                r = requests.get("http://127.0.0.1:8000/health/full", timeout=1.2)
                if r.ok:
                    h = r.json()
                    clo_ok = h.get("clo", {}).get("ok")
                    api_ok = h.get("api", {}).get("ok")
                    vs = h.get("vector_store", "?")
                    self.after(0, lambda: self._rag_badge.configure(text=f"API: {'✓' if api_ok else '✗'}  VS: {vs}"))
                    self.after(0, lambda: self._clo_badge.configure(text=f"CLO: {'✓' if clo_ok else '✗'}"))
                    self.after(0, lambda: self._diag_badge.configure(text=f"RAM free: {h.get('sys',{}).get('ram_free_gb',0)} GB"))
            except Exception:
                pass
            finally:
                self.after(10000, self._poll_health_full)
        threading.Thread(target=run, daemon=True).start()

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
        self.last_query_time = 0  # For debouncing
        self.debounce_ms = 500  # Minimum time between queries
        
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
        """Submit query (non-blocking) with debouncing"""
        q = self.query_input.get("1.0", "end").strip()
        if not q:
            return
        
        # Debounce: prevent rapid-fire queries
        current_time = time.time() * 1000  # Convert to milliseconds
        if current_time - self.last_query_time < self.debounce_ms:
            self.app.toast.show("Please wait before submitting another query", "warn", ms=1500)
            return
        
        self.last_query_time = current_time
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
                        
                        self.app.toast.show(f"Query complete ({len(contexts)} contexts)", "success")
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
            
            self.app.toast.show("Answer copied to clipboard", "success", ms=1500)
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
            self.app.toast.show(f"Exported to {filename}", "success")
            log(f"UI: Exported to {filepath}", "UI")
            
        except Exception as e:
            log(f"UI: Export failed: {e}", "UI")
            self.status.set_status("error", "✗ Export Failed")


class SystemTab(ctk.CTkFrame):
    """System monitor with visual meters and snapshot"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        self.current_stats = {}
        
        # Title
        title = ctk.CTkLabel(self, text="System Monitor", font=heading())
        title.pack(pady=20)
        
        # System card
        system_card = Card(self)
        system_card.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Header with snapshot button
        header_frame = ctk.CTkFrame(system_card, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(header_frame, text="Resource Usage", font=subheading()).pack(side="left")
        
        self.snapshot_btn = ctk.CTkButton(
            header_frame,
            text="📸 Take Snapshot",
            command=self.take_snapshot,
            width=150,
            height=30,
            font=body()
        )
        self.snapshot_btn.pack(side="right", padx=5)
        
        # Metrics container
        metrics_frame = ctk.CTkFrame(system_card, fg_color="transparent")
        metrics_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # CPU Section
        cpu_section = ctk.CTkFrame(metrics_frame, fg_color=CARD_BG, corner_radius=8)
        cpu_section.pack(fill="x", pady=10)
        
        ctk.CTkLabel(cpu_section, text="🖥️ CPU", font=subheading()).pack(pady=10, padx=20, anchor="w")
        
        self.cpu_label = ctk.CTkLabel(cpu_section, text="0.0%", font=body(), text_color=TEXT_SECONDARY)
        self.cpu_label.pack(padx=20, anchor="w")
        
        self.cpu_bar = ctk.CTkProgressBar(cpu_section, width=400, height=20)
        self.cpu_bar.pack(padx=20, pady=10, fill="x")
        self.cpu_bar.set(0)
        
        # RAM Section
        ram_section = ctk.CTkFrame(metrics_frame, fg_color=CARD_BG, corner_radius=8)
        ram_section.pack(fill="x", pady=10)
        
        ctk.CTkLabel(ram_section, text="💾 Memory", font=subheading()).pack(pady=10, padx=20, anchor="w")
        
        self.ram_label = ctk.CTkLabel(ram_section, text="0.0%", font=body(), text_color=TEXT_SECONDARY)
        self.ram_label.pack(padx=20, anchor="w")
        
        self.ram_bar = ctk.CTkProgressBar(ram_section, width=400, height=20)
        self.ram_bar.pack(padx=20, pady=10, fill="x")
        self.ram_bar.set(0)
        
        # GPU Section
        gpu_section = ctk.CTkFrame(metrics_frame, fg_color=CARD_BG, corner_radius=8)
        gpu_section.pack(fill="x", pady=10)
        
        ctk.CTkLabel(gpu_section, text="🎮 GPU", font=subheading()).pack(pady=10, padx=20, anchor="w")
        
        self.gpu_name_label = ctk.CTkLabel(gpu_section, text="No GPU detected", font=small(), text_color=TEXT_SECONDARY)
        self.gpu_name_label.pack(padx=20, anchor="w")
        
        self.gpu_util_label = ctk.CTkLabel(gpu_section, text="Utilization: 0%", font=body(), text_color=TEXT_SECONDARY)
        self.gpu_util_label.pack(padx=20, anchor="w")
        
        self.gpu_util_bar = ctk.CTkProgressBar(gpu_section, width=400, height=20)
        self.gpu_util_bar.pack(padx=20, pady=5, fill="x")
        self.gpu_util_bar.set(0)
        
        self.gpu_vram_label = ctk.CTkLabel(gpu_section, text="VRAM: 0 MB / 0 MB", font=body(), text_color=TEXT_SECONDARY)
        self.gpu_vram_label.pack(padx=20, anchor="w")
        
        self.gpu_vram_bar = ctk.CTkProgressBar(gpu_section, width=400, height=20)
        self.gpu_vram_bar.pack(padx=20, pady=10, fill="x")
        self.gpu_vram_bar.set(0)
        
        # Status
        self.status = StatusLabel(system_card, status="info", text="Connecting...")
        self.status.pack(pady=10)
        
        # Update stats periodically
        self.after(1000, self.update_stats)

    def update_stats(self):
        """Fetch and display system stats (non-blocking)"""
        def run():
            try:
                r = requests.get("http://localhost:8000/system-stats", timeout=5)
                
                def update_ui():
                    if r.ok:
                        try:
                            stats = r.json()
                            self.current_stats = stats
                            
                            # Update CPU
                            cpu_percent = stats.get("cpu_percent", 0)
                            self.cpu_label.configure(text=f"{cpu_percent:.1f}%")
                            self.cpu_bar.set(cpu_percent / 100.0)
                            
                            # Color code based on usage
                            if cpu_percent > 80:
                                self.cpu_bar.configure(progress_color=STATUS_ERROR)
                            elif cpu_percent > 60:
                                self.cpu_bar.configure(progress_color=STATUS_WARNING)
                            else:
                                self.cpu_bar.configure(progress_color=STATUS_OK)
                            
                            # Update RAM
                            mem_percent = stats.get("mem_percent", 0)
                            self.ram_label.configure(text=f"{mem_percent:.1f}%")
                            self.ram_bar.set(mem_percent / 100.0)
                            
                            if mem_percent > 80:
                                self.ram_bar.configure(progress_color=STATUS_ERROR)
                            elif mem_percent > 60:
                                self.ram_bar.configure(progress_color=STATUS_WARNING)
                            else:
                                self.ram_bar.configure(progress_color=STATUS_OK)
                            
                            # Update GPU
                            gpu = stats.get("gpu", {})
                            if gpu.get("available"):
                                gpu_name = gpu.get("name", "Unknown GPU")
                                self.gpu_name_label.configure(text=f"Device: {gpu_name}")
                                
                                # GPU Utilization
                                gpu_util = gpu.get("utilization_percent", gpu.get("utilization", 0))
                                self.gpu_util_label.configure(text=f"Utilization: {gpu_util:.1f}%")
                                self.gpu_util_bar.set(gpu_util / 100.0)
                                
                                # VRAM
                                vram_used = gpu.get("memory_used_mb", 0)
                                vram_total = gpu.get("memory_total_mb", 1)
                                vram_percent = (vram_used / vram_total * 100) if vram_total > 0 else 0
                                
                                self.gpu_vram_label.configure(text=f"VRAM: {vram_used:,} MB / {vram_total:,} MB")
                                self.gpu_vram_bar.set(vram_percent / 100.0)
                                
                                if vram_percent > 80:
                                    self.gpu_vram_bar.configure(progress_color=STATUS_ERROR)
                                elif vram_percent > 60:
                                    self.gpu_vram_bar.configure(progress_color=STATUS_WARNING)
                                else:
                                    self.gpu_vram_bar.configure(progress_color=STATUS_OK)
                            else:
                                self.gpu_name_label.configure(text="No GPU detected (CPU mode)")
                                self.gpu_util_label.configure(text="Utilization: N/A")
                                self.gpu_util_bar.set(0)
                                self.gpu_vram_label.configure(text="VRAM: N/A")
                                self.gpu_vram_bar.set(0)
                            
                            self.status.set_status("ok", "✓ Live")
                            
                        except Exception as e:
                            log(f"UI: Failed to parse system stats: {e}", "UI")
                            self.status.set_status("error", "✗ Parse Error")
                    else:
                        self.status.set_status("error", f"✗ HTTP {r.status_code}")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: System stats fetch error: {e}", "UI")
                
                def update_ui():
                    self.status.set_status("error", "✗ Connection Error")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()
        self.after(4000, self.update_stats)

    def take_snapshot(self):
        """Save current system stats to JSON file"""
        try:
            if not self.current_stats:
                self.status.set_status("error", "✗ No data to snapshot")
                return
            
            # Create logs directory
            logs_dir = os.path.join(BASE_DIR, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            # Generate filename
            timestamp = time.strftime("%Y%m%d-%H%M%S")
            filename = f"system_snapshot-{timestamp}.json"
            filepath = os.path.join(logs_dir, filename)
            
            # Add metadata
            snapshot_data = {
                "timestamp": timestamp,
                "datetime": time.strftime("%Y-%m-%d %H:%M:%S"),
                "stats": self.current_stats
            }
            
            # Write to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(snapshot_data, f, indent=2)
            
            # Show feedback
            original_text = self.snapshot_btn.cget("text")
            self.snapshot_btn.configure(text="✓ Saved!")
            self.after(2000, lambda: self.snapshot_btn.configure(text=original_text))
            
            self.status.set_status("ok", f"✓ Snapshot saved: {filename}")
            self.app.toast.show(f"Snapshot saved", "success")
            log(f"UI: System snapshot saved to {filepath}", "UI")
            
        except Exception as e:
            log(f"UI: Snapshot failed: {e}", "UI")
            self.status.set_status("error", "✗ Snapshot Failed")


class SettingsTab(ctk.CTkFrame):
    """Settings tab with vector store selector and configuration"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        self.config_file = os.path.join(BASE_DIR, "ui", "config.json")
        
        # Load current settings
        self.load_settings()
        
        # Title
        title = ctk.CTkLabel(self, text="Settings", font=heading())
        title.pack(pady=20)
        
        # Settings card
        settings_card = Card(self)
        settings_card.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Vector Store section
        ctk.CTkLabel(settings_card, text="Vector Store", font=subheading()).pack(pady=10, padx=20, anchor="w")
        
        vector_frame = ctk.CTkFrame(settings_card, fg_color="transparent")
        vector_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(
            vector_frame,
            text="Select vector database backend:",
            font=body(),
            text_color=TEXT_SECONDARY
        ).pack(anchor="w", pady=5)
        
        # Vector store dropdown
        self.vector_store_var = ctk.StringVariable(value=CFG.vector_store)
        self.vector_store_dropdown = ctk.CTkOptionMenu(
            vector_frame,
            variable=self.vector_store_var,
            values=["faiss", "chroma"],
            width=200,
            font=body()
        )
        self.vector_store_dropdown.pack(anchor="w", pady=5)
        
        # Info text
        ctk.CTkLabel(
            vector_frame,
            text="FAISS: Fast, lightweight, in-memory (default)\nChroma: Persistent, feature-rich, requires chromadb package",
            font=small(),
            text_color=TEXT_SECONDARY,
            justify="left"
        ).pack(anchor="w", pady=5)
        
        # Save button
        self.save_btn = ctk.CTkButton(
            settings_card,
            text="💾 Save Settings",
            command=self.save_settings,
            height=40,
            font=subheading(),
            fg_color=ACCENT
        )
        self.save_btn.pack(pady=20)
        
        # Status
        self.status = StatusLabel(settings_card, status="info", text="")
        self.status.pack(pady=10)
        
        # Info panel
        info_card = Card(self)
        info_card.pack(padx=20, pady=10, fill="x")
        
        ctk.CTkLabel(info_card, text="Configuration Info", font=subheading()).pack(pady=10, padx=20, anchor="w")
        
        info_text = f"""Current Configuration:
        
Provider: {CFG.provider}
Model: {CFG.model_name}
Vector Store: {CFG.vector_store}
Data Directory: {CFG.data_dir}
Vector Directory: {CFG.vector_dir}

Note: Some settings require API/UI restart to take effect.
Edit config.yaml or set environment variables for more options.
"""
        
        info_label = ctk.CTkLabel(
            info_card,
            text=info_text,
            font=mono(),
            text_color=TEXT_SECONDARY,
            justify="left"
        )
        info_label.pack(padx=20, pady=10, anchor="w")
    
    def load_settings(self):
        """Load settings from config file"""
        try:
            if os.path.exists(self.config_file):
                import json
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    # Settings loaded successfully
                    log(f"UI: Loaded settings from {self.config_file}", "UI")
        except Exception as e:
            log(f"UI: Failed to load settings: {e}", "UI")
    
    def save_settings(self):
        """Save settings to config file and update config.yaml"""
        try:
            import json
            
            selected_vector_store = self.vector_store_var.get()
            
            # Save to ui/config.json
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            
            settings = {
                "vector_store": selected_vector_store,
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            # Also update config.yaml if it exists
            config_yaml_path = os.path.join(BASE_DIR, "config.yaml")
            if os.path.exists(config_yaml_path):
                try:
                    import yaml
                    
                    with open(config_yaml_path, 'r', encoding='utf-8') as f:
                        yaml_config = yaml.safe_load(f) or {}
                    
                    yaml_config['vector_store'] = selected_vector_store
                    
                    with open(config_yaml_path, 'w', encoding='utf-8') as f:
                        yaml.dump(yaml_config, f, default_flow_style=False, sort_keys=False)
                    
                    log(f"UI: Updated config.yaml with vector_store={selected_vector_store}", "UI")
                except ImportError:
                    # PyYAML not installed
                    pass
                except Exception as e:
                    log(f"UI: Failed to update config.yaml: {e}", "UI")
            
            self.status.set_status("ok", "✓ Settings saved")
            self.app.toast.show("Settings saved successfully", "success")
            
            # Show warning if vector store changed
            if selected_vector_store != CFG.vector_store:
                self.app.toast.show("Restart API and UI for vector store change to take effect", "warn", ms=4000)
                self.status.set_status("warn", "⚠ Restart required for vector store change")
            
            log(f"UI: Settings saved: vector_store={selected_vector_store}", "UI")
            
        except Exception as e:
            log(f"UI: Failed to save settings: {e}", "UI")
            self.status.set_status("error", "✗ Save failed")
            self.app.toast.show(f"Save failed: {str(e)}", "error")


class LogsTab(ctk.CTkFrame):
    """Live logs viewer with filtering and controls"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        self.tailing_paused = False
        self.log_filter = "ALL"
        
        # Title
        title = ctk.CTkLabel(self, text="Live Logs", font=heading())
        title.pack(pady=20)
        
        # Logs card
        logs_card = Card(self)
        logs_card.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Controls header
        controls_frame = ctk.CTkFrame(logs_card, fg_color="transparent")
        controls_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(controls_frame, text="Controls", font=subheading()).pack(side="left")
        
        # Open logs folder button
        self.open_folder_btn = ctk.CTkButton(
            controls_frame,
            text="📁 Open Logs Folder",
            command=self.open_logs_folder,
            width=150,
            height=30,
            font=body()
        )
        self.open_folder_btn.pack(side="right", padx=5)
        
        # Pause toggle button
        self.pause_btn = ctk.CTkButton(
            controls_frame,
            text="⏸️ Pause Tailing",
            command=self.toggle_pause,
            width=130,
            height=30,
            font=body(),
            fg_color=ACCENT
        )
        self.pause_btn.pack(side="right", padx=5)
        
        # Filter controls
        filter_frame = ctk.CTkFrame(logs_card, fg_color="transparent")
        filter_frame.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(filter_frame, text="Filter:", font=body(), text_color=TEXT_SECONDARY).pack(side="left", padx=(0, 10))
        
        # Filter buttons
        self.filter_buttons = {}
        for level in ["ALL", "INFO", "WARN", "ERROR"]:
            btn = ctk.CTkButton(
                filter_frame,
                text=level,
                command=lambda l=level: self.set_filter(l),
                width=70,
                height=28,
                font=small(),
                fg_color=ACCENT if level == "ALL" else "transparent",
                border_width=1,
                border_color=ACCENT
            )
            btn.pack(side="left", padx=3)
            self.filter_buttons[level] = btn
        
        # Status
        self.status = StatusLabel(logs_card, status="info", text="Tailing...")
        self.status.pack(pady=10)
        
        # Log viewer
        self.log_viewer = ctk.CTkTextbox(logs_card, font=mono(), wrap="word")
        self.log_viewer.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.after(1000, self.refresh)

    def toggle_pause(self):
        """Toggle pause/resume tailing"""
        self.tailing_paused = not self.tailing_paused
        
        if self.tailing_paused:
            self.pause_btn.configure(text="▶️ Resume Tailing", fg_color=STATUS_WARNING)
            self.status.set_status("warn", "⏸️ Paused")
        else:
            self.pause_btn.configure(text="⏸️ Pause Tailing", fg_color=ACCENT)
            self.status.set_status("info", "▶️ Tailing...")
            # Immediately refresh when resuming
            self.after(100, self.refresh)

    def set_filter(self, level: str):
        """Set log level filter"""
        self.log_filter = level
        
        # Update button colors
        for lvl, btn in self.filter_buttons.items():
            if lvl == level:
                btn.configure(fg_color=ACCENT)
            else:
                btn.configure(fg_color="transparent")
        
        # Immediately refresh with new filter
        self.refresh()
        
        log(f"UI: Log filter set to {level}", "UI")

    def open_logs_folder(self):
        """Open logs folder in file explorer"""
        try:
            logs_dir = os.path.join(BASE_DIR, "logs")
            
            # Ensure directory exists
            os.makedirs(logs_dir, exist_ok=True)
            
            # Open in file explorer (cross-platform)
            if os.name == 'nt':  # Windows
                os.startfile(logs_dir)
            elif os.name == 'posix':  # macOS/Linux
                import subprocess
                if sys.platform == 'darwin':  # macOS
                    subprocess.Popen(['open', logs_dir])
                else:  # Linux
                    subprocess.Popen(['xdg-open', logs_dir])
            
            self.status.set_status("ok", "✓ Folder opened")
            log(f"UI: Opened logs folder: {logs_dir}", "UI")
            
        except Exception as e:
            log(f"UI: Failed to open logs folder: {e}", "UI")
            self.status.set_status("error", "✗ Failed to open folder")

    def refresh(self):
        """Refresh logs (non-blocking)"""
        # Check if paused before scheduling next refresh
        if not self.tailing_paused:
            log_file = os.path.join(BASE_DIR, "logs", "app.log")
            
            def read():
                try:
                    if os.path.exists(log_file):
                        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                            all_lines = f.readlines()[-100:]  # Read more lines for filtering
                        
                        # Apply filter
                        if self.log_filter == "ALL":
                            filtered_lines = all_lines
                        else:
                            # Filter by log level
                            filtered_lines = []
                            for line in all_lines:
                                if self.log_filter == "ERROR" and "ERROR" in line:
                                    filtered_lines.append(line)
                                elif self.log_filter == "WARN" and ("WARN" in line or "WARNING" in line):
                                    filtered_lines.append(line)
                                elif self.log_filter == "INFO" and "INFO" in line:
                                    filtered_lines.append(line)
                        
                        # Limit display to last 50 after filtering
                        display_lines = filtered_lines[-50:] if filtered_lines else []
                        
                        content = "".join(display_lines) if display_lines else f"No {self.log_filter} logs found.\n"
                        
                        def update_ui():
                            # Only update if not paused (double check)
                            if not self.tailing_paused:
                                self.log_viewer.delete("1.0", "end")
                                self.log_viewer.insert("end", content)
                                
                                # Auto-scroll to bottom
                                self.log_viewer.see("end")
                                
                                if self.log_filter == "ALL":
                                    self.status.set_status("ok", f"✓ {len(display_lines)} lines")
                                else:
                                    self.status.set_status("ok", f"✓ {len(display_lines)} {self.log_filter} lines")
                        
                        self.after(0, update_ui)
                    else:
                        self.after(0, lambda: self.status.set_status("warn", "⚠ Log file not found"))
                except Exception as e:
                    log(f"UI: Log refresh error: {e}", "UI")
            
            threading.Thread(target=read, daemon=True).start()
        
        # Schedule next refresh (respects pause state)
        self.after(4000, self.refresh)


class BridgeTab(ctk.CTkFrame):
    """Cloud Bridge tab"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        
        # Title
        title = ctk.CTkLabel(self, text="Cloud Bridge", font=heading())
        title.pack(pady=20)
        
        self.auto_backup_enabled = False
        self.config_file = os.path.join(BASE_DIR, "ui", "config.json")
        
        # Load saved config
        self.load_config()
        
        if not BRIDGE_AVAILABLE:
            Card(self).pack(padx=20, pady=20)
            ctk.CTkLabel(
                self,
                text="⚠️ Cloud Bridge not available",
                font=subheading(),
                text_color=STATUS_WARNING
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
    """CLO 3D Integration control panel"""
    
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=DARK_BG)
        self.app = app
        self.client = None
        self.connected = False
        
        # State machine for periodic probing
        self._clo_state = "idle"  # idle, probing, ok, down
        self._probe_interval_ms = 5000  # 5 seconds
        self._probe_active = False
        self._hide_warning_session = False  # "Don't show again" flag
        self._last_error = None  # For "Why?" explainer
        
        # Import CLO client
        try:
            from modules.clo_companion.clo_client import CLOClient
            from modules.clo_companion.config import CLO_HOST, CLO_PORT
            self.CLOClient = CLOClient
            self.default_host = CLO_HOST
            self.default_port = CLO_PORT
            self.clo_available = True
        except ImportError:
            self.clo_available = False
        
        # Title
        title = ctk.CTkLabel(self, text="CLO 3D Integration", font=heading())
        title.pack(pady=20)
        
        if not self.clo_available:
            error_card = Card(self)
            error_card.pack(padx=20, pady=20, fill="both", expand=True)
            ctk.CTkLabel(
                error_card,
                text="⚠️ CLO companion module not available",
                font=subheading(),
                text_color=STATUS_WARNING
            ).pack(pady=50)
            return
        
        # Connection panel
        conn_card = Card(self)
        conn_card.pack(padx=20, pady=10, fill="x")
        
        ctk.CTkLabel(conn_card, text="Connection", font=subheading()).pack(pady=10, padx=20, anchor="w")
        
        # Help/Instructions panel (collapsible)
        help_frame = ctk.CTkFrame(conn_card, fg_color=CARD_BG, corner_radius=8)
        help_frame.pack(padx=20, pady=5, fill="x")
        
        self.help_toggle_btn = ctk.CTkButton(
            help_frame,
            text="ℹ️ Show Setup Instructions",
            command=self.toggle_help,
            font=small(),
            fg_color="transparent",
            hover_color="#1a1a1e",
            height=25
        )
        self.help_toggle_btn.pack(pady=5)
        
        self.help_content = ctk.CTkTextbox(help_frame, font=small(), height=0, wrap="word")
        self.help_content.pack_forget()  # Hidden by default
        
        help_text = """Quick Start Checklist:

☐ 1. Launch CLO 3D application

☐ 2. In CLO: File > Script > Run Script...

☐ 3. Navigate to: modules/clo_companion/clo_bridge_listener.py

☐ 4. Click "Run" - you should see:
      "CLO Bridge listening on 127.0.0.1:51235"

☐ 5. Return here and click "Connect"

Note: The bridge listener must be running in CLO for the
connection to work. Keep CLO's script console open to
see listener status and command logs.

Troubleshooting:
- Port already in use? Set CLO_PORT env variable
- Firewall blocking? Allow localhost connections
- Script errors? Check CLO's Python console output
"""
        self.help_content.insert("1.0", help_text)
        self.help_content.configure(state="disabled")
        self.help_visible = False
        
        # Host and port fields
        config_frame = ctk.CTkFrame(conn_card, fg_color="transparent")
        config_frame.pack(pady=5, padx=20, fill="x")
        
        ctk.CTkLabel(config_frame, text="Host:", font=body(), text_color=TEXT_SECONDARY).pack(side="left", padx=(0, 5))
        
        self.host_entry = ctk.CTkEntry(config_frame, width=150, font=body())
        self.host_entry.insert(0, self.default_host)
        self.host_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(config_frame, text="Port:", font=body(), text_color=TEXT_SECONDARY).pack(side="left", padx=(20, 5))
        
        self.port_entry = ctk.CTkEntry(config_frame, width=80, font=body())
        self.port_entry.insert(0, str(self.default_port))
        self.port_entry.pack(side="left", padx=5)
        
        # Connect button
        self.connect_btn = ctk.CTkButton(
            config_frame,
            text="🔌 Connect",
            command=self.toggle_connection,
            width=120,
            height=32,
            font=body(),
            fg_color=ACCENT
        )
        self.connect_btn.pack(side="left", padx=20)
        
        # "How to connect" help link
        help_link = ctk.CTkButton(
            config_frame,
            text="❓ How to connect",
            command=self.toggle_help,
            width=120,
            height=32,
            font=small(),
            fg_color="transparent",
            hover_color=CARD_BG,
            border_width=1,
            border_color=TEXT_SECONDARY
        )
        help_link.pack(side="left", padx=5)
        
        # Status
        self.conn_status = StatusLabel(conn_card, status="info", text="Disconnected")
        self.conn_status.pack(pady=10)
        
        # Bridge warning frame (shown when listener not found)
        self.bridge_warning_frame = ctk.CTkFrame(conn_card, fg_color="transparent")
        self.bridge_warning_frame.pack_forget()  # Hidden by default
        
        warning_text_frame = ctk.CTkFrame(self.bridge_warning_frame, fg_color="transparent")
        warning_text_frame.pack(side="left", fill="x", expand=True)
        
        self.bridge_warning = ctk.CTkLabel(
            warning_text_frame,
            text="⚠️ Listener not found. Open CLO → Script → Run Script… (see help)",
            font=small(),
            text_color=STATUS_WARNING,
            wraplength=400
        )
        self.bridge_warning.pack(side="left", padx=5)
        
        # Warning action buttons
        warning_buttons = ctk.CTkFrame(self.bridge_warning_frame, fg_color="transparent")
        warning_buttons.pack(side="right", padx=5)
        
        # "Why?" explainer button
        self.why_btn = ctk.CTkButton(
            warning_buttons,
            text="Why?",
            command=self.show_error_details,
            width=50,
            height=24,
            font=small(),
            fg_color="transparent",
            hover_color=CARD_BG,
            border_width=1,
            border_color=STATUS_WARNING
        )
        self.why_btn.pack(side="left", padx=2)
        
        # "Retry now" button
        self.retry_btn = ctk.CTkButton(
            warning_buttons,
            text="Retry",
            command=self.retry_bridge_check,
            width=60,
            height=24,
            font=small(),
            fg_color=ACCENT,
            hover_color=STATUS_OK
        )
        self.retry_btn.pack(side="left", padx=2)
        
        # "Don't show again" button
        self.hide_btn = ctk.CTkButton(
            warning_buttons,
            text="Hide",
            command=self.hide_warning_session,
            width=50,
            height=24,
            font=small(),
            fg_color="transparent",
            hover_color=CARD_BG,
            border_width=1,
            border_color=TEXT_SECONDARY
        )
        self.hide_btn.pack(side="left", padx=2)
        
        # Start periodic probe
        self.after(500, self.start_periodic_probe)
        
        # Actions panel
        actions_card = Card(self)
        actions_card.pack(padx=20, pady=10, fill="both", expand=True)
        
        ctk.CTkLabel(actions_card, text="Actions", font=subheading()).pack(pady=10, padx=20, anchor="w")
        
        # Action buttons grid
        btn_grid = ctk.CTkFrame(actions_card, fg_color="transparent")
        btn_grid.pack(pady=10, padx=20, fill="x")
        
        # Row 1: Import and Export
        self.import_btn = ctk.CTkButton(
            btn_grid,
            text="📁 Import Garment",
            command=self.import_garment,
            width=180,
            height=40,
            font=body(),
            state="disabled"
        )
        self.import_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.export_btn = ctk.CTkButton(
            btn_grid,
            text="💾 Export Garment",
            command=self.export_garment,
            width=180,
            height=40,
            font=body(),
            state="disabled"
        )
        self.export_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Row 2: Simulation controls
        sim_frame = ctk.CTkFrame(btn_grid, fg_color="transparent")
        sim_frame.grid(row=1, column=0, columnspan=2, pady=10)
        
        ctk.CTkLabel(sim_frame, text="Simulation Steps:", font=body(), text_color=TEXT_SECONDARY).pack(side="left", padx=5)
        
        self.sim_steps = ctk.CTkEntry(sim_frame, width=80, font=body())
        self.sim_steps.insert(0, "50")
        self.sim_steps.pack(side="left", padx=5)
        
        self.sim_btn = ctk.CTkButton(
            sim_frame,
            text="▶️ Run Simulation",
            command=self.run_simulation,
            width=150,
            height=35,
            font=body(),
            state="disabled",
            fg_color=ACCENT
        )
        self.sim_btn.pack(side="left", padx=10)
        
        # Row 3: Screenshot
        self.screenshot_btn = ctk.CTkButton(
            btn_grid,
            text="📷 Take Screenshot",
            command=self.take_screenshot,
            width=180,
            height=40,
            font=body(),
            state="disabled"
        )
        self.screenshot_btn.grid(row=2, column=0, padx=5, pady=5)
        
        # Screenshot preview area
        preview_frame = ctk.CTkFrame(actions_card, fg_color=CARD_BG, corner_radius=8)
        preview_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(preview_frame, text="Last Screenshot:", font=body(), text_color=TEXT_SECONDARY).pack(pady=5, padx=10, anchor="w")
        
        self.screenshot_preview = ctk.CTkLabel(
            preview_frame,
            text="No screenshot yet",
            font=small(),
            text_color=TEXT_SECONDARY
        )
        self.screenshot_preview.pack(pady=5, padx=10)
        
        # Output log
        ctk.CTkLabel(actions_card, text="Activity Log", font=subheading()).pack(pady=(15, 5), padx=20, anchor="w")
        
        self.output = ctk.CTkTextbox(actions_card, font=mono(), height=150)
        self.output.pack(fill="both", expand=True, padx=20, pady=10)
        self.output.insert("1.0", "CLO 3D Integration ready.\nConnect to CLO bridge to begin.\n")

    def log_output(self, message: str, is_error: bool = False):
        """Append timestamped message to output log"""
        timestamp = time.strftime("%H:%M:%S")
        prefix = "✗" if is_error else "✓"
        self.output.insert("end", f"[{timestamp}] {prefix} {message}\n")
        self.output.see("end")

    def start_periodic_probe(self):
        """Start periodic CLO bridge probing with jitter"""
        if not self._probe_active:
            self._probe_active = True
            self._probe_clo_async()
    
    def _probe_clo_async(self):
        """Async probe with state machine and coalesced updates"""
        import threading
        import random
        
        if self._clo_state == "probing":
            return  # Already probing
        
        self._clo_state = "probing"
        
        def run():
            ok = False
            error_detail = None
            
            try:
                import requests
                # Hit the lightweight /health/clo endpoint
                r = requests.get("http://127.0.0.1:5000/health/clo", timeout=1.2)
                if r.ok:
                    data = r.json()
                    ok = data.get("ok", False)
                    if not ok:
                        error_detail = data.get("error", "Unknown error")
            except Exception as e:
                ok = False
                error_detail = f"{e.__class__.__name__}: {str(e)}"
            
            new_state = "ok" if ok else "down"
            
            def apply():
                old_state = self._clo_state
                self._clo_state = new_state
                self._last_error = error_detail
                
                # Only update UI if state changed (debounce churn)
                if old_state != new_state:
                    self._render_bridge_banner()
                
                # Schedule next probe with jitter
                jitter = random.randint(0, 500)
                self.after(self._probe_interval_ms + jitter, self._probe_clo_async)
            
            self.after(0, apply)
        
        threading.Thread(target=run, daemon=True).start()
    
    def _render_bridge_banner(self):
        """Render warning banner based on current state"""
        if self._clo_state == "down" and not self._hide_warning_session and not self.connected:
            # Show warning
            self.bridge_warning_frame.pack(pady=5, fill="x")
        elif self._clo_state == "ok":
            # Hide warning when bridge is up
            self.bridge_warning_frame.pack_forget()
        # Note: "probing" state doesn't change banner
    
    def check_bridge_status(self):
        """Legacy method - now uses periodic probe"""
        # Trigger immediate probe
        self.retry_bridge_check()
    
    def retry_bridge_check(self):
        """Manual retry - force immediate probe"""
        self._clo_state = "idle"  # Reset to allow new probe
        self._probe_clo_async()
        self.app.toast.show("Checking CLO Bridge...", "info")
    
    def show_error_details(self):
        """Show modal with last probe error details"""
        from tkinter import messagebox
        
        if self._last_error:
            error_msg = f"CLO Bridge Check Failed\n\n"
            error_msg += f"Error Details:\n{self._last_error}\n\n"
            error_msg += f"Troubleshooting Steps:\n"
            error_msg += f"1. Verify CLO 3D is running\n"
            error_msg += f"2. In CLO: Script → Run Script…\n"
            error_msg += f"3. Select: modules\\clo_companion\\clo_bridge_listener.py\n"
            error_msg += f"4. Check firewall settings (allow port {self.default_port})\n"
            error_msg += f"5. Test: PowerShell > Test-NetConnection 127.0.0.1 -Port {self.default_port}"
            
            messagebox.showinfo("Why is CLO Bridge not reachable?", error_msg)
        else:
            messagebox.showinfo("CLO Bridge Status", "No error details available.\n\nTry clicking 'Retry' to test connection.")
    
    def hide_warning_session(self):
        """Hide warning for this session (until app restart)"""
        self._hide_warning_session = True
        self.bridge_warning_frame.pack_forget()
        self.app.toast.show("CLO warning hidden for this session", "info")
    
    def toggle_help(self):
        """Toggle help instructions visibility"""
        if self.help_visible:
            # Hide help
            self.help_content.pack_forget()
            self.help_toggle_btn.configure(text="ℹ️ Show Setup Instructions")
            self.help_visible = False
        else:
            # Show help
            self.help_content.pack(fill="x", padx=10, pady=5)
            self.help_toggle_btn.configure(text="ℹ️ Hide Setup Instructions")
            self.help_visible = True

    def toggle_connection(self):
        """Toggle connection to CLO bridge"""
        if self.connected:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        """Connect to CLO bridge listener"""
        self.connect_btn.configure(state="disabled", text="Connecting...")
        self.app.active_operations += 1
        
        def run():
            try:
                host = self.host_entry.get().strip()
                port_str = self.port_entry.get().strip()
                
                try:
                    port = int(port_str)
                except ValueError:
                    def update_ui():
                        self.app.active_operations -= 1
                        self.conn_status.set_status("error", "Invalid port number")
                        self.connect_btn.configure(state="normal", text="🔌 Connect")
                        self.log_output(f"Invalid port: {port_str}", is_error=True)
                        self.app.toast.show(f"Invalid port: {port_str}", "error")
                    self.after(0, update_ui)
                    return
                
                # Create client
                self.client = self.CLOClient(host=host, port=port)
                result = self.client.connect()
                
                def update_ui():
                    self.app.active_operations -= 1
                    
                    if result["ok"]:
                        self.connected = True
                        attempts = result.get("data", {}).get("attempts", 1)
                        self.conn_status.set_status("ok", f"🟢 Connected to {host}:{port}")
                        self.connect_btn.configure(text="🔌 Disconnect", fg_color=STATUS_WARNING)
                        
                        # Enable action buttons
                        self.import_btn.configure(state="normal")
                        self.export_btn.configure(state="normal")
                        self.sim_btn.configure(state="normal")
                        self.screenshot_btn.configure(state="normal")
                        
                        msg = f"Connected to CLO bridge at {host}:{port}"
                        if attempts > 1:
                            msg += f" (attempt {attempts})"
                        self.log_output(msg)
                        log(f"UI: {msg}", "UI")
                        
                        # Hide bridge warning on successful connection
                        self.bridge_warning_frame.pack_forget()
                        self._clo_state = "ok"  # Update state
                        
                        # Auto-hide help on successful connection
                        if self.help_visible:
                            self.toggle_help()
                    else:
                        self.connected = False
                        self.conn_status.set_status("error", "🔴 Connection failed")
                        self.connect_btn.configure(state="normal", text="🔌 Connect")
                        
                        error = result.get("error", "Unknown error")
                        help_text = result.get("help", "")
                        
                        self.log_output(f"Connection failed: {error}", is_error=True)
                        self.app.toast.show("CLO connection failed", "error")
                        
                        # If help text provided and help not visible, show it
                        if help_text and not self.help_visible:
                            # Update help content with specific troubleshooting
                            self.help_content.configure(state="normal")
                            current_help = self.help_content.get("1.0", "end")
                            self.help_content.delete("1.0", "end")
                            self.help_content.insert("1.0", f"ERROR: {error}\n\n{help_text}\n\n{'='*50}\n\n{current_help}")
                            self.help_content.configure(state="disabled")
                            self.toggle_help()  # Show help
                    
                    self.connect_btn.configure(state="normal")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: CLO connection error: {e}", "UI")
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.conn_status.set_status("error", "🔴 Error")
                    self.connect_btn.configure(state="normal", text="🔌 Connect")
                    self.log_output(f"Connection error: {str(e)}", is_error=True)
                    self.app.toast.show("Connection error", "error")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()

    def disconnect(self):
        """Disconnect from CLO bridge"""
        self.connected = False
        self.client = None
        
        self.conn_status.set_status("info", "Disconnected")
        self.connect_btn.configure(text="🔌 Connect", fg_color=ACCENT)
        
        # Disable action buttons
        self.import_btn.configure(state="disabled")
        self.export_btn.configure(state="disabled")
        self.sim_btn.configure(state="disabled")
        self.screenshot_btn.configure(state="disabled")
        
        self.log_output("Disconnected from CLO bridge")
        
        # Reset state and re-check after disconnect
        self._clo_state = "idle"
        self.retry_bridge_check()

    def import_garment(self):
        """Import garment file into CLO"""
        from tkinter import filedialog
        
        file_path = filedialog.askopenfilename(
            title="Select Garment File",
            filetypes=[
                ("CLO Project", "*.zprj"),
                ("OBJ Files", "*.obj"),
                ("FBX Files", "*.fbx"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        self.import_btn.configure(state="disabled")
        self.app.active_operations += 1
        
        def run():
            try:
                result = self.client.import_garment(file_path)
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.import_btn.configure(state="normal")
                    
                    if result["ok"]:
                        self.log_output(f"Imported: {os.path.basename(file_path)}")
                        self.app.toast.show(f"Imported {os.path.basename(file_path)}", "success")
                    else:
                        error = result.get("error", "Unknown error")
                        self.log_output(f"Import failed: {error}", is_error=True)
                        self.app.toast.show("Import failed", "error")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: Import error: {e}", "UI")
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.import_btn.configure(state="normal")
                    self.log_output(f"Import error: {str(e)}", is_error=True)
                    self.app.toast.show("Import error", "error")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()

    def export_garment(self):
        """Export garment from CLO"""
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            title="Export Garment",
            defaultextension=".zprj",
            filetypes=[
                ("CLO Project", "*.zprj"),
                ("OBJ Files", "*.obj"),
                ("FBX Files", "*.fbx"),
                ("glTF", "*.gltf"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        # Determine format from extension
        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        format_map = {"zprj": "zprj", "obj": "obj", "fbx": "fbx", "gltf": "gltf"}
        export_format = format_map.get(ext, "zprj")
        
        self.export_btn.configure(state="disabled")
        self.app.active_operations += 1
        
        def run():
            try:
                result = self.client.export_garment(file_path, format=export_format)
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.export_btn.configure(state="normal")
                    
                    if result["ok"]:
                        self.log_output(f"Exported to: {os.path.basename(file_path)}")
                        self.app.toast.show(f"Exported {os.path.basename(file_path)}", "success")
                    else:
                        error = result.get("error", "Unknown error")
                        self.log_output(f"Export failed: {error}", is_error=True)
                        self.app.toast.show("Export failed", "error")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: Export error: {e}", "UI")
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.export_btn.configure(state="normal")
                    self.log_output(f"Export error: {str(e)}", is_error=True)
                    self.app.toast.show("Export error", "error")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()

    def run_simulation(self):
        """Run physics simulation in CLO"""
        try:
            steps = int(self.sim_steps.get())
            if steps <= 0:
                self.log_output("Simulation steps must be positive", is_error=True)
                self.app.toast.show("Steps must be positive", "error")
                return
        except ValueError:
            self.log_output("Invalid simulation steps value", is_error=True)
            self.app.toast.show("Invalid steps value", "error")
            return
        
        self.sim_btn.configure(state="disabled")
        self.app.active_operations += 1
        
        def run():
            try:
                result = self.client.run_simulation(steps=steps)
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.sim_btn.configure(state="normal")
                    
                    if result["ok"]:
                        self.log_output(f"Simulation completed: {steps} steps")
                        self.app.toast.show(f"Simulation complete ({steps} steps)", "success")
                    else:
                        error = result.get("error", "Unknown error")
                        self.log_output(f"Simulation failed: {error}", is_error=True)
                        self.app.toast.show("Simulation failed", "error")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: Simulation error: {e}", "UI")
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.sim_btn.configure(state="normal")
                    self.log_output(f"Simulation error: {str(e)}", is_error=True)
                    self.app.toast.show("Simulation error", "error")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()

    def take_screenshot(self):
        """Take screenshot of CLO viewport"""
        # Create exports directory
        export_dir = os.path.join(BASE_DIR, "exports", "clo_shots")
        os.makedirs(export_dir, exist_ok=True)
        
        # Generate filename
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"clo_screenshot_{timestamp}.png"
        filepath = os.path.join(export_dir, filename)
        
        self.screenshot_btn.configure(state="disabled")
        self.app.active_operations += 1
        
        def run():
            try:
                result = self.client.take_screenshot(filepath, width=1280, height=720)
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.screenshot_btn.configure(state="normal")
                    
                    if result["ok"]:
                        self.log_output(f"Screenshot saved: {filename}")
                        self.screenshot_preview.configure(text=f"📸 {filename}")
                        self.app.toast.show("Screenshot saved", "success")
                        log(f"UI: CLO screenshot saved to {filepath}", "UI")
                    else:
                        error = result.get("error", "Unknown error")
                        self.log_output(f"Screenshot failed: {error}", is_error=True)
                        self.app.toast.show("Screenshot failed", "error")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: Screenshot error: {e}", "UI")
                
                def update_ui():
                    self.app.active_operations -= 1
                    self.screenshot_btn.configure(state="normal")
                    self.log_output(f"Screenshot error: {str(e)}", is_error=True)
                    self.app.toast.show("Screenshot error", "error")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()


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
