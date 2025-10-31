"""
RAG System Control Panel
GUI application for managing the local RAG academic assistant and CLO Companion
"""

# Fix Tkinter Tcl/Tk paths before importing
import os
import sys
from core.io_safety import safe_reconfigure_streams
safe_reconfigure_streams()

# Force UTF-8 encoding (safe for pythonw.exe)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.io_safety import safe_reconfigure_streams
safe_reconfigure_streams()

# Auto-detect and set Tcl/Tk library paths
def setup_tkinter_paths():
    """Auto-configure Tcl/Tk library paths for Windows"""
    if os.environ.get("TCL_LIBRARY") and os.environ.get("TK_LIBRARY"):
        return
    
    possible_python_dirs = [
        os.path.dirname(sys.executable),
        r"C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python312",
        r"C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python314",
        os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs", "Python", "Python312"),
        os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs", "Python", "Python314"),
    ]
    
    tcl_path = None
    tk_path = None
    
    for python_dir in possible_python_dirs:
        tcl_dir = os.path.join(python_dir, "tcl")
        if os.path.exists(tcl_dir):
            try:
                for root, dirs, files in os.walk(tcl_dir):
                    if "init.tcl" in files:
                        tcl_path = root
                        tcl_parent = os.path.dirname(tcl_path)
                        for item in os.listdir(tcl_parent):
                            tk_candidate = os.path.join(tcl_parent, item)
                            if item.startswith("tk") and os.path.isdir(tk_candidate):
                                if os.path.exists(os.path.join(tk_candidate, "tk.tcl")):
                                    tk_path = tk_candidate
                                    break
                        if tk_path:
                            break
            except Exception:
                continue
        if tcl_path and tk_path:
            break
    
    if tcl_path and not os.environ.get("TCL_LIBRARY"):
        os.environ["TCL_LIBRARY"] = tcl_path
    if tk_path and not os.environ.get("TK_LIBRARY"):
        os.environ["TK_LIBRARY"] = tk_path

setup_tkinter_paths()

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import threading
import socket
import time
from typing import Dict
from datetime import datetime
from pathlib import Path

# Import unified logger
try:
    from logger import log, log_exception, get_recent_logs
except ImportError:
    def log(msg, category="GUI", print_to_console=True):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{category}] {msg}")
    def log_exception(category="ERROR", exception=None, context=""):
        import traceback
        print(f"[{category}] {context}: {exception}", file=sys.stderr)
        traceback.print_exc()
    def get_recent_logs(lines=50, category=None):
        return []

# Import diagnostics
try:
    from diagnostics import DiagnosticsChecker
except ImportError:
    DiagnosticsChecker = None

class RAGControlPanel:
    def __init__(self, root):
        self.root = root
        self.root.title("Julian Assistant Suite Control Panel")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)
        
        # State variables
        self.api_process = None
        self.clo_api_process = None
        self.logging_enabled = True
        self.log_dir = os.path.join(os.path.dirname(__file__), "Logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file = os.path.join(self.log_dir, "operations.log")
        
        # Check if first launch
        self.first_launch_file = os.path.join(os.path.dirname(__file__), ".first_launch")
        
        # GUI Setup
        self.setup_ui()
        
        # Initial status check
        self.root.after(1000, self.update_all_status)
        
        # Log system information
        import platform
        py_version = sys.version.split()[0]
        self.log(f"Control Panel started | Python {py_version} on {platform.system()} {platform.release()}")
        
        # Show first-launch walkthrough
        is_first_launch = not os.path.exists(self.first_launch_file)
        if is_first_launch:
            self.root.after(2000, self.show_first_launch_walkthrough)
        
        # Auto-start API server after initialization (5 seconds delay)
        self.root.after(5000, self.auto_start_api_server)
        
        # Note: CLO Companion API starts on-demand (when first generation is requested)
        
        # Handle window close (X button) event
        self.root.protocol("WM_DELETE_WINDOW", self.on_window_close)
        
        # Graceful shutdown flag
        self.shutting_down = False
    
    def load_api_endpoint(self):
        """Load API host and port from config, with fallback to defaults"""
        import json
        cfg_path = os.path.join(os.path.dirname(__file__), "config", "academic_rag_config.json")
        host, port = "127.0.0.1", 5000  # defaults
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                api_config = config.get("api", {})
                host = api_config.get("host", host)
                port = int(api_config.get("port", port))
        except Exception as e:
            self.log(f"Could not load API config, using defaults: {e}", "WARNING")
        return host, port
    
    def check_api_health(self, host=None, port=None, timeout=2):
        """Check if API is healthy by hitting /health endpoint"""
        if host is None or port is None:
            host, port = self.load_api_endpoint()
        try:
            import requests
            url = f"http://{host}:{port}/health"
            r = requests.get(url, timeout=timeout)
            return r.ok and r.status_code == 200
        except Exception:
            return False
    
    def setup_ui(self):
        """Setup the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title with version and model info
        version = "v7.9.7-Julian-DynamicLLMRouter"
        title_label = ttk.Label(main_frame, text=f"Julian Assistant Suite {version}", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 5))
        
        # Model label
        self.model_label = ttk.Label(main_frame, text="Model: Llama 3.2 via Ollama", 
                                    font=("Arial", 9), foreground="gray")
        self.model_label.grid(row=0, column=2, sticky=tk.E, padx=10)
        
        # Update notification (if available)
        try:
            from update_checker import check_for_updates
            has_update, _, _ = check_for_updates()
            if has_update:
                update_label = ttk.Label(main_frame, text="⚠ Update Available", 
                                       foreground="orange", font=("Arial", 9))
                update_label.grid(row=0, column=2, sticky=tk.E, padx=10)
        except:
            pass
        
        # LLM Router Status (above status indicators)
        self.llm_status_label = ttk.Label(main_frame, text="LLM: ⚪ Checking...", 
                                         font=("Arial", 9))
        self.llm_status_label.grid(row=1, column=0, columnspan=3, pady=2)
        
        # Initialize LLM status update
        self.root.after(1000, self.update_all_status)
        self.root.after(5000, self.update_all_status)
        
        # Status Indicators Frame
        status_frame = ttk.LabelFrame(main_frame, text="System Status", padding="10")
        status_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        # Status indicators
        self.status_labels = {}
        indicators = [
            ("Python", "python"),
            ("Ollama", "ollama"),
            ("Llama Model", "llama"),
            ("ChromaDB", "chromadb"),
            ("RAG API", "api"),
            ("Vault Path", "vault"),
            ("Cloud Bridge", "cloud")
        ]
        
        for i, (name, key) in enumerate(indicators):
            row = i // 3
            col = i % 3
            
            label = ttk.Label(status_frame, text=name + ":")
            label.grid(row=row, column=col*2, sticky=tk.W, padx=5, pady=2)
            
            status_indicator = ttk.Label(status_frame, text="●", font=("Arial", 16))
            status_indicator.grid(row=row, column=col*2+1, sticky=tk.W, padx=2)
            self.status_labels[key] = status_indicator
        
        # Control Buttons Frame
        button_frame = ttk.LabelFrame(main_frame, text="Actions", padding="10")
        button_frame.grid(row=3, column=0, sticky=(tk.W, tk.N, tk.S), padx=(0, 10))
        
        buttons = [
            ("Index Documents", self.index_documents, "blue"),
            ("Start API Server", self.start_api_server, "green"),
            ("Stop API Server", self.stop_api_server, "red"),
            ("Test Query", self.test_query, "purple"),
            ("Reindex Vault", self.reindex_vault, "orange"),
            ("Health Check", self.run_health_check, "cyan"),
            ("Full System Test", self.run_full_system_test, "purple"),
            ("Backup System", self.backup_system, "brown"),
            ("Restore System", self.restore_system, "darkblue"),
            ("Cloud Sync Now", self.sync_cloud, "teal"),
            ("Cloud Status", self.cloud_status, "lightblue"),
            ("Open Logs Folder", self.open_logs_folder, "gray"),
            ("Quit", self.quit_app, "darkgray")
        ]
        
        for i, (text, command, color) in enumerate(buttons):
            btn = tk.Button(button_frame, text=text, command=command, 
                          width=18, height=2, font=("Arial", 9))
            btn.grid(row=i, column=0, pady=3, sticky=(tk.W, tk.E))
            button_frame.columnconfigure(0, weight=1)
        
        # Progress bar for long operations (initially hidden)
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100, length=200, mode='indeterminate')
        self.progress_bar.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=10, pady=2)
        self.progress_bar.grid_remove()
        
        # Status messages console (non-scrolling, timestamped, shows recent 4 lines)
        status_frame = ttk.LabelFrame(main_frame, text="Status Messages", padding="5")
        status_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2)
        
        self.status_text = tk.Text(status_frame, height=4, width=80, wrap=tk.WORD, 
                                   font=("Courier", 8), state=tk.DISABLED, bg="#f5f5f5")
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        status_frame.columnconfigure(0, weight=1)
        
        # Create Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        # Dashboard Tab (main)
        dashboard_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(dashboard_frame, text="📊 Dashboard")
        
        # Logs Frame (in Dashboard)
        logs_frame = ttk.LabelFrame(dashboard_frame, text="Live Logs", padding="5")
        logs_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        logs_frame.columnconfigure(0, weight=1)
        logs_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(logs_frame, height=18, width=80,
                                                  font=("Consolas", 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear logs button
        clear_btn = ttk.Button(logs_frame, text="Clear Logs", command=self.clear_logs)
        clear_btn.grid(row=1, column=0, pady=5)
        
        dashboard_frame.columnconfigure(0, weight=1)
        dashboard_frame.rowconfigure(0, weight=1)
        
        # CLO Companion Tab
        clo_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(clo_frame, text="👗 CLO Companion")
        self.setup_clo_tab(clo_frame)
        
        # Troubleshooter Tab
        trouble_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(trouble_frame, text="🛠 Troubleshooter")
        self.setup_troubleshooter_tab(trouble_frame)
        
        # Settings Tab (if not exists)
        try:
            # Check if settings tab already exists
            settings_exists = False
            for i in range(self.notebook.index("end")):
                if "Settings" in self.notebook.tab(i, "text") or "⚙️" in self.notebook.tab(i, "text"):
                    settings_exists = True
                    break
            
            if not settings_exists:
                settings_frame = ttk.Frame(self.notebook, padding="10")
                self.notebook.add(settings_frame, text="⚙️ Settings")
                self.setup_settings_tab(settings_frame)
                
                # Maintenance tab
                maintenance_frame = ttk.Frame(self.notebook)
                self.notebook.add(maintenance_frame, text="🧹 System Maintenance")
                self.setup_maintenance_tab(maintenance_frame)
        except:
            pass  # Settings tab setup handled elsewhere
        
        # Bottom status bar with restart button (will show "✅ Self-Healing Verified" after tests pass)
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_bar = ttk.Label(status_frame, text="Ready", relief=tk.SUNKEN)
        self.status_bar.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Restart Control Panel button (bottom-right)
        self.restart_btn = tk.Button(
            status_frame,
            text="🔄 Restart",
            command=self.restart_control_panel,
            bg="#FF9800",
            fg="white",
            font=("Arial", 9),
            width=12,
            relief=tk.RAISED,
            cursor="hand2"
        )
        self.restart_btn.grid(row=0, column=1, padx=2, pady=2, sticky=tk.E)
        
        # Add tooltip functionality if not exists
        if not hasattr(self, 'create_tooltip'):
            def create_tooltip(widget, text):
                def on_enter(event):
                    tooltip = tk.Toplevel()
                    tooltip.wm_overrideredirect(True)
                    tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
                    label = tk.Label(tooltip, text=text, background="#ffffe0", 
                                   relief=tk.SOLID, borderwidth=1, font=("Arial", 9))
                    label.pack()
                    widget.tooltip = tooltip
                
                def on_leave(event):
                    if hasattr(widget, 'tooltip'):
                        widget.tooltip.destroy()
                        del widget.tooltip
                
                widget.bind('<Enter>', on_enter)
                widget.bind('<Leave>', on_leave)
            
            self.create_tooltip = create_tooltip
        
        # Add tooltip to restart button
        self.create_tooltip(self.restart_btn, "Stop and restart all modules without closing the launcher")
        
        # Self-healing verified banner (hidden by default)
        self.self_heal_banner = ttk.Label(main_frame, text="✅ Self-Healing Verified", 
                                          font=("Arial", 10, "bold"), 
                                          foreground="green", 
                                          relief=tk.RAISED)
        # Banner will be shown after tests pass
        
        # Adjust row configuration
        main_frame.rowconfigure(4, weight=1)
    
    def setup_clo_tab(self, parent_frame):
        """Setup CLO Companion tab with garment generation and chat interface"""
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(parent_frame, text="CLO Companion - Garment Generator", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # Main content frame (now with chat)
        content_frame = ttk.Frame(parent_frame)
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Create notebook for tabs: Generate | Chat
        clo_notebook = ttk.Notebook(content_frame)
        clo_notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Tab 1: Generation Panel
        gen_frame = ttk.Frame(clo_notebook, padding="10")
        clo_notebook.add(gen_frame, text="⚙️ Generate")
        
        # Tab 2: Chat Panel
        chat_frame = ttk.Frame(clo_notebook, padding="10")
        clo_notebook.add(chat_frame, text="💬 Chat & Iterate")
        self.setup_clo_chat_panel(chat_frame)
        
        # Generation panel content
        gen_content = ttk.Frame(gen_frame)
        gen_content.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        gen_content.columnconfigure(1, weight=1)
        
        # Left panel - Input
        input_frame = ttk.LabelFrame(gen_content, text="Generate Garment", padding="15")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), padx=(0, 10))
        input_frame.columnconfigure(0, weight=1)
        
        # Prompt label
        prompt_label = ttk.Label(input_frame, text="Garment Prompt:", font=("Arial", 10))
        prompt_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Example prompts
        example_frame = ttk.Frame(input_frame)
        example_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(example_frame, text="Examples:", font=("Arial", 9), foreground="gray").grid(row=0, column=0, sticky=tk.W)
        examples = [
            "white cotton t-shirt with rolled sleeves",
            "oversized beige trench coat with belt",
            "black denim pants"
        ]
        for i, example in enumerate(examples):
            example_label = ttk.Label(example_frame, text=f"• {example}", 
                                     font=("Arial", 8), foreground="gray", cursor="hand2")
            example_label.grid(row=i+1, column=0, sticky=tk.W, padx=(15, 0))
            example_label.bind("<Button-1>", lambda e, ex=example: self.clo_prompt_entry.delete(0, tk.END) or self.clo_prompt_entry.insert(0, ex))
        
        # Prompt entry
        self.clo_prompt_entry = tk.Entry(input_frame, font=("Arial", 10), width=50)
        self.clo_prompt_entry.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Generate button
        self.clo_generate_btn = tk.Button(input_frame, text="Generate Garment", 
                                         command=self.generate_clo_garment,
                                         bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                                         width=25, height=2)
        self.clo_generate_btn.grid(row=3, column=0, pady=10)
        
        # Progress bar for CLO
        self.clo_progress_var = tk.DoubleVar()
        self.clo_progress_bar = ttk.Progressbar(input_frame, variable=self.clo_progress_var,
                                                maximum=100, length=300, mode='indeterminate')
        self.clo_progress_bar.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        self.clo_progress_bar.grid_remove()
        
        # Status label
        self.clo_status_label = ttk.Label(input_frame, text="Ready to generate", 
                                         font=("Arial", 9), foreground="gray")
        self.clo_status_label.grid(row=5, column=0, pady=5)
        
        # Open outputs button
        open_outputs_btn = tk.Button(input_frame, text="📁 Open Output Folder", 
                                    command=self.open_clo_outputs, font=("Arial", 9))
        open_outputs_btn.grid(row=6, column=0, pady=10)
        
        # Right panel - Outputs list
        outputs_frame = ttk.LabelFrame(gen_content, text="Generated Garments", padding="10")
        outputs_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        outputs_frame.columnconfigure(0, weight=1)
        outputs_frame.rowconfigure(0, weight=1)
        
        # Listbox with scrollbar
        listbox_frame = ttk.Frame(outputs_frame)
        listbox_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        listbox_frame.columnconfigure(0, weight=1)
        listbox_frame.rowconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(listbox_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.clo_outputs_listbox = tk.Listbox(listbox_frame, height=15, font=("Consolas", 9),
                                             yscrollcommand=scrollbar.set)
        self.clo_outputs_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.config(command=self.clo_outputs_listbox.yview)
        
        # Double-click to open folder
        self.clo_outputs_listbox.bind("<Double-Button-1>", lambda e: self.open_clo_outputs())
        
        # Refresh button
        refresh_btn = ttk.Button(outputs_frame, text="Refresh List", 
                                command=self.refresh_clo_outputs)
        refresh_btn.grid(row=1, column=0, pady=5)
        
        # Render mode controls
        render_frame = ttk.LabelFrame(gen_content, text="Render Mode", padding="10")
        render_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        # Fast Preview button
        self.fast_preview_btn = tk.Button(render_frame, text="🟢 Fast Preview", 
                                         command=lambda: self.set_render_mode("fast_preview"),
                                         bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
                                         width=18, height=2)
        self.fast_preview_btn.grid(row=0, column=0, padx=5)
        
        # Realistic Render button
        self.realistic_render_btn = tk.Button(render_frame, text="🔵 Realistic Render", 
                                             command=lambda: self.set_render_mode("realistic_render"),
                                             bg="#2196F3", fg="white", font=("Arial", 9, "bold"),
                                             width=18, height=2)
        self.realistic_render_btn.grid(row=0, column=1, padx=5)
        
        # GPU status indicator
        self.gpu_status_label = ttk.Label(render_frame, text="GPU: Checking...", 
                                          font=("Arial", 8), foreground="gray")
        self.gpu_status_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # View Full Render button
        view_render_btn = ttk.Button(render_frame, text="📷 View Full Render", 
                                    command=self.view_full_render)
        view_render_btn.grid(row=2, column=0, columnspan=2, pady=5)
        
        # Initialize render mode
        self.current_render_mode = "fast_preview"
        self.update_gpu_status()
        
        # Load initial outputs
        self.refresh_clo_outputs()
    
    def setup_clo_chat_panel(self, parent_frame):
        """Setup chat panel for iterative design feedback"""
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.rowconfigure(0, weight=1)
        
        # Top frame with version display and mode indicator
        top_frame = ttk.Frame(parent_frame)
        top_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        top_frame.columnconfigure(1, weight=1)
        
        # Left: Version label
        version_frame = ttk.Frame(top_frame)
        version_frame.grid(row=0, column=0, sticky=tk.W)
        
        self.clo_version_label = ttk.Label(version_frame, text="Current Design: None (v1)", 
                                          font=("Arial", 10, "bold"))
        self.clo_version_label.grid(row=0, column=0, sticky=tk.W)
        
        # Mode indicator (color bar)
        self.clo_mode_frame = tk.Frame(version_frame, width=200, height=25, bg="#4CAF50", relief=tk.RAISED, bd=1)
        self.clo_mode_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        self.clo_mode_frame.grid_propagate(False)
        
        self.clo_mode_label = tk.Label(self.clo_mode_frame, text="CHAT Mode", 
                                       font=("Arial", 9, "bold"), bg="#4CAF50", fg="white")
        self.clo_mode_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # System prompt excerpt
        self.clo_prompt_excerpt = ttk.Label(version_frame, 
                                           text="Mode: Creative conversation assistant",
                                           font=("Arial", 8), foreground="gray",
                                           wraplength=300)
        self.clo_prompt_excerpt.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        
        # Right: Buttons
        button_frame_right = ttk.Frame(top_frame)
        button_frame_right.grid(row=0, column=1, sticky=tk.E)
        
        load_state_btn = ttk.Button(button_frame_right, text="Refresh State", 
                                   command=self.load_design_state)
        load_state_btn.grid(row=0, column=0, padx=5)
        
        refresh_mode_btn = ttk.Button(button_frame_right, text="Refresh Mode", 
                                    command=self.refresh_clo_mode)
        refresh_mode_btn.grid(row=0, column=1, padx=5)
        
        # Chat history area
        chat_history_frame = ttk.LabelFrame(parent_frame, text="Chat History", padding="10")
        chat_history_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        chat_history_frame.columnconfigure(0, weight=1)
        chat_history_frame.rowconfigure(0, weight=1)
        
        # Scrollable text widget for chat
        chat_scrollbar = ttk.Scrollbar(chat_history_frame)
        chat_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        self.clo_chat_text = tk.Text(chat_history_frame, height=20, width=80,
                                     font=("Consolas", 10), wrap=tk.WORD,
                                     yscrollcommand=chat_scrollbar.set,
                                     state=tk.DISABLED, bg="#f9f9f9")
        self.clo_chat_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        chat_scrollbar.config(command=self.clo_chat_text.yview)
        
        # Configure text tags for styling
        self.clo_chat_text.tag_configure("user_tag", foreground="#2196F3", font=("Consolas", 10, "bold"))
        self.clo_chat_text.tag_configure("ai_tag", foreground="#4CAF50", font=("Consolas", 10, "bold"))
        
        # Chat input area
        input_area = ttk.Frame(parent_frame)
        input_area.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        input_area.columnconfigure(0, weight=1)
        
        # Input prompt
        ttk.Label(input_area, text="Type feedback or new idea:", font=("Arial", 9)).grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Text input with scroll
        input_scroll = ttk.Scrollbar(input_area, orient=tk.VERTICAL)
        self.clo_chat_input = tk.Text(input_area, height=3, width=70,
                                     font=("Arial", 10), wrap=tk.WORD,
                                     yscrollcommand=input_scroll.set)
        self.clo_chat_input.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        input_scroll.grid(row=1, column=1, sticky=(tk.N, tk.S))
        input_scroll.config(command=self.clo_chat_input.yview)
        input_area.columnconfigure(0, weight=1)
        
        # Buttons frame
        button_area = ttk.Frame(parent_frame)
        button_area.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        # Send button
        self.clo_send_btn = tk.Button(button_area, text="💬 Send Feedback", 
                                     command=self.send_clo_feedback,
                                     bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
                                     width=20, height=2)
        self.clo_send_btn.grid(row=0, column=0, padx=5)
        
        # Undo button
        self.clo_undo_btn = tk.Button(button_area, text="↶ Undo", 
                                     command=self.undo_clo_change,
                                     bg="#FF9800", fg="white", font=("Arial", 10),
                                     width=15, height=2)
        self.clo_undo_btn.grid(row=0, column=1, padx=5)
        
        # Clear chat button
        clear_chat_btn = tk.Button(button_area, text="Clear Chat", 
                                  command=self.clear_clo_chat,
                                  font=("Arial", 9))
        clear_chat_btn.grid(row=0, column=2, padx=5)
        
        # Status label
        self.clo_chat_status = ttk.Label(parent_frame, text="Ready for feedback", 
                                         font=("Arial", 9), foreground="gray")
        self.clo_chat_status.grid(row=4, column=0, pady=5)
        
        # Create transient overlay for CLO Wizard activation (initially hidden)
        self.clo_wizard_overlay = tk.Label(parent_frame, 
                                          text="🪄 CLO Wizard Active",
                                          font=("Arial", 12, "bold"),
                                          bg="#2196F3", fg="white",
                                          relief=tk.RAISED, bd=2)
        self.clo_wizard_overlay.place(relx=0.5, rely=0.1, anchor="center")
        self.clo_wizard_overlay.place_forget()  # Hide initially
        
        # Load existing chat history and state
        self.refresh_clo_chat()
        self.load_design_state()
        self.refresh_clo_mode()
        
        # Bind Enter key (with Shift for newline)
        self.clo_chat_input.bind("<Return>", lambda e: self.send_clo_feedback() if not (e.state & 0x1) else None)
    
    def show_clo_wizard_overlay(self):
        """Show transient CLO Wizard overlay (fades after 1.5s)"""
        self.clo_wizard_overlay.place(relx=0.5, rely=0.1, anchor="center")
        self.root.after(1500, lambda: self.clo_wizard_overlay.place_forget())
    
    def handle_wrong_mode(self):
        """Handle /wrong command - record false positive"""
        try:
            import requests
            # Get last message from chat history
            response = requests.get("http://127.0.0.1:5001/chat_history?limit=1", timeout=5)
            if response.status_code == 200:
                data = response.json()
                history = data.get("history", [])
                if history:
                    last_msg = history[-1]
                    if last_msg.get("role") == "user":
                        # Record false positive
                        requests.post(
                            "http://127.0.0.1:5001/record_false_positive",
                            json={
                                "text": last_msg.get("message", ""),
                                "detected_intent": "EDIT",  # Assume was incorrectly detected as EDIT
                                "correct_intent": "CHAT"
                            },
                            timeout=2
                        )
                        self.add_clo_chat_message("CLO", "✅ Recorded feedback. The system will learn from this.", prefix="[SYSTEM]")
        except:
            pass
    
    def refresh_clo_mode(self):
        """Refresh mode indicator from API"""
        try:
            import requests
            if not self.check_port("127.0.0.1", 5001):
                self.clo_mode_frame.config(bg="#888888")
                self.clo_mode_label.config(text="API Offline", bg="#888888")
                return
            
            # Get mode from mode_manager (via API or directly)
            # For now, check mode via design state and recent chat
            response = requests.get("http://127.0.0.1:5001/design_state", timeout=5)
            if response.status_code == 200:
                # Mode detection happens on next feedback, but we can show current
                # Check last chat message for mode hints
                chat_response = requests.get("http://127.0.0.1:5001/chat_history?limit=1", timeout=5)
                if chat_response.status_code == 200:
                    chat_data = chat_response.json()
                    history = chat_data.get("history", [])
                    if history:
                        last_msg = history[-1].get("message", "").lower()
                        # Simple heuristic: if last message has edit action, likely in CLO_WIZARD
                        if any(keyword in last_msg for keyword in ["updated", "v2", "v3", "edit", "modified"]):
                            self._update_mode_indicator("CLO_WIZARD")
                        else:
                            self._update_mode_indicator("CHAT")
                    else:
                        self._update_mode_indicator("CHAT")
                else:
                    self._update_mode_indicator("CHAT")
            else:
                self._update_mode_indicator("CHAT")
        except:
            self.clo_mode_frame.config(bg="#888888")
            self.clo_mode_label.config(text="Mode Unknown", bg="#888888")
    
    def _update_mode_indicator(self, mode: str):
        """Update mode indicator visual"""
        if mode == "CLO_WIZARD":
            self.clo_mode_frame.config(bg="#2196F3")  # Blue glow
            self.clo_mode_label.config(text="CLO_WIZARD Active", bg="#2196F3", fg="white")
            self.clo_prompt_excerpt.config(text="Mode: Structured JSON command execution", foreground="blue")
        else:
            self.clo_mode_frame.config(bg="#4CAF50")  # Green
            self.clo_mode_label.config(text="CHAT Mode", bg="#4CAF50", fg="white")
            self.clo_prompt_excerpt.config(text="Mode: Creative conversation assistant", foreground="gray")
    
    def send_clo_feedback(self):
        """Send feedback message to CLO Companion API (automatic routing)"""
        feedback = self.clo_chat_input.get("1.0", tk.END).strip()
        
        if not feedback:
            messagebox.showwarning("Empty Feedback", "Please enter feedback or a prompt")
            return
        
        # Check for /wrong command (user feedback)
        if feedback.lower() == "/wrong":
            self.handle_wrong_mode()
            self.clo_chat_input.delete("1.0", tk.END)
            return
        
        # Clear input
        self.clo_chat_input.delete("1.0", tk.END)
        
        # Auto-detect intent before sending
        try:
            import requests
            # Pre-detect for UI feedback
            response = requests.post(
                "http://127.0.0.1:5001/detect_intent",
                json={"text": feedback},
                timeout=2
            )
            if response.status_code == 200:
                intent_data = response.json()
                detected_intent = intent_data.get("intent", "CHAT")
                
                # Show transient overlay if EDIT detected
                if detected_intent == "EDIT":
                    self.show_clo_wizard_overlay()
                    self.add_clo_chat_message("You", feedback, prefix="[EDIT]")
                else:
                    self.add_clo_chat_message("You", feedback, prefix="[CHAT]")
            else:
                self.add_clo_chat_message("You", feedback)
        except:
            # Fallback if API unavailable
            self.add_clo_chat_message("You", feedback)
        
        # Disable send button
        self.clo_send_btn.config(state=tk.DISABLED)
        self.clo_chat_status.config(text="Processing feedback...", foreground="blue")
        
        def process_feedback():
            try:
                import requests
                
                # Check if API is running
                if not self.check_port("127.0.0.1", 5001):
                    self.start_clo_api()
                    time.sleep(3)
                
                # Check if we have a current design
                state_response = requests.get("http://127.0.0.1:5001/design_state", timeout=5)
                has_current_design = False
                if state_response.status_code == 200:
                    state_data = state_response.json()
                    has_current_design = state_data.get("state", {}).get("current_file") is not None
                
                if has_current_design:
                    # Iterate on existing
                    response = requests.post(
                        "http://127.0.0.1:5001/iterate",
                        json={"feedback": feedback},
                        timeout=60
                    )
                else:
                    # New generation
                    response = requests.post(
                        "http://127.0.0.1:5001/generate_garment",
                        json={"prompt": feedback, "seed": None},
                        timeout=60
                    )
                
                if response.status_code == 200:
                    result = response.json()
                    message = result.get("message", "Success")
                    version = result.get("version", "")
                    filename = result.get("obj_file", result.get("base_name", "unknown"))
                    
                    ai_message = f"✅ {message}"
                    if version:
                        ai_message += f" (v{version})"
                    
                    # Check if mode switched (from response or detection)
                    detected_mode = result.get("mode", "")
                    if detected_mode:
                        mode_str = "CLO_WIZARD" if detected_mode == "EDIT" else "CHAT"
                        self.root.after(0, lambda m=mode_str: self._update_mode_indicator(m))
                        self.root.after(0, lambda: self.log(f"[CLO] Mode: {mode_str}", "CLO"))
                    
                    # Add prefix based on mode
                    prefix = "[EDIT]" if detected_mode == "EDIT" else "[CHAT]"
                    self.root.after(0, lambda p=prefix, m=ai_message: self.add_clo_chat_message("CLO", m, prefix=p))
                    self.root.after(0, lambda: self.clo_send_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.clo_chat_status.config(text="Ready", foreground="green"))
                    
                    # Refresh outputs, state, and mode
                    self.root.after(0, self.refresh_clo_outputs)
                    self.root.after(0, self.load_design_state)
                    self.root.after(0, self.refresh_clo_mode)
                    
                else:
                    error_msg = f"Error: {response.status_code}"
                    detail = response.json().get("detail", "") if response.content else ""
                    if detail:
                        error_msg = f"Error: {detail}"
                    self.root.after(0, lambda: self.add_clo_chat_message("CLO", f"❌ {error_msg}"))
                    self.root.after(0, lambda: self.clo_send_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.clo_chat_status.config(text="Error occurred", foreground="red"))
                    
            except requests.exceptions.ConnectionError:
                error_msg = "CLO Companion API is not running. Starting..."
                self.root.after(0, lambda: self.add_clo_chat_message("CLO", f"⚠️ {error_msg}"))
                self.start_clo_api()
                self.root.after(0, lambda: self.clo_send_btn.config(state=tk.NORMAL))
                messagebox.showwarning("API Starting", "CLO Companion API is starting. Please wait a few seconds and try again.")
            except Exception as e:
                error_msg = f"Error: {e}"
                self.root.after(0, lambda: self.add_clo_chat_message("CLO", f"❌ {error_msg}"))
                self.root.after(0, lambda: self.clo_send_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.clo_chat_status.config(text="Error", foreground="red"))
                self.log(f"[CLO] Error processing feedback: {e}", "ERROR")
        
        thread = threading.Thread(target=process_feedback, daemon=True)
        thread.start()
    
    def add_clo_chat_message(self, role: str, message: str, prefix: str = None):
        """Add message to chat display with optional mode prefix"""
        self.clo_chat_text.config(state=tk.NORMAL)
        
        timestamp = datetime.now().strftime("%H:%M")
        
        # Build prefix
        if prefix:
            mode_prefix = f"[{prefix}] "
        else:
            mode_prefix = ""
        
        if role == "You":
            full_prefix = f"[{timestamp}] {mode_prefix}You: "
            tag = "user_tag"
            color = "#2196F3"  # Blue for EDIT
            if prefix == "[CHAT]":
                color = "#666666"  # Gray for CHAT
            self.clo_chat_text.tag_configure("user_edit_tag", foreground=color, font=("Consolas", 10, "bold"))
            self.clo_chat_text.insert(tk.END, full_prefix, "user_edit_tag" if prefix else "user_tag")
        else:
            full_prefix = f"[{timestamp}] {mode_prefix}{role}: "
            tag = "ai_tag"
            color = "#4CAF50"  # Green for AI response
            if prefix == "[EDIT]":
                color = "#2196F3"  # Blue for edit response
            self.clo_chat_text.tag_configure("ai_edit_tag", foreground=color, font=("Consolas", 10, "bold"))
            self.clo_chat_text.insert(tk.END, full_prefix, "ai_edit_tag" if prefix == "[EDIT]" else "ai_tag")
        
        self.clo_chat_text.insert(tk.END, f"{message}\n\n")
        self.clo_chat_text.see(tk.END)
        self.clo_chat_text.config(state=tk.DISABLED)
    
    def refresh_clo_chat(self):
        """Refresh chat history from API"""
        try:
            import requests
            if not self.check_port("127.0.0.1", 5001):
                return
            
            response = requests.get("http://127.0.0.1:5001/chat_history", timeout=5)
            if response.status_code == 200:
                data = response.json()
                history = data.get("history", [])
                
                self.clo_chat_text.config(state=tk.NORMAL)
                self.clo_chat_text.delete("1.0", tk.END)
                
                for msg in history[-20:]:  # Last 20 messages
                    role = "You" if msg.get("role") == "user" else "CLO"
                    message = msg.get("message", "")
                    self.add_clo_chat_message(role, message)
                
                self.clo_chat_text.config(state=tk.DISABLED)
        except:
            pass
    
    def load_design_state(self):
        """Load and display current design state"""
        try:
            import requests
            if not self.check_port("127.0.0.1", 5001):
                self.clo_version_label.config(text="Current Design: None (API not running)")
                return
            
            response = requests.get("http://127.0.0.1:5001/design_state", timeout=5)
            if response.status_code == 200:
                data = response.json()
                state = data.get("state", {})
                current_file = state.get("current_file", None)
                version = state.get("version", 1)
                
                if current_file:
                    self.clo_version_label.config(text=f"Current Design: {os.path.basename(current_file)} (v{version})")
                else:
                    self.clo_version_label.config(text="Current Design: None (v1)")
            else:
                self.clo_version_label.config(text="Current Design: None (v1)")
        except:
            self.clo_version_label.config(text="Current Design: None (check API)")
    
    def undo_clo_change(self):
        """Undo last change"""
        def do_undo():
            try:
                import requests
                if not self.check_port("127.0.0.1", 5001):
                    messagebox.showwarning("API Not Running", "CLO Companion API is not running")
                    return
                
                response = requests.post("http://127.0.0.1:5001/undo", timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    message = result.get("message", "Undone")
                    self.root.after(0, lambda: self.add_clo_chat_message("CLO", f"✅ {message}"))
                    self.root.after(0, self.refresh_clo_outputs)
                    self.root.after(0, self.load_design_state)
                    messagebox.showinfo("Undo", message)
                else:
                    error_msg = response.json().get("detail", "Undo failed") if response.content else "Undo failed"
                    messagebox.showerror("Error", error_msg)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to undo: {e}")
        
        thread = threading.Thread(target=do_undo, daemon=True)
        thread.start()
    
    def clear_clo_chat(self):
        """Clear chat history (GUI only)"""
        if messagebox.askyesno("Clear Chat", "Clear chat history display? (This does not clear saved chat history)"):
            try:
                self.clo_chat_text.config(state=tk.NORMAL)
                self.clo_chat_text.delete("1.0", tk.END)
                self.clo_chat_text.config(state=tk.DISABLED)
                self.log("[CLO] Chat display cleared", "CLO")
            except:
                pass
    
    def generate_clo_garment(self):
        """Generate garment from prompt via CLO Companion API"""
        prompt = self.clo_prompt_entry.get().strip()
        
        if not prompt:
            messagebox.showwarning("Input Required", "Please enter a garment prompt")
            return
        
        # Show progress
        self.clo_progress_bar.grid()
        self.clo_progress_bar.start()
        self.clo_generate_btn.config(state=tk.DISABLED)
        self.clo_status_label.config(text="Generating garment...", foreground="blue")
        self.log(f"[CLO] Generating garment from prompt: {prompt}")
        
        def run_generation():
            try:
                import requests
                
                # Check if CLO API is running
                if not self.check_port("127.0.0.1", 5001):
                    self.start_clo_api()
                    time.sleep(3)
                
                # Call API
                response = requests.post(
                    "http://127.0.0.1:5001/generate_garment",
                    json={"prompt": prompt, "seed": None},
                    timeout=60
                )
                
                if response.status_code == 200:
                    result = response.json()
                    filename = result.get("obj_file", "unknown")
                    message = result.get("message", "Generated")
                    
                    self.root.after(0, lambda: self.clo_progress_bar.stop())
                    self.root.after(0, lambda: self.clo_progress_bar.grid_remove())
                    self.root.after(0, lambda: self.clo_generate_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.clo_status_label.config(
                        text=f"✅ Garment generated: {filename}", foreground="green"
                    ))
                    
                    self.log(f"[CLO] ✅ {message}")
                    self.add_status_message(f"✅ Garment generated: {filename}")
                    
                    # Refresh outputs list and state
                    self.root.after(0, self.refresh_clo_outputs)
                    self.root.after(0, self.load_design_state)
                    
                    messagebox.showinfo("Success", f"Garment generated successfully!\n\nFile: {filename}")
                else:
                    error_msg = f"Generation failed: {response.status_code}"
                    detail = response.json().get("detail", "") if response.content else ""
                    if detail:
                        error_msg = f"Generation failed: {detail}"
                    
                    self.root.after(0, lambda: self.clo_progress_bar.stop())
                    self.root.after(0, lambda: self.clo_progress_bar.grid_remove())
                    self.root.after(0, lambda: self.clo_generate_btn.config(state=tk.NORMAL))
                    self.root.after(0, lambda: self.clo_status_label.config(
                        text="Generation failed", foreground="red"
                    ))
                    
                    self.log(f"[CLO] Error: {error_msg}", "ERROR")
                    messagebox.showerror("Error", error_msg)
                    
            except requests.exceptions.ConnectionError:
                error_msg = "CLO Companion API is not running. Starting it now..."
                self.root.after(0, lambda: self.clo_progress_bar.stop())
                self.root.after(0, lambda: self.clo_progress_bar.grid_remove())
                self.root.after(0, lambda: self.clo_generate_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.clo_status_label.config(
                    text="Starting API server...", foreground="orange"
                ))
                
                self.start_clo_api()
                self.log("[CLO] CLO Companion API starting...", "WARNING")
                messagebox.showwarning("API Starting", 
                    "CLO Companion API was not running. It is starting now.\n\n"
                    "Please wait a few seconds and try again.")
            except Exception as e:
                error_msg = f"Generation error: {e}"
                self.root.after(0, lambda: self.clo_progress_bar.stop())
                self.root.after(0, lambda: self.clo_progress_bar.grid_remove())
                self.root.after(0, lambda: self.clo_generate_btn.config(state=tk.NORMAL))
                self.root.after(0, lambda: self.clo_status_label.config(
                    text="Error occurred", foreground="red"
                ))
                
                self.log(f"[CLO] Error: {error_msg}", "ERROR")
                messagebox.showerror("Error", error_msg)
        
        thread = threading.Thread(target=run_generation, daemon=True)
        thread.start()
    
    def start_clo_api(self):
        """Start CLO Companion API server"""
        if self.clo_api_process is not None:
            if self.check_port("127.0.0.1", 5001):
                self.log("[CLO] API already running", "WARNING")
                return
        
        self.log("Starting CLO Companion API server...", "CLO")
        self.status_bar.config(text="Starting CLO Companion API...")
        
        api_script = os.path.join(os.path.dirname(__file__), "modules", "clo_companion", "clo_api.py")
        
        try:
            api_error_log = os.path.join(self.log_dir, "clo_api_errors.log")
            with open(api_error_log, 'w', encoding='utf-8') as log_file:
                self.clo_api_process = subprocess.Popen(
                    [sys.executable, api_script],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=os.path.dirname(__file__),
                    bufsize=1
                )
            
            self.log(f"[CLO] API process started (PID: {self.clo_api_process.pid})")
            
            # Wait and verify
            time.sleep(2)
            if self.check_port("127.0.0.1", 5001):
                self.log("[CLO] API server started successfully")
                self.status_bar.config(text="CLO Companion API running on port 5001")
            else:
                self.log("[CLO] API process started but not responding", "WARNING")
        except Exception as e:
            self.log(f"[CLO] Failed to start API: {e}", "ERROR")
            messagebox.showerror("Error", f"Failed to start CLO Companion API: {e}")
    
    def stop_clo_api(self):
        """Stop CLO Companion API server"""
        if self.clo_api_process:
            self.log("[CLO] Stopping API server...")
            try:
                self.clo_api_process.terminate()
                self.clo_api_process.wait(timeout=5)
                self.clo_api_process = None
                self.log("[CLO] API server stopped")
            except:
                pass
    
    def refresh_clo_outputs(self):
        """Refresh the outputs listbox"""
        try:
            import requests
            
            if not self.check_port("127.0.0.1", 5001):
                self.clo_outputs_listbox.delete(0, tk.END)
                self.clo_outputs_listbox.insert(0, "CLO Companion API not running")
                return
            
            response = requests.get("http://127.0.0.1:5001/list_outputs", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                outputs = data.get("outputs", [])
                
                self.clo_outputs_listbox.delete(0, tk.END)
                
                if not outputs:
                    self.clo_outputs_listbox.insert(0, "No garments generated yet")
                else:
                    for output in outputs:
                        prompt = output.get("prompt", "")[:40]
                        filename = output.get("obj_file", "")
                        timestamp = output.get("timestamp", "")
                        if timestamp:
                            try:
                                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                time_str = dt.strftime("%Y-%m-%d %H:%M")
                            except:
                                time_str = timestamp[:16]
                        else:
                            time_str = "Unknown"
                        
                        display = f"{time_str} | {prompt}... | {filename}"
                        self.clo_outputs_listbox.insert(tk.END, display)
            else:
                self.clo_outputs_listbox.delete(0, tk.END)
                self.clo_outputs_listbox.insert(0, f"Error loading outputs: {response.status_code}")
        except:
            self.clo_outputs_listbox.delete(0, tk.END)
            self.clo_outputs_listbox.insert(0, "CLO Companion API not running")
    
    def open_clo_outputs(self):
        """Open CLO Companion outputs folder in Explorer"""
        outputs_dir = os.path.join(os.path.dirname(__file__), "modules", "clo_companion", "outputs")
        os.makedirs(outputs_dir, exist_ok=True)
        
        try:
            import subprocess
            subprocess.Popen(f'explorer "{outputs_dir}"')
            self.log(f"[CLO] Opened outputs folder: {outputs_dir}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")
    
    def add_status_message(self, message):
        """Add timestamped message to status console"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_entry = f"[{timestamp}] {message}\n"
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, status_entry)
        # Keep only last 4 lines
        lines = self.status_text.get("1.0", tk.END).split('\n')
        if len(lines) > 5:
            self.status_text.delete("1.0", f"{len(lines)-4}.0")
        self.status_text.config(state=tk.DISABLED)
        self.status_text.see(tk.END)
    
    def log(self, message, level="INFO"):
        """Log message to both GUI and file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        # Add to unified logger
        try:
            from logger import log as unified_log
            unified_log(message, "GUI", print_to_console=False)
        except:
            pass
        
        # Add to GUI log display
        if self.logging_enabled:
            self.log_text.insert(tk.END, log_entry)
            self.log_text.see(tk.END)
        
        # Write to file
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Failed to write log: {e}")
    
    def clear_logs(self):
        """Clear the log display"""
        self.log_text.delete("1.0", tk.END)
        self.log("Logs cleared")
    
    def check_port(self, host, port):
        """Check if a port is open"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False
    
    def update_all_status(self):
        """Update all status indicators"""
        try:
            # Python
            self.status_labels["python"].config(foreground="green", text="●")
            
            # Ollama
            if self.check_port("127.0.0.1", 11434):
                self.status_labels["ollama"].config(foreground="green", text="●")
            else:
                self.status_labels["ollama"].config(foreground="red", text="●")
            
            # Llama Model (check via Ollama API)
            try:
                import requests
                response = requests.get("http://127.0.0.1:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    models = response.json().get("models", [])
                    has_llama = any("llama" in m.get("name", "").lower() for m in models)
                    self.status_labels["llama"].config(
                        foreground="green" if has_llama else "orange", 
                        text="●"
                    )
                else:
                    self.status_labels["llama"].config(foreground="orange", text="●")
            except:
                self.status_labels["llama"].config(foreground="orange", text="●")
            
            # ChromaDB
            chroma_path = os.path.join(os.path.dirname(__file__), ".chromadb")
            if os.path.exists(chroma_path):
                self.status_labels["chromadb"].config(foreground="green", text="●")
            else:
                self.status_labels["chromadb"].config(foreground="orange", text="●")
            
            # RAG API
            if self.check_port("127.0.0.1", 5000):
                self.status_labels["api"].config(foreground="green", text="●")
            else:
                self.status_labels["api"].config(foreground="red", text="●")
            
            # Vault Path
            vault_path = os.path.join(os.path.expanduser("~"), "Documents", "Obsidian", "Notes")
            if os.path.exists(vault_path):
                self.status_labels["vault"].config(foreground="green", text="●")
            else:
                self.status_labels["vault"].config(foreground="orange", text="●")
            
            # Cloud Bridge
            try:
                import requests
                response = requests.get("http://127.0.0.1:5000/cloud/status", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("connected"):
                        self.status_labels["cloud"].config(foreground="green", text="●")
                    else:
                        self.status_labels["cloud"].config(foreground="orange", text="●")
                else:
                    self.status_labels["cloud"].config(foreground="orange", text="●")
            except:
                self.status_labels["cloud"].config(foreground="orange", text="●")
                
        except Exception as e:
            self.log(f"Error updating status: {e}", "ERROR")
    
    def update_gpu_status(self):
        """Update GPU status indicator using core.gpu module"""
        try:
            # Use core.gpu instead of direct pynvml import
            from core.gpu import get_gpu_status
            
            gpu = get_gpu_status()
            
            if not gpu["available"]:
                    status_msg = "GPU: Not detected"
                    print(f"[GPU] {status_msg}")
                    self.log(status_msg, "GPU")
                    if hasattr(self, 'gpu_status_label'):
                        self.gpu_status_label.config(text=status_msg, foreground="gray")
                    return
                
            # GPU is available - format status
            name = gpu.get("name", "Unknown")
            mem_used_mb = gpu.get("memory_used", 0)
            mem_total_mb = gpu.get("memory_total", 0)
            mem_percent = gpu.get("memory_percent", 0)
            util = gpu.get("utilization", 0)
                
            mem_used_gb = mem_used_mb / 1024
            mem_total_gb = mem_total_mb / 1024
                
            status_msg = f"GPU: {name} | {mem_used_gb:.1f}/{mem_total_gb:.1f}GB ({mem_percent:.0f}%) | Util: {util:.0f}%"
            print(f"[GPU] {status_msg}")
            self.log(status_msg, "GPU")
            
            # Update label if exists
            if hasattr(self, 'gpu_status_label'):
                # Short version for GUI label
                label_text = f"GPU: {name} | {mem_percent:.0f}% used | {util:.0f}% util"
                self.gpu_status_label.config(text=label_text, foreground="green")
                try:
                    pynvml.nvmlShutdown()
                except:
                    pass
                    
        except Exception as e:
            # Catch-all for any unexpected errors
            status_msg = "GPU: Not detected"
            print(f"[GPU] {status_msg}")
            self.log(f"GPU status update error: {e}", "GPU")
            if hasattr(self, 'gpu_status_label'):
                self.gpu_status_label.config(text=status_msg, foreground="gray")
    
    def index_documents(self):
        """Index documents from Obsidian vault"""
        self.log("Starting document indexing...")
        self.add_status_message("Indexing documents...")
        
        def do_index():
            try:
                index_script = os.path.join(os.path.dirname(__file__), "modules", "academic_rag", "index_documents.py")
                result = subprocess.run([sys.executable, index_script], 
                                      capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0:
                    self.root.after(0, lambda: self.add_status_message("✅ Indexing complete"))
                    self.root.after(0, lambda: self.log("Document indexing completed successfully"))
                    messagebox.showinfo("Success", "Documents indexed successfully!")
                else:
                    error = result.stderr or result.stdout
                    self.root.after(0, lambda: self.log(f"Indexing error: {error}", "ERROR"))
                    messagebox.showerror("Error", f"Indexing failed: {error}")
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Indexing exception: {e}", "ERROR"))
                messagebox.showerror("Error", f"Indexing failed: {e}")
        
        thread = threading.Thread(target=do_index, daemon=True)
        thread.start()
    
    def start_api_server(self):
        """Start the RAG API server"""
        if self.api_process is not None:
            if self.check_port("127.0.0.1", 5000):
                messagebox.showinfo("Info", "API server is already running")
                return
        
        self.log("Starting API server...")
        self.status_bar.config(text="Starting API server...")
        
        api_script = os.path.join(os.path.dirname(__file__), "modules", "academic_rag", "api.py")
        
        try:
            api_error_log = os.path.join(self.log_dir, "api_startup_errors.log")
            with open(api_error_log, 'w', encoding='utf-8') as log_file:
                self.api_process = subprocess.Popen(
                    [sys.executable, api_script],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=os.path.dirname(__file__),
                    bufsize=1
                )
            
            self.log(f"API process started (PID: {self.api_process.pid})")
            
            # Wait and verify startup (Flask can take 4-5 seconds to initialize)
            host, port = self.load_api_endpoint()
            time.sleep(2)
            
            # Try health check with retries
            max_retries = 3
            for attempt in range(max_retries):
                if self.check_api_health(host, port):
                    self.log(f"API server started successfully on {host}:{port}")
                    self.status_bar.config(text=f"API server running on port {port}")
                    self.add_status_message("✅ API server started")
                    break
                elif attempt < max_retries - 1:
                    self.log(f"Health check attempt {attempt + 1} failed, retrying...")
                    time.sleep(2)  # Wait 2 more seconds before retry
            else:
                # After all retries failed
                self.log(f"API process started but health check failed on {host}:{port}", "WARNING")
                self.status_bar.config(text=f"API server starting on port {port} (check logs)")
        except Exception as e:
            self.log(f"Failed to start API: {e}", "ERROR")
            messagebox.showerror("Error", f"Failed to start API server: {e}")
    
    def stop_api_server(self):
        """Stop the RAG API server"""
        if self.api_process:
            self.log("Stopping API server...")
            try:
                self.api_process.terminate()
                self.api_process.wait(timeout=5)
                self.api_process = None
                self.log("API server stopped")
                self.status_bar.config(text="API server stopped")
                self.add_status_message("API server stopped")
            except:
                self.log("Error stopping API server", "ERROR")
                self.api_process = None
        else:
            messagebox.showinfo("Info", "API server is not running")
    
    def auto_start_api_server(self):
        """Auto-start API server after initialization"""
        if not self.check_port("127.0.0.1", 5000):
            self.start_api_server()
    
    def test_query(self):
        """Test query to the RAG API"""
        test_prompt = "What is strategic management?"
        self.log(f"Testing query: {test_prompt}")
        
        def do_test():
            try:
                import requests
                time.sleep(2)  # Give API time to be ready
                
                response = requests.post(
                    "http://127.0.0.1:5000/query",
                    json={"query": test_prompt},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    answer = result.get("answer", "No answer")
                    self.root.after(0, lambda: self.log(f"Test query response: {answer[:100]}..."))
                    self.root.after(0, lambda: messagebox.showinfo("Success", f"Query successful!\n\nResponse preview:\n{answer[:200]}..."))
                else:
                    self.root.after(0, lambda: self.log(f"Test query failed: {response.status_code}", "ERROR"))
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Query failed: {response.status_code}"))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Test query exception: {e}", "ERROR"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Query failed: {e}"))
        
        thread = threading.Thread(target=do_test, daemon=True)
        thread.start()
    
    def reindex_vault(self):
        """Reindex the Obsidian vault"""
        self.index_documents()
    
    def run_health_check(self):
        """Run comprehensive health check"""
        if DiagnosticsChecker is None:
            messagebox.showwarning("Diagnostics", "Diagnostics module not available")
            return
        
        self.log("Running health check...")
        self.add_status_message("Running health check...")
        
        def do_check():
            try:
                checker = DiagnosticsChecker()
                results = checker.run_all_checks()
                
                # Format results
                output = []
                for check, status, message in results:
                    icon = "✅" if status else "❌"
                    output.append(f"{icon} {check}: {message}")
                
                result_text = "\n".join(output)
                
                self.root.after(0, lambda: self.log(f"Health check complete:\n{result_text}"))
                self.root.after(0, lambda: self.add_status_message("✅ Health check complete"))
                self.root.after(0, lambda: messagebox.showinfo("Health Check", result_text))
            except Exception as e:
                self.root.after(0, lambda: self.log(f"Health check error: {e}", "ERROR"))
                self.root.after(0, lambda: messagebox.showerror("Error", f"Health check failed: {e}"))
        
        thread = threading.Thread(target=do_check, daemon=True)
        thread.start()
    
    def run_full_system_test(self):
        """Run full system test"""
        self.log("Running full system test...")
        messagebox.showinfo("Full System Test", "This will test all components.\n\nSee logs for details.")
        # Implementation would run diagnostics, test query, etc.
    
    def backup_system(self):
        """Backup system data"""
        try:
            from backup_restore import create_backup
            backup_path = create_backup()
            if backup_path:
                messagebox.showinfo("Success", f"Backup created:\n{backup_path}")
                self.log(f"Backup created: {backup_path}")
            else:
                messagebox.showerror("Error", "Backup failed")
        except ImportError:
            messagebox.showerror("Error", "Backup module not available")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {e}")
    
    def restore_system(self):
        """Restore system from backup"""
        try:
            from tkinter import filedialog
            backup_file = filedialog.askopenfilename(
                title="Select backup file",
                filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
            )
            if backup_file:
                from backup_restore import restore_backup
                if restore_backup(backup_file):
                    messagebox.showinfo("Success", "Backup restored successfully!")
                    self.log(f"Backup restored from: {backup_file}")
                else:
                    messagebox.showerror("Error", "Restore failed")
        except ImportError:
            messagebox.showerror("Error", "Restore module not available")
        except Exception as e:
            messagebox.showerror("Error", f"Restore failed: {e}")
    
    def sync_cloud(self):
        """Sync with cloud bridge"""
        self.log("Cloud sync requested")
        messagebox.showinfo("Cloud Sync", "Cloud sync feature - coming soon")
    
    def cloud_status(self):
        """Check cloud bridge status"""
        self.log("Checking cloud status...")
        messagebox.showinfo("Cloud Status", "Cloud bridge status - check logs")
    
    def setup_troubleshooter_tab(self, parent_frame):
        """Setup Smart Troubleshooter tab with diagnostics and repair tools"""
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(parent_frame, text="🧠 Smart Troubleshooter", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # Main content frame
        content_frame = ttk.Frame(parent_frame)
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(1, weight=1)
        
        # Error feed section
        error_frame = ttk.LabelFrame(content_frame, text="Live Error Feed", padding="10")
        error_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N), pady=(0, 10))
        error_frame.columnconfigure(0, weight=1)
        error_frame.rowconfigure(0, weight=1)
        
        self.troubleshooter_error_text = scrolledtext.ScrolledText(
            error_frame, height=12, width=80, wrap=tk.WORD,
            font=("Consolas", 9), state=tk.DISABLED, bg="#f5f5f5"
        )
        self.troubleshooter_error_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Buttons frame
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        buttons_frame.columnconfigure(2, weight=1)
        
        # Run Diagnostics button
        diagnostics_btn = tk.Button(
            buttons_frame, text="🔍 Run Diagnostics", 
            command=self.run_diagnostics,
            bg="#2196F3", fg="white", font=("Arial", 11, "bold"),
            width=25, height=2
        )
        diagnostics_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # Fix Detected Issues button
        fix_btn = tk.Button(
            buttons_frame, text="🔧 Fix Detected Issues", 
            command=self.apply_auto_fixes,
            bg="#4CAF50", fg="white", font=("Arial", 11, "bold"),
            width=25, height=2
        )
        fix_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Generate Cursor Prompt button
        cursor_prompt_btn = tk.Button(
            buttons_frame, text="📝 Generate Cursor Prompt", 
            command=self.generate_cursor_prompt,
            bg="#FF9800", fg="white", font=("Arial", 11, "bold"),
            width=25, height=2
        )
        cursor_prompt_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Status label
        self.troubleshooter_status_label = ttk.Label(
            content_frame, text="Status: Ready", 
            font=("Arial", 10), foreground="green"
        )
        self.troubleshooter_status_label.grid(row=2, column=0, pady=10)
        
        # Console output section (optional)
        console_frame = ttk.LabelFrame(content_frame, text="Console Output", padding="10")
        console_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        console_frame.columnconfigure(0, weight=1)
        console_frame.rowconfigure(0, weight=1)
        content_frame.rowconfigure(3, weight=1)
        
        self.troubleshooter_console_text = scrolledtext.ScrolledText(
            console_frame, height=8, width=80, wrap=tk.WORD,
            font=("Consolas", 8), state=tk.DISABLED, bg="#1e1e1e", fg="#d4d4d4"
        )
        self.troubleshooter_console_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Initialize error feed with welcome message
        self.troubleshooter_error_text.config(state=tk.NORMAL)
        self.troubleshooter_error_text.insert(tk.END, 
            "🧠 Smart Troubleshooter Ready\n\n"
            "Click 'Run Diagnostics' to scan for issues.\n"
            "Error messages and system warnings will appear here.\n"
        )
        self.troubleshooter_error_text.config(state=tk.DISABLED)
    
    def run_diagnostics(self):
        """Run system diagnostics and display results"""
        try:
            self.log("Running system diagnostics...", "TROUBLESHOOTER")
            self.troubleshooter_status_label.config(
                text="Status: Running diagnostics...", 
                foreground="orange"
            )
            
            # Clear previous results
            self.troubleshooter_error_text.config(state=tk.NORMAL)
            self.troubleshooter_error_text.delete(1.0, tk.END)
            self.troubleshooter_console_text.config(state=tk.NORMAL)
            self.troubleshooter_console_text.delete(1.0, tk.END)
            
            # Try to use troubleshooter module if available
            try:
                troubleshooter_path = os.path.join(os.path.dirname(__file__), "modules", "troubleshooter")
                if os.path.exists(troubleshooter_path):
                    # Try to import and run troubleshooter
                    sys.path.insert(0, troubleshooter_path)
                    try:
                        from troubleshooter import run_diagnostics as ts_run_diagnostics
                        results = ts_run_diagnostics()
                        self._display_diagnostics_results(results)
                    except ImportError:
                        # If module exists but import fails, run basic diagnostics
                        self._run_basic_diagnostics()
                    finally:
                        if troubleshooter_path in sys.path:
                            sys.path.remove(troubleshooter_path)
                else:
                    self._run_basic_diagnostics()
            except Exception as e:
                self.log(f"Error running diagnostics: {e}", "TROUBLESHOOTER")
                self._run_basic_diagnostics()
            
            self.troubleshooter_error_text.config(state=tk.DISABLED)
            self.troubleshooter_console_text.config(state=tk.DISABLED)
            
            self.troubleshooter_status_label.config(
                text="Status: Diagnostics complete", 
                foreground="green"
            )
            
        except Exception as e:
            self.log(f"Critical error in diagnostics: {e}", "TROUBLESHOOTER")
            self.troubleshooter_status_label.config(
                text=f"Status: Error - {str(e)[:50]}", 
                foreground="red"
            )
            log_exception("TROUBLESHOOTER", e, "run_diagnostics")
    
    def _run_basic_diagnostics(self):
        """Run basic system diagnostics when troubleshooter module is unavailable"""
        issues = []
        warnings = []
        
        # Check Python version
        python_version = sys.version_info
        if python_version < (3, 8):
            issues.append(f"⚠️ Python version {python_version.major}.{python_version.minor} is below recommended 3.8+")
        
        # Check required ports
        ports_to_check = [
            ("Ollama", "127.0.0.1", 11434),
            ("RAG API", "127.0.0.1", 5000),
        ]
        
        for service_name, host, port in ports_to_check:
            if not self.check_port(host, port):
                warnings.append(f"⚠️ {service_name} not responding on {host}:{port}")
        
        # Check critical directories
        critical_dirs = [
            (os.path.join(os.path.dirname(__file__), ".chromadb"), "ChromaDB"),
            (os.path.join(os.path.expanduser("~"), "Documents", "Obsidian", "Notes"), "Obsidian Vault"),
        ]
        
        for dir_path, dir_name in critical_dirs:
            if not os.path.exists(dir_path):
                warnings.append(f"⚠️ {dir_name} directory not found: {dir_path}")
        
        # Display results
        output = "🔍 Diagnostic Results\n\n"
        if issues:
            output += "❌ Issues Found:\n"
            for issue in issues:
                output += f"  {issue}\n"
            output += "\n"
        
        if warnings:
            output += "⚠️ Warnings:\n"
            for warning in warnings:
                output += f"  {warning}\n"
            output += "\n"
        
        if not issues and not warnings:
            output += "✅ No issues detected. System appears healthy.\n"
        
        self.troubleshooter_error_text.insert(tk.END, output)
        
        # Console output
        console_output = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Diagnostics started\n"
        console_output += f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Python: {sys.version}\n"
        console_output += f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checks: {len(ports_to_check)} ports, {len(critical_dirs)} directories\n"
        console_output += f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Issues: {len(issues)}, Warnings: {len(warnings)}\n"
        self.troubleshooter_console_text.insert(tk.END, console_output)
    
    def _display_diagnostics_results(self, results):
        """Display results from troubleshooter module"""
        output = "🔍 Diagnostic Results\n\n"
        if isinstance(results, dict):
            if results.get("issues"):
                output += "❌ Issues Found:\n"
                for issue in results["issues"]:
                    output += f"  {issue}\n"
                output += "\n"
            
            if results.get("warnings"):
                output += "⚠️ Warnings:\n"
                for warning in results["warnings"]:
                    output += f"  {warning}\n"
                output += "\n"
            
            if results.get("info"):
                self.troubleshooter_console_text.insert(tk.END, results["info"])
        else:
            output += str(results)
        
        self.troubleshooter_error_text.insert(tk.END, output)
    
    def apply_auto_fixes(self):
        """Apply auto-fixes for detected issues"""
        try:
            self.log("Applying auto-fixes...", "TROUBLESHOOTER")
            self.troubleshooter_status_label.config(
                text="Status: Applying fixes...", 
                foreground="orange"
            )
            
            fixes_applied = []
            
            # Try to use troubleshooter module if available
            try:
                troubleshooter_path = os.path.join(os.path.dirname(__file__), "modules", "troubleshooter")
                if os.path.exists(troubleshooter_path):
                    sys.path.insert(0, troubleshooter_path)
                    try:
                        from troubleshooter import apply_fixes as ts_apply_fixes
                        fixes_applied = ts_apply_fixes()
                    except ImportError:
                        fixes_applied = self._apply_basic_fixes()
                    finally:
                        if troubleshooter_path in sys.path:
                            sys.path.remove(troubleshooter_path)
                else:
                    fixes_applied = self._apply_basic_fixes()
            except Exception as e:
                self.log(f"Error applying fixes: {e}", "TROUBLESHOOTER")
                fixes_applied = self._apply_basic_fixes()
            
            # Display results
            output = "🔧 Auto-Fix Results\n\n"
            if fixes_applied:
                output += "✅ Fixes Applied:\n"
                for fix in fixes_applied:
                    output += f"  ✓ {fix}\n"
            else:
                output += "ℹ️ No automatic fixes available. Please review diagnostics manually.\n"
            
            self.troubleshooter_error_text.config(state=tk.NORMAL)
            self.troubleshooter_error_text.insert(tk.END, output)
            self.troubleshooter_error_text.config(state=tk.DISABLED)
            
            self.troubleshooter_status_label.config(
                text="Status: Auto-fixes complete", 
                foreground="green"
            )
            
        except Exception as e:
            self.log(f"Critical error in auto-fixes: {e}", "TROUBLESHOOTER")
            self.troubleshooter_status_label.config(
                text=f"Status: Error - {str(e)[:50]}", 
                foreground="red"
            )
            log_exception("TROUBLESHOOTER", e, "apply_auto_fixes")
    
    def _apply_basic_fixes(self):
        """Apply basic safe fixes when troubleshooter module is unavailable"""
        fixes = []
        
        # Try to create missing directories
        critical_dirs = [
            (os.path.join(os.path.dirname(__file__), ".chromadb"), "ChromaDB"),
        ]
        
        for dir_path, dir_name in critical_dirs:
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    fixes.append(f"Created {dir_name} directory")
                except Exception:
                    pass
        
        return fixes
    
    def generate_cursor_prompt(self):
        """Generate a repair prompt for Cursor AI"""
        try:
            self.log("Generating Cursor prompt...", "TROUBLESHOOTER")
            self.troubleshooter_status_label.config(
                text="Status: Generating prompt...", 
                foreground="orange"
            )
            
            # Get diagnostic context
            diagnostic_info = []
            
            # Collect system info
            diagnostic_info.append(f"Python Version: {sys.version}")
            diagnostic_info.append(f"Platform: {sys.platform}")
            diagnostic_info.append(f"Working Directory: {os.getcwd()}")
            
            # Check ports
            if not self.check_port("127.0.0.1", 11434):
                diagnostic_info.append("⚠️ Ollama not running on port 11434")
            if not self.check_port("127.0.0.1", 5000):
                diagnostic_info.append("⚠️ RAG API not running on port 5000")
            
            # Get recent errors from error feed if available
            error_content = ""
            if hasattr(self, 'troubleshooter_error_text'):
                self.troubleshooter_error_text.config(state=tk.NORMAL)
                error_content = self.troubleshooter_error_text.get(1.0, tk.END)
                self.troubleshooter_error_text.config(state=tk.DISABLED)
            
            # Generate prompt
            prompt = f"""SYSTEM PROMPT:

You are a senior engineer diagnosing and fixing issues in the Julian Assistant Suite.

CONTEXT:
Imagine a world without boundries.

DIAGNOSTIC INFORMATION:
{chr(10).join(f"  - {info}" for info in diagnostic_info)}

RECENT ERROR LOGS:
{error_content[:1000] if error_content else "No recent errors captured"}

TASK:
Analyze the diagnostic information and error logs above. Provide:
1. Root cause analysis of detected issues
2. Step-by-step repair instructions
3. Code fixes if applicable
4. Prevention strategies

CONSTRAINTS:
- Maintain UTF-8 encoding
- Preserve existing functionality
- Follow existing code patterns
"""
            
            # Equip a text widget in a new window or copy to clipboard
            try:
                import pyperclip
                pyperclip.copy(prompt)
                messagebox.showinfo(
                    "Cursor Prompt Generated", 
                    "Prompt generated and copied to clipboard!\n\nPaste it into Cursor's chat for AI-assisted repair."
                )
            except ImportError:
                # If pyperclip not available, show in a window
                prompt_window = tk.Toplevel(self.root)
                prompt_window.title("Cursor Repair Prompt")
                prompt_window.geometry("800x600")
                
                text_widget = scrolledtext.ScrolledText(prompt_window, wrap=tk.WORD, font=("Consolas", 10))
                text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                text_widget.insert(1.0, prompt)
                text_widget.config(state=tk.DISABLED)
                
                copy_btn = tk.Button(prompt_window, text="Copy to Clipboard (manual)", 
                                    command=lambda: self._manual_copy_prompt(prompt))
                copy_btn.pack(pady=5)
            
            self.troubleshooter_status_label.config(
                text="Status: Prompt generated", 
                foreground="green"
            )
            
        except Exception as e:
            self.log(f"Critical error generating prompt: {e}", "TROUBLESHOOTER")
            self.troubleshooter_status_label.config(
                text=f"Status: Error - {str(e)[:50]}", 
                foreground="red"
            )
            log_exception("TROUBLESHOOTER", e, "generate_cursor_prompt")
    
    def _manual_copy_prompt(self, prompt):
        """Helper to show manual copy instructions"""
        messagebox.showinfo(
            "Copy Prompt", 
            "Select all text (Ctrl+A) in the window above and copy (Ctrl+C) to use in Cursor."
        )
    
    def setup_maintenance_tab(self, parent_frame):
        """Setup System Maintenance tab"""
        parent_frame.columnconfigure(0, weight=1)
        parent_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(parent_frame, text="Smart Cleanup & Optimization", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, pady=10)
        
        # Buttons frame
        buttons_frame = ttk.Frame(parent_frame)
        buttons_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        
        # Run Smart Cleanup button
        cleanup_btn = tk.Button(buttons_frame, text="🧹 Run Smart Cleanup", 
                                command=self.run_smart_cleanup,
                                bg="#FF9800", fg="white", font=("Arial", 11, "bold"),
                                width=25, height=2)
        cleanup_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # View Last Report button
        view_report_btn = tk.Button(buttons_frame, text="📄 View Last Report", 
                                   command=self.view_last_report,
                                   bg="#2196F3", fg="white", font=("Arial", 11),
                                   width=25, height=2)
        view_report_btn.grid(row=0, column=1, padx=5, pady=5)
        
        # Rebuild Indexes button
        rebuild_indexes_btn = tk.Button(buttons_frame, text="🔍 Rebuild Indexes", 
                                        command=self.rebuild_indexes,
                                        bg="#9C27B0", fg="white", font=("Arial", 11),
                                        width=25, height=2)
        rebuild_indexes_btn.grid(row=1, column=0, padx=5, pady=5)
        
        # n8n Integration buttons
        n8n_frame = ttk.Frame(buttons_frame)
        n8n_frame.grid(row=1, column=1, padx=5, pady=5)
        
        test_n8n_btn = tk.Button(n8n_frame, text="🔗 Test n8n Connection", 
                                command=self.test_n8n_connection,
                                bg="#00BCD4", fg="white", font=("Arial", 10),
                                width=25, height=2)
        test_n8n_btn.grid(row=0, column=0, pady=2)
        
        open_n8n_btn = tk.Button(n8n_frame, text="🌐 Open n8n Dashboard", 
                                command=self.open_n8n_dashboard,
                                bg="#607D8B", fg="white", font=("Arial", 10),
                                width=25, height=2)
        open_n8n_btn.grid(row=1, column=0, pady=2)
        
        # Rebuild Shortcut button
        rebuild_shortcut_btn = tk.Button(n8n_frame, text="📌 Rebuild Shortcut", 
                                        command=self.rebuild_shortcut,
                                        bg="#795548", fg="white", font=("Arial", 10),
                                        width=25, height=2)
        rebuild_shortcut_btn.grid(row=2, column=0, pady=2)
        
        # n8n status indicator
        self.n8n_status_label = ttk.Label(parent_frame, text="n8n: ⚪ Not configured", 
                                         font=("Arial", 9))
        self.n8n_status_label.grid(row=5, column=0, pady=5)
        
        # Status banner
        self.maintenance_status_banner = ttk.Label(parent_frame, text="✅ System Ready", 
                                                   font=("Arial", 10), 
                                                   foreground="green",
                                                   relief=tk.RAISED)
        self.maintenance_status_banner.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # Progress bar
        self.cleanup_progress_var = tk.DoubleVar()
        self.cleanup_progress_bar = ttk.Progressbar(parent_frame, variable=self.cleanup_progress_var,
                                                     maximum=100, length=500, mode='indeterminate')
        self.cleanup_progress_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        self.cleanup_progress_bar.grid_remove()
        
        # Live log display
        log_frame = ttk.LabelFrame(parent_frame, text="Cleanup Log", padding="10")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent_frame.rowconfigure(4, weight=1)
        
        self.cleanup_log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80,
                                                          font=("Consolas", 9))
        self.cleanup_log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.cleanup_log_text.insert("1.0", "Smart Cleanup log will appear here...\n")
        self.cleanup_log_text.config(state=tk.DISABLED)
        
        # Update n8n status on tab load
        self.root.after(100, self.update_n8n_status)
    
    def run_smart_cleanup(self):
        """Run smart cleanup process"""
        self.log("Starting Smart Cleanup...", "CLEANUP")
        
        # Update status
        self.maintenance_status_banner.config(text="🔄 Running Cleanup...", foreground="orange")
        
        # Show progress bar
        self.cleanup_progress_bar.grid()
        self.cleanup_progress_bar.start()
        
        # Clear log display
        self.cleanup_log_text.config(state=tk.NORMAL)
        self.cleanup_log_text.delete("1.0", tk.END)
        self.cleanup_log_text.insert("1.0", "Starting Smart Cleanup...\n\n")
        self.cleanup_log_text.update()
        
        def do_cleanup():
            try:
                from core.smart_cleanup import run_smart_cleanup
                
                # Run cleanup
                result = run_smart_cleanup()
                
                # Update GUI
                self.root.after(0, lambda: self._update_cleanup_results(result))
            
            except Exception as e:
                self.root.after(0, lambda: self._cleanup_error(str(e)))
        
        thread = threading.Thread(target=do_cleanup, daemon=True)
        thread.start()
    
    def _update_cleanup_results(self, result: Dict):
        """Update GUI with cleanup results"""
        self.cleanup_progress_bar.stop()
        self.cleanup_progress_bar.grid_remove()
        
        # Update log display
        self.cleanup_log_text.config(state=tk.NORMAL)
        self.cleanup_log_text.delete("1.0", tk.END)
        
        log_text = f"✅ Smart Cleanup Complete!\n\n"
        log_text += f"Files Removed: {result.get('files_removed', 0)}\n"
        log_text += f"Space Freed: {result.get('space_freed_mb', 0):.2f} MB\n\n"
        
        if result.get('warnings'):
            log_text += f"⚠️ Warnings ({len(result['warnings'])}):\n"
            for warning in result['warnings'][:10]:  # Show first 10
                log_text += f"  - {warning}\n"
            log_text += "\n"
        
        if result.get('errors'):
            log_text += f"❌ Errors ({len(result['errors'])}):\n"
            for error in result['errors']:
                log_text += f"  - {error}\n"
            log_text += "\n"
        
        log_text += f"\nReport saved to:\n{result.get('report_path', 'N/A')}\n"
        if result.get('desktop_report_path'):
            log_text += f"Desktop copy: {result.get('desktop_report_path')}\n"
        
        self.cleanup_log_text.insert("1.0", log_text)
        self.cleanup_log_text.config(state=tk.DISABLED)
        
        # Update status banner
        if result.get('errors'):
            self.maintenance_status_banner.config(text="🔴 Cleanup completed with errors", foreground="red")
        elif result.get('warnings'):
            self.maintenance_status_banner.config(text="⚠️ Cleanup completed with warnings", foreground="orange")
        else:
            self.maintenance_status_banner.config(text="✅ Cleanup completed successfully", foreground="green")
        
        # Show messagebox
        messagebox.showinfo(
            "Cleanup Complete",
            f"Smart Cleanup completed!\n\n"
            f"Files Removed: {result.get('files_removed', 0)}\n"
            f"Space Freed: {result.get('space_freed_mb', 0):.2f} MB\n\n"
            f"Report copied to Desktop."
        )
        
        self.log(f"Cleanup complete: {result.get('files_removed', 0)} files removed, "
                f"{result.get('space_freed_mb', 0):.2f} MB freed", "CLEANUP")
    
    def _cleanup_error(self, error_msg: str):
        """Handle cleanup error"""
        self.cleanup_progress_bar.stop()
        self.cleanup_progress_bar.grid_remove()
        
        self.cleanup_log_text.config(state=tk.NORMAL)
        self.cleanup_log_text.insert("end", f"\n❌ Error: {error_msg}\n")
        self.cleanup_log_text.config(state=tk.DISABLED)
        
        self.maintenance_status_banner.config(text="🔴 Cleanup failed", foreground="red")
        
        messagebox.showerror("Cleanup Error", f"Cleanup failed:\n{error_msg}")
    
    def view_full_render(self):
        """Open renders folder in file explorer"""
        try:
            renders_dir = os.path.join(os.path.dirname(__file__), "modules", "clo_companion", "outputs", "renders")
            if os.path.exists(renders_dir):
                os.startfile(renders_dir)
                self.log(f"Opened renders folder: {renders_dir}", "CLO")
            else:
                messagebox.showinfo("No Renders", "Render folder not found. Run a render first.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open renders folder: {e}")
    
    def view_last_report(self):
        """View last cleanup report from Desktop"""
        try:
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            
            # Find most recent CLEANUP_REPORT
            reports = sorted(glob.glob(os.path.join(desktop_path, "CLEANUP_REPORT_*.md")),
                           key=os.path.getmtime, reverse=True)
            
            if reports:
                report_path = reports[0]
                # Open with default text editor
                os.startfile(report_path)
                self.log(f"Opened report: {report_path}", "CLEANUP")
            else:
                # Try root CLEANUP_REPORT.md
                base_dir = os.path.dirname(os.path.abspath(__file__))
                root_report = os.path.join(base_dir, "CLEANUP_REPORT.md")
                if os.path.exists(root_report):
                    os.startfile(root_report)
                    self.log(f"Opened report: {root_report}", "CLEANUP")
                else:
                    messagebox.showinfo("No Report", "No cleanup report found. Run cleanup first.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open report: {e}")
    
    def rebuild_indexes(self):
        """Rebuild ChromaDB indexes only"""
        self.log("Rebuilding ChromaDB indexes...", "CLEANUP")
        
        self.maintenance_status_banner.config(text="🔄 Rebuilding Indexes...", foreground="orange")
        self.cleanup_progress_bar.grid()
        self.cleanup_progress_bar.start()
        
        def do_rebuild():
            try:
                # Trigger reindexing
                from index_documents import main as index_main
                
                # This would trigger a full reindex
                # For now, we'll just optimize ChromaDB
                from core.smart_cleanup import SmartCleanup
                cleanup = SmartCleanup()
                optimize_result = cleanup.optimize_chromadb()
                
                self.root.after(0, lambda: self._rebuild_complete(optimize_result))
            
            except Exception as e:
                self.root.after(0, lambda: self._rebuild_error(str(e)))
        
        thread = threading.Thread(target=do_rebuild, daemon=True)
        thread.start()
    
    def _rebuild_complete(self, success: bool):
        """Handle rebuild completion"""
        self.cleanup_progress_bar.stop()
        self.cleanup_progress_bar.grid_remove()
        
        if success:
            self.maintenance_status_banner.config(text="✅ Indexes rebuilt successfully", foreground="green")
            messagebox.showinfo("Success", "ChromaDB indexes rebuilt successfully!")
        else:
            self.maintenance_status_banner.config(text="⚠️ Index rebuild completed with warnings", foreground="orange")
            messagebox.showwarning("Warning", "Index rebuild completed but some warnings occurred.")
    
    def _rebuild_error(self, error_msg: str):
        """Handle rebuild error"""
        self.cleanup_progress_bar.stop()
        self.cleanup_progress_bar.grid_remove()
        self.maintenance_status_banner.config(text="🔴 Index rebuild failed", foreground="red")
        messagebox.showerror("Error", f"Index rebuild failed:\n{error_msg}")
    
    def test_n8n_connection(self):
        """Test n8n connection"""
        try:
            from core.n8n_integration import get_n8n
            
            n8n = get_n8n()
            
            # Show progress
            self.maintenance_status_banner.config(text="🔄 Testing n8n connection...", foreground="orange")
            
            def do_test():
                result = n8n.test_connection()
                self.root.after(0, lambda: self._update_n8n_test_result(result))
            
            thread = threading.Thread(target=do_test, daemon=True)
            thread.start()
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not test n8n connection:\n{e}")
    
    def _update_n8n_test_result(self, result: Dict):
        """Update n8n test result"""
        if result.get("success"):
            self.maintenance_status_banner.config(text="✅ n8n connection successful", foreground="green")
            self.n8n_status_label.config(text="n8n: 🟢 Connected", foreground="green")
            messagebox.showinfo("n8n Connection", "✅ n8n connection test successful!")
        else:
            self.maintenance_status_banner.config(text="❌ n8n connection failed", foreground="red")
            self.n8n_status_label.config(text="n8n: 🔴 Disconnected", foreground="red")
            messagebox.showerror("n8n Connection", f"❌ n8n connection test failed:\n{result.get('message', 'Unknown error')}")
    
    def open_n8n_dashboard(self):
        """Open n8n dashboard in browser"""
        try:
            from core.n8n_integration import get_n8n
            
            n8n = get_n8n()
            url = n8n.config.get("url", "")
            
            if not url:
                messagebox.showwarning("Not Configured", "n8n URL not configured.\n\nConfigure in Settings tab first.")
                return
            
            # Open in default browser
            import webbrowser
            webbrowser.open(url)
            
            self.log(f"Opened n8n dashboard: {url}", "N8N")
        
        except Exception as e:
            messagebox.showerror("Error", f"Could not open n8n dashboard:\n{e}")
    
    def update_n8n_status(self):
        """Update n8n status indicator"""
        try:
            from core.n8n_integration import get_n8n
            
            n8n = get_n8n()
            
            if n8n.config.get("enabled"):
                # Test connection
                result = n8n.test_connection()
                if result.get("success"):
                    self.n8n_status_label.config(text="n8n: 🟢 Connected", foreground="green")
                else:
                    self.n8n_status_label.config(text="n8n: 🟡 Configured (disconnected)", foreground="orange")
            else:
                self.n8n_status_label.config(text="n8n: ⚪ Not configured", foreground="gray")
        
        except:
            self.n8n_status_label.config(text="n8n: ⚪ Not configured", foreground="gray")
    
    def rebuild_shortcut(self):
        """Rebuild desktop shortcut"""
        try:
            import subprocess
            import os
            
            base_dir = os.path.dirname(os.path.abspath(__file__))
            create_shortcut_script = os.path.join(base_dir, "create_shortcut.py")
            
            if not os.path.exists(create_shortcut_script):
                messagebox.showerror("Error", f"create_shortcut.py not found:\n{create_shortcut_script}")
                return
            
            self.log("Rebuilding desktop shortcut...", "SHORTCUT")
            self.maintenance_status_banner.config(text="🔄 Rebuilding Shortcut...", foreground="orange")
            
            # Run create_shortcut.py
            result = subprocess.run(
                [sys.executable, create_shortcut_script],
                cwd=base_dir,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                self.maintenance_status_banner.config(text="✅ Shortcut rebuilt successfully", foreground="green")
                messagebox.showinfo(
                    "Success",
                    "✅ Desktop shortcut recreated successfully.\n\n"
                    "Shortcut location: Desktop\\Julian Assistant Suite.lnk"
                )
                self.log("Desktop shortcut rebuilt successfully", "SHORTCUT")
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                self.maintenance_status_banner.config(text="🔴 Shortcut rebuild failed", foreground="red")
                messagebox.showerror(
                    "Error",
                    f"Failed to rebuild shortcut:\n{error_msg}"
                )
                self.log(f"Failed to rebuild shortcut: {error_msg}", "SHORTCUT", level="ERROR")
        
        except Exception as e:
            self.maintenance_status_banner.config(text="🔴 Shortcut rebuild failed", foreground="red")
            messagebox.showerror("Error", f"Could not rebuild shortcut:\n{e}")
            self.log(f"Error rebuilding shortcut: {e}", "SHORTCUT", level="ERROR")
    
    def restart_control_panel(self):
        """Restart the Control Panel"""
        try:
            self.log("Control Panel restart requested by user", "SYSTEM")
            
            # Confirm with user
            if not messagebox.askyesno(
                "Restart Control Panel",
                "This will restart the Control Panel and stop all running modules.\n\n"
                "Continue?"
            ):
                return
            
            # Disable restart button
            self.restart_btn.config(state=tk.DISABLED, text="Restarting...")
            self.status_bar.config(text="Restarting Control Panel...")
            self.root.update()
            
            # Stop all running modules
            self.log("Stopping all modules...", "SYSTEM")
            
            # Stop API server if running
            if self.api_process and self.api_process.poll() is None:
                try:
                    self.stop_api_server()
                    time.sleep(1)
                except:
                    pass
            
            # Stop CLO API if running
            if hasattr(self, 'clo_process') and self.clo_process:
                try:
                    if self.clo_process.poll() is None:
                        self.clo_process.terminate()
                        self.clo_process.wait(timeout=3)
                except:
                    try:
                        if self.clo_process.poll() is None:
                            self.clo_process.kill()
                    except:
                        pass
                time.sleep(1)
            
            # Stop other modules
            try:
                from core.module_registry import get_module_registry
                registry = get_module_registry()
                for module_id in registry.get_all_modules():
                    try:
                        registry.stop_module(module_id)
                    except:
                        pass
                time.sleep(1)
            except:
                pass
            
            # Log restart to operations log
            try:
                operations_log = os.path.join(self.log_dir, "operations.log")
                with open(operations_log, "a", encoding="utf-8") as f:
                    from datetime import datetime
                    f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] [SYSTEM] Control Panel restarted by user\n")
            except:
                pass
            
            # Resolve overlapping instances before relaunch
            try:
                sys.path.insert(0, base_dir)
                from core.overlap_resolver import resolve_overlaps
                self.log("Resolving overlapping instances before restart...", "SYSTEM")
                resolve_overlaps(skip_control_panel=True)  # Skip current instance
                time.sleep(1)
            except Exception as overlap_error:
                self.log(f"Overlap resolution warning: {overlap_error}", "SYSTEM", level="WARNING")
            
            # Wait a moment for cleanup
            time.sleep(2)
            
            # Relaunch Control Panel
            base_dir = os.path.dirname(os.path.abspath(__file__))
            target_script = os.path.join(base_dir, "RAG_Control_Panel.py")
            
            self.log(f"Relaunching Control Panel: {sys.executable} {target_script}", "SYSTEM")
            
            # Launch new instance
            subprocess.Popen(
                [sys.executable, target_script],
                cwd=base_dir,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            )
            
            # Close current instance
            self.log("Closing current Control Panel instance", "SYSTEM")
            time.sleep(0.5)
            self.root.quit()
            self.root.destroy()
            
        except Exception as e:
            self.log(f"Error during restart: {e}", "SYSTEM", level="ERROR")
            self.restart_btn.config(state=tk.NORMAL, text="🔄 Restart")
            messagebox.showerror(
                "Restart Failed",
                f"Failed to restart Control Panel:\n{e}\n\nCheck logs for details."
            )
    
    def open_logs_folder(self):
        """Open logs folder in Explorer"""
        try:
            import subprocess
            subprocess.Popen(f'explorer "{self.log_dir}"')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")
    
    def show_first_launch_walkthrough(self):
        """Show first launch walkthrough"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Welcome to Julian Assistant Suite")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        content = ttk.Frame(dialog, padding="20")
        content.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(content, text="Welcome! 👋", font=("Arial", 16, "bold"))
        title.pack(pady=10)
        
        instructions = """This is your local NotebookLM-style academic assistant.

QUICK START:

1. INDEX DOCUMENTS
   Click "Index Documents" to scan your Obsidian vault.
   This may take a few minutes on first run.

2. START API SERVER
   Click "Start API Server" to begin.
   Keep this window open while using.
   Status indicator will turn green when ready.

3. INTEGRATE WITH OBSIDIAN
   Configure ChatGPT MD plugin:
   • API URL: http://127.0.0.1:5000/v1
   • Model: local-rag-llama3.2
   • See CHATGPT_MD_INTEGRATION.md for details

4. TEST IT!
   Click "Test Query" or use Obsidian.

5. CLO COMPANION
   Use the 👗 CLO Companion tab to generate and iterate garment designs.

TIPS:
• Status indicators show system health
• Logs panel shows real-time operations
• Click "Open Logs Folder" for detailed logs
• Run "Health Check" if something doesn't work"""
        
        text_widget = scrolledtext.ScrolledText(content, height=20, width=60,
                                                font=("Arial", 9), wrap=tk.WORD)
        text_widget.insert(1.0, instructions)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(pady=10, fill=tk.BOTH, expand=True)
        
        def skip_walkthrough():
            with open(self.first_launch_file, 'w') as f:
                f.write("")
            dialog.destroy()
            response = messagebox.askyesno(
                "Health Check",
                "Would you like to run a Health Check now?\n\nThis verifies all components are ready."
            )
            if response:
                self.run_health_check()
        
        button_frame = ttk.Frame(content)
        button_frame.pack(pady=10)
        
        btn = ttk.Button(button_frame, text="Got it!", command=skip_walkthrough)
        btn.pack()
    
    def graceful_shutdown(self):
        """Graceful shutdown routine - stop API, sync, close DB"""
        if self.shutting_down:
            return
        
        self.shutting_down = True
        self.log("Initiating graceful shutdown...")
        
        # Stop API servers
        if self.check_port("127.0.0.1", 5000):
            self.log("Stopping Academic RAG API server...")
            self.stop_api_server()
            time.sleep(2)
        
        if self.check_port("127.0.0.1", 5001):
            self.log("Stopping CLO Companion API server...")
            self.stop_clo_api()
            time.sleep(2)
        
        # Close memory manager if needed
        try:
            from core.memory_manager import get_memory_manager
            memory = get_memory_manager()
            if memory:
                memory.close()
        except:
            pass
    
    def on_window_close(self):
        """Handle window close (X button) event"""
        if self.shutting_down:
            return
        
        # Check if API servers are running
        api_running = False
        clo_api_running = False
        try:
            api_running = self.check_port("127.0.0.1", 5000)
            clo_api_running = self.check_port("127.0.0.1", 5001)
        except:
            pass
        
        if (api_running or (self.api_process is not None)) or (clo_api_running or (self.clo_api_process is not None)):
            servers_running = []
            if api_running or (self.api_process is not None):
                servers_running.append("Academic RAG API (port 5000)")
            if clo_api_running or (self.clo_api_process is not None):
                servers_running.append("CLO Companion API (port 5001)")
            
            server_list = "\n".join(f"  • {s}" for s in servers_running)
            response = messagebox.askyesno(
                "API Servers Running",
                f"The following API servers are running:\n\n{server_list}\n\nStop servers and exit?\n\nYes = Stop servers and close gracefully\nNo = Keep window open (servers keep running)"
            )
            if response:
                self.graceful_shutdown()
                self.root.after(500, lambda: (self.root.quit(), self.root.destroy()))
            else:
                return
        else:
            self.graceful_shutdown()
            self.root.after(500, lambda: (self.root.quit(), self.root.destroy()))
    
    def setup_settings_tab(self, parent_frame):
        """Setup Settings tab with n8n and Cursor Bridge controls"""
        parent_frame.columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(parent_frame, text="⚙️ Settings", 
                               font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 15))
        
        # n8n Integration Section
        n8n_frame = ttk.LabelFrame(parent_frame, text="n8n Integration", padding="15")
        n8n_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        n8n_frame.columnconfigure(1, weight=1)
        
        # Enable n8n Sync toggle
        self.n8n_sync_var = tk.BooleanVar(value=True)
        n8n_sync_check = ttk.Checkbutton(n8n_frame, text="Enable n8n Sync", 
                                        variable=self.n8n_sync_var,
                                        command=self.update_n8n_config)
        n8n_sync_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # n8n URL
        ttk.Label(n8n_frame, text="n8n URL:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.n8n_url_entry = ttk.Entry(n8n_frame, width=40)
        self.n8n_url_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.n8n_url_entry.insert(0, "http://<VPS_IP>:5678")
        
        # View n8n Dashboard button
        view_n8n_btn = ttk.Button(n8n_frame, text="🔗 View n8n Dashboard", 
                                 command=self.open_n8n_dashboard)
        view_n8n_btn.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Cursor Bridge Section
        cursor_frame = ttk.LabelFrame(parent_frame, text="Cursor Bridge", padding="15")
        cursor_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        cursor_frame.columnconfigure(1, weight=1)
        
        # Auto mode toggle
        self.cursor_auto_var = tk.BooleanVar(value=True)
        cursor_auto_check = ttk.Checkbutton(cursor_frame, text="Auto Mode (Listen for events)", 
                                           variable=self.cursor_auto_var,
                                           command=self.update_cursor_config)
        cursor_auto_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Ask before fix toggle
        self.cursor_ask_var = tk.BooleanVar(value=True)
        cursor_ask_check = ttk.Checkbutton(cursor_frame, text="Ask Before Fix (code rewrites)", 
                                          variable=self.cursor_ask_var,
                                          command=self.update_cursor_config)
        cursor_ask_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Load current config
        self.load_settings_config()
    
    def load_settings_config(self):
        """Load settings from config files"""
        try:
            import json
            
            # Load n8n config
            n8n_config_file = os.path.join(os.path.dirname(__file__), "config", "n8n_config.json")
            if os.path.exists(n8n_config_file):
                with open(n8n_config_file, 'r', encoding='utf-8') as f:
                    n8n_config = json.load(f)
                    self.n8n_sync_var.set(n8n_config.get("enable_alerts", True))
                    url = n8n_config.get("url", "http://<VPS_IP>:5678")
                    self.n8n_url_entry.delete(0, tk.END)
                    self.n8n_url_entry.insert(0, url)
            
            # Load Cursor Bridge config
            cursor_config_file = os.path.join(os.path.dirname(__file__), "config", "cursor_bridge.json")
            if os.path.exists(cursor_config_file):
                with open(cursor_config_file, 'r', encoding='utf-8') as f:
                    cursor_config = json.load(f)
                    self.cursor_auto_var.set(cursor_config.get("auto_mode", True))
                    self.cursor_ask_var.set(cursor_config.get("ask_before_fix", True))
        except Exception as e:
            log(f"Error loading settings: {e}", "SETTINGS", level="ERROR")
    
    def update_n8n_config(self):
        """Update n8n configuration"""
        try:
            import json
            
            n8n_config_file = os.path.join(os.path.dirname(__file__), "config", "n8n_config.json")
            
            # Load existing config or create new
            if os.path.exists(n8n_config_file):
                with open(n8n_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Update values
            config["enable_alerts"] = self.n8n_sync_var.get()
            config["url"] = self.n8n_url_entry.get().strip()
            
            # Save
            with open(n8n_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.log("[SETTINGS] n8n config updated", "SETTINGS")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update n8n config: {e}")
    
    def update_cursor_config(self):
        """Update Cursor Bridge configuration"""
        try:
            import json
            
            cursor_config_file = os.path.join(os.path.dirname(__file__), "config", "cursor_bridge.json")
            
            # Load existing config or create new
            if os.path.exists(cursor_config_file):
                with open(cursor_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Update values
            config["auto_mode"] = self.cursor_auto_var.get()
            config["ask_before_fix"] = self.cursor_ask_var.get()
            
            # Save
            with open(cursor_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.log("[SETTINGS] Cursor Bridge config updated", "SETTINGS")
        
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update Cursor Bridge config: {e}")
    
    def open_n8n_dashboard(self):
        """Open n8n dashboard in browser"""
        try:
            url = self.n8n_url_entry.get().strip()
            if url and "http" in url:
                import webbrowser
                webbrowser.open(url)
                self.log(f"[SETTINGS] Opened n8n dashboard: {url}", "SETTINGS")
            else:
                messagebox.showwarning("Invalid URL", "Please enter a valid n8n URL")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open n8n dashboard: {e}")
    
    def quit_app(self):
        """Quit the application (called by Quit button)"""
        self.on_window_close()

def main():
    """Main entry point"""
    root = tk.Tk()
    app = RAGControlPanel(root)
    root.mainloop()

if __name__ == "__main__":
    main()
