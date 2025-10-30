"""
Julian Assistant Suite v3.0 - Modern GUI with CustomTkinter
Multi-tab interface with Dashboard, RAG, CLO, Voice, Settings
"""

import os
import sys
import threading
import time
import json
from datetime import datetime
from pathlib import Path

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Try CustomTkinter, fallback to Tkinter if not available
try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
    # Set appearance mode and theme
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
except ImportError:
    CTK_AVAILABLE = False
    import tkinter as tk
    from tkinter import ttk
    log("CustomTkinter not available, using standard Tkinter", "GUI", level="WARNING")

import tkinter.messagebox as messagebox
from tkinter import scrolledtext

try:
    from logger import log, log_exception, get_recent_logs
except ImportError:
    def log(msg, category="GUI", print_to_console=True):
        print(f"[{category}] {msg}")
    def log_exception(category="ERROR", exception=None, context=""):
        print(f"[{category}] {context}: {exception}")
    def get_recent_logs(lines=50, category=None):
        return []

# Import core systems
try:
    from core.memory_manager import get_memory_manager
    from core.context_graph import get_context_graph
    from core.module_registry import get_registry
    from core.health_monitor import get_health_monitor
    from core.config_manager import get_suite_config, save_suite_config, get_module_config
    from modules.system_monitor.monitor import get_system_monitor
    from local_engines.engine_manager import get_engine_manager
except ImportError as e:
    log(f"Error importing core systems: {e}", "GUI", level="ERROR")

if CTK_AVAILABLE:
    class JulianAssistantSuite(ctk.CTk):
        def __init__(self):
            super().__init__()
            
            # Load user preferences
            self.load_preferences()
            
            # Initialize
            self.setup_window()
            self.setup_tabs()
            self.load_session()
            
            # Start background threads
            self.start_background_tasks()
            
            log("Julian Assistant Suite v3.0 started", "GUI")
        
        def load_preferences(self):
            """Load user preferences"""
            prefs_path = os.path.join(BASE_DIR, "config", "user_prefs.json")
            try:
                if os.path.exists(prefs_path):
                    with open(prefs_path, 'r', encoding='utf-8') as f:
                        self.prefs = json.load(f)
                else:
                    self.prefs = {
                        "theme": "Dark",
                        "window_width": 1400,
                        "window_height": 900,
                        "last_tab": "Dashboard"
                    }
            except:
                self.prefs = {"theme": "Dark"}
            
            # Set theme
            if CTK_AVAILABLE and self.prefs.get("theme") == "Dark":
                ctk.set_appearance_mode("dark")
            elif CTK_AVAILABLE:
                ctk.set_appearance_mode("light")
        
        def setup_window(self):
            """Setup main window"""
            self.title("Julian Assistant Suite v3.5.0-Julian-Memory")
            width = self.prefs.get("window_width", 1400)
            height = self.prefs.get("window_height", 900)
            self.geometry(f"{width}x{height}")
            
            # Setup grid
            self.grid_columnconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=1)
        
        def setup_tabs(self):
            """Setup tabbed interface"""
            # Tab view
            self.tabview = ctk.CTkTabview(self)
            self.tabview.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
            
            # Create tabs
            self.tabs = {}
            tab_names = ["Dashboard", "RAG & Docs", "CLO Companion", "Voice & Automation", "Memory", "Settings & Profiles"]
            
            for tab_name in tab_names:
                self.tabs[tab_name] = self.tabview.add(tab_name)
                self.tabs[tab_name].grid_columnconfigure(0, weight=1)
                self.tabs[tab_name].grid_rowconfigure(0, weight=1)
            
            # Setup each tab
            self.setup_dashboard_tab()
            self.setup_rag_tab()
            self.setup_clo_tab()
            self.setup_voice_tab()
            self.setup_memory_tab()
            self.setup_settings_tab()
            
            # Restore last tab
            last_tab = self.prefs.get("last_tab", "Dashboard")
            if last_tab in tab_names:
                self.tabview.set(last_tab)
        
        def setup_dashboard_tab(self):
            """Dashboard tab with metrics and quick controls"""
            tab = self.tabs["Dashboard"]
            
            # Top bar with title
            title_frame = ctk.CTkFrame(tab)
            title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            
            title_label = ctk.CTkLabel(
                title_frame,
                text="System Dashboard",
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title_label.pack(side="left", padx=20, pady=10)
            
            # Metrics frame
            metrics_frame = ctk.CTkFrame(tab)
            metrics_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
            
            # CPU/RAM/GPU bars
            self.cpu_label = ctk.CTkLabel(metrics_frame, text="CPU: 0%", font=ctk.CTkFont(size=12))
            self.cpu_label.grid(row=0, column=0, padx=10, pady=5)
            
            self.cpu_bar = ctk.CTkProgressBar(metrics_frame, width=200)
            self.cpu_bar.grid(row=0, column=1, padx=10, pady=5)
            self.cpu_bar.set(0)
            
            self.ram_label = ctk.CTkLabel(metrics_frame, text="RAM: 0%", font=ctk.CTkFont(size=12))
            self.ram_label.grid(row=0, column=2, padx=10, pady=5)
            
            self.ram_bar = ctk.CTkProgressBar(metrics_frame, width=200)
            self.ram_bar.grid(row=0, column=3, padx=10, pady=5)
            self.ram_bar.set(0)
            
            self.gpu_label = ctk.CTkLabel(metrics_frame, text="GPU: N/A", font=ctk.CTkFont(size=12))
            self.gpu_label.grid(row=1, column=0, padx=10, pady=5)
            
            self.gpu_bar = ctk.CTkProgressBar(metrics_frame, width=200)
            self.gpu_bar.grid(row=1, column=1, padx=10, pady=5)
            self.gpu_bar.set(0)
            
            # Quick Actions
            actions_frame = ctk.CTkFrame(tab)
            actions_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
            
            self.full_test_btn = ctk.CTkButton(
                actions_frame,
                text="Full System Test",
                command=self.run_full_test,
                width=200,
                height=40
            )
            self.full_test_btn.pack(side="left", padx=10, pady=10)
            
            # Module status grid
            status_frame = ctk.CTkFrame(tab)
            status_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
            tab.rowconfigure(3, weight=1)
            
            self.module_status_labels = {}
            registry = get_registry()
            if registry:
                modules = registry.get_all_modules()
                for i, module in enumerate(modules):
                    module_id = module.get('module_id')
                    status_label = ctk.CTkLabel(
                        status_frame,
                        text=f"{module_id}: Unknown",
                        font=ctk.CTkFont(size=12)
                    )
                    status_label.grid(row=i, column=0, padx=10, pady=5, sticky="w")
                    self.module_status_labels[module_id] = status_label
        
        def setup_rag_tab(self):
            """RAG & Docs tab"""
            tab = self.tabs["RAG & Docs"]
            
            # Query section
            query_frame = ctk.CTkFrame(tab)
            query_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            
            query_label = ctk.CTkLabel(query_frame, text="Query:", font=ctk.CTkFont(size=14))
            query_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            self.query_entry = ctk.CTkEntry(query_frame, width=600, height=30)
            self.query_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
            query_frame.columnconfigure(1, weight=1)
            
            self.query_btn = ctk.CTkButton(
                query_frame,
                text="Query",
                command=self.execute_rag_query,
                width=100
            )
            self.query_btn.grid(row=0, column=2, padx=10, pady=5)
            
            # Context preview
            context_frame = ctk.CTkFrame(tab)
            context_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
            
            context_label = ctk.CTkLabel(context_frame, text="Context Preview:", font=ctk.CTkFont(size=12))
            context_label.pack(side="left", padx=10, pady=5)
            
            self.context_preview_btn = ctk.CTkButton(
                context_frame,
                text="Show Preview",
                command=self.show_context_preview,
                width=150
            )
            self.context_preview_btn.pack(side="left", padx=10, pady=5)
            
            # Response area
            response_frame = ctk.CTkFrame(tab)
            response_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)
            tab.rowconfigure(2, weight=1)
            
            self.response_text = ctk.CTkTextbox(response_frame, width=800, height=400)
            self.response_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        def setup_clo_tab(self):
            """CLO Companion tab"""
            tab = self.tabs["CLO Companion"]
            
            # Prompt input
            prompt_frame = ctk.CTkFrame(tab)
            prompt_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            
            prompt_label = ctk.CTkLabel(prompt_frame, text="Garment Prompt:", font=ctk.CTkFont(size=14))
            prompt_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            self.garment_entry = ctk.CTkEntry(prompt_frame, width=500, height=30, placeholder_text="e.g., Generate short-sleeve shirt pattern")
            self.garment_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
            prompt_frame.columnconfigure(1, weight=1)
            
            self.generate_btn = ctk.CTkButton(
                prompt_frame,
                text="Generate",
                command=self.generate_garment,
                width=120
            )
            self.generate_btn.grid(row=0, column=2, padx=10, pady=5)
            
            self.preview_btn = ctk.CTkButton(
                prompt_frame,
                text="Preview Latest",
                command=self.preview_garment,
                width=120
            )
            self.preview_btn.grid(row=0, column=3, padx=10, pady=5)
            
            # Output area
            output_frame = ctk.CTkFrame(tab)
            output_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
            tab.rowconfigure(1, weight=1)
            
            self.clo_output_text = ctk.CTkTextbox(output_frame, width=800, height=400)
            self.clo_output_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        def setup_voice_tab(self):
            """Voice & Automation tab"""
            tab = self.tabs["Voice & Automation"]
            
            # Voice control section
            voice_frame = ctk.CTkFrame(tab)
            voice_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            
            mic_status_label = ctk.CTkLabel(voice_frame, text="🎤 Mic Status:", font=ctk.CTkFont(size=14, weight="bold"))
            mic_status_label.grid(row=0, column=0, padx=10, pady=5)
            
            self.mic_status_indicator = ctk.CTkLabel(voice_frame, text="Disabled", font=ctk.CTkFont(size=12))
            self.mic_status_indicator.grid(row=0, column=1, padx=10, pady=5)
            
            self.mic_toggle = ctk.CTkSwitch(voice_frame, text="Enable Voice Control", command=self.toggle_voice)
            self.mic_toggle.grid(row=0, column=2, padx=10, pady=5)
            
            # Command editor
            editor_frame = ctk.CTkFrame(tab)
            editor_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
            
            cmd_label = ctk.CTkLabel(editor_frame, text="Voice Commands:", font=ctk.CTkFont(size=12))
            cmd_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
            
            self.edit_commands_btn = ctk.CTkButton(
                editor_frame,
                text="Edit Commands",
                command=self.edit_voice_commands,
                width=150
            )
            self.edit_commands_btn.grid(row=0, column=1, padx=10, pady=5)
            
            # Command list
            self.command_list = ctk.CTkTextbox(editor_frame, width=700, height=200)
            self.command_list.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
            editor_frame.columnconfigure(0, weight=1)
            
            self.load_command_list()
        
        def setup_memory_tab(self):
            """Memory tab with facts display and management"""
            tab = self.tabs["Memory"]
            
            # Top bar
            title_frame = ctk.CTkFrame(tab)
            title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            
            title_label = ctk.CTkLabel(
                title_frame,
                text="🧠 Persistent Memory",
                font=ctk.CTkFont(size=20, weight="bold")
            )
            title_label.pack(side="left", padx=20, pady=10)
            
            # Stats
            stats_frame = ctk.CTkFrame(tab)
            stats_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
            
            self.memory_stats_label = ctk.CTkLabel(
                stats_frame,
                text="Facts: 0 | Semantic: 0",
                font=ctk.CTkFont(size=12)
            )
            self.memory_stats_label.pack(side="left", padx=10, pady=5)
            
            # Actions
            actions_frame = ctk.CTkFrame(tab)
            actions_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
            
            self.refresh_memory_btn = ctk.CTkButton(
                actions_frame,
                text="Refresh",
                command=self.refresh_memory_display,
                width=100
            )
            self.refresh_memory_btn.pack(side="left", padx=5, pady=5)
            
            self.forget_btn = ctk.CTkButton(
                actions_frame,
                text="Forget Selected",
                command=self.forget_selected_facts,
                width=150,
                fg_color="red"
            )
            self.forget_btn.pack(side="left", padx=5, pady=5)
            
            self.export_memory_btn = ctk.CTkButton(
                actions_frame,
                text="Export",
                command=self.export_memory,
                width=100
            )
            self.export_memory_btn.pack(side="left", padx=5, pady=5)
            
            # Facts list
            list_frame = ctk.CTkFrame(tab)
            list_frame.grid(row=3, column=0, sticky="nsew", padx=10, pady=10)
            tab.rowconfigure(3, weight=1)
            
            # Scrollable frame for facts
            self.facts_scroll = ctk.CTkScrollableFrame(list_frame, width=800, height=400)
            self.facts_scroll.pack(fill="both", expand=True, padx=10, pady=10)
            
            self.fact_checkboxes = {}  # Store checkboxes for selection
            
            # Context preview section
            context_frame = ctk.CTkFrame(tab)
            context_frame.grid(row=4, column=0, sticky="ew", padx=10, pady=5)
            
            context_label = ctk.CTkLabel(context_frame, text="Last Context Bundle:", font=ctk.CTkFont(size=12))
            context_label.pack(side="left", padx=10, pady=5)
            
            self.context_preview_btn_memory = ctk.CTkButton(
                context_frame,
                text="Show Preview",
                command=self.show_context_preview,
                width=150
            )
            self.context_preview_btn_memory.pack(side="left", padx=10, pady=5)
            
            # Load initial data
            self.refresh_memory_display()
        
        def refresh_memory_display(self):
            """Refresh memory facts display"""
            try:
                from core.memory_manager import get_memory_manager
                from core.context_graph import get_context_graph
                
                memory = get_memory_manager()
                graph = get_context_graph()
                
                # Get facts
                facts = memory.recall("julian", limit=50)
                semantic_facts = graph._get_semantic_memory()
                
                # Update stats
                self.memory_stats_label.configure(
                    text=f"Facts: {len(facts)} | Semantic: {len(semantic_facts)}"
                )
                
                # Clear existing checkboxes
                for widget in self.facts_scroll.winfo_children():
                    widget.destroy()
                self.fact_checkboxes.clear()
                
                # Display facts
                for fact in facts[:20]:  # Show top 20
                    fact_frame = ctk.CTkFrame(self.facts_scroll)
                    fact_frame.pack(fill="x", padx=5, pady=2)
                    
                    # Checkbox
                    var = tk.BooleanVar()
                    checkbox = ctk.CTkCheckBox(
                        fact_frame,
                        text="",
                        variable=var,
                        width=20
                    )
                    checkbox.pack(side="left", padx=5, pady=5)
                    self.fact_checkboxes[fact['key']] = var
                    
                    # Fact display
                    fact_text = f"{fact['key']}: {str(fact['value'])[:50]}"
                    fact_label = ctk.CTkLabel(
                        fact_frame,
                        text=fact_text,
                        font=ctk.CTkFont(size=11),
                        anchor="w"
                    )
                    fact_label.pack(side="left", padx=5, pady=5, fill="x", expand=True)
                    
                    # Confidence badge
                    conf_label = ctk.CTkLabel(
                        fact_frame,
                        text=f"{fact.get('confidence', 1.0):.2f}",
                        font=ctk.CTkFont(size=10),
                        width=50
                    )
                    conf_label.pack(side="right", padx=5, pady=5)
                
            except Exception as e:
                log_exception("GUI", e, "Error refreshing memory display")
        
        def forget_selected_facts(self):
            """Forget selected facts"""
            try:
                from core.memory_manager import get_memory_manager
                memory = get_memory_manager()
                
                to_forget = [key for key, var in self.fact_checkboxes.items() if var.get()]
                
                if not to_forget:
                    messagebox.showinfo("Info", "No facts selected")
                    return
                
                for key in to_forget:
                    memory.forget("julian", key)
                
                log(f"Forgot {len(to_forget)} facts", "GUI")
                self.refresh_memory_display()
                self.show_toast(f"✅ Forgot {len(to_forget)} facts")
                
            except Exception as e:
                log_exception("GUI", e, "Error forgetting facts")
        
        def export_memory(self):
            """Export memory to JSON file"""
            try:
                from core.memory_manager import get_memory_manager
                import json
                
                memory = get_memory_manager()
                all_facts = memory.get_all_facts("julian")
                
                export_path = os.path.join(BASE_DIR, "exports", f"memory_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                os.makedirs(os.path.dirname(export_path), exist_ok=True)
                
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(all_facts, f, indent=2, ensure_ascii=False)
                
                self.show_toast(f"✅ Exported to: {export_path}")
                messagebox.showinfo("Export", f"Memory exported to:\n{export_path}")
                
            except Exception as e:
                log_exception("GUI", e, "Error exporting memory")
        
        def setup_settings_tab(self):
            """Settings & Profiles tab"""
            tab = self.tabs["Settings & Profiles"]
            
            # Profile selector
            profile_frame = ctk.CTkFrame(tab)
            profile_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
            
            profile_label = ctk.CTkLabel(profile_frame, text="Active Profile:", font=ctk.CTkFont(size=14))
            profile_label.grid(row=0, column=0, padx=10, pady=5)
            
            self.profile_menu = ctk.CTkOptionMenu(
                profile_frame,
                values=["Academic", "Creative", "Low-Power"],
                command=self.switch_profile,
                width=200
            )
            self.profile_menu.grid(row=0, column=1, padx=10, pady=5)
            self.profile_menu.set(self.prefs.get("active_profile", "Academic"))
            
            # Engine selector
            engine_frame = ctk.CTkFrame(tab)
            engine_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
            
            engine_label = ctk.CTkLabel(engine_frame, text="Engine Mode:", font=ctk.CTkFont(size=14))
            engine_label.grid(row=0, column=0, padx=10, pady=5)
            
            self.engine_menu = ctk.CTkOptionMenu(
                engine_frame,
                values=["Auto", "Ollama", "llama.cpp"],
                command=self.switch_engine,
                width=200
            )
            self.engine_menu.grid(row=0, column=1, padx=10, pady=5)
            self.engine_menu.set(self.prefs.get("engine_mode", "Auto"))
            
            # Theme selector
            theme_frame = ctk.CTkFrame(tab)
            theme_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
            
            theme_label = ctk.CTkLabel(theme_frame, text="Theme:", font=ctk.CTkFont(size=14))
            theme_label.grid(row=0, column=0, padx=10, pady=5)
            
            self.theme_menu = ctk.CTkOptionMenu(
                theme_frame,
                values=["Dark", "Light"],
                command=self.switch_theme,
                width=200
            )
            self.theme_menu.grid(row=0, column=1, padx=10, pady=5)
            self.theme_menu.set(self.prefs.get("theme", "Dark"))
        
        def start_background_tasks(self):
            """Start background monitoring threads"""
            # Update metrics
            def update_metrics():
                while True:
                    try:
                        monitor = get_system_monitor()
                        if monitor:
                            metrics = monitor.get_metrics()
                            self.update_metrics_display(metrics)
                    except:
                        pass
                    time.sleep(5)
            
            # Update module status
            def update_status():
                while True:
                    try:
                        self.update_module_status()
                    except:
                        pass
                    time.sleep(10)
            
            threading.Thread(target=update_metrics, daemon=True).start()
            threading.Thread(target=update_status, daemon=True).start()
            log("Background tasks started", "GUI")
        
        def update_metrics_display(self, metrics):
            """Update metrics display"""
            try:
                cpu = metrics.get("cpu_percent", 0) / 100.0
                ram = metrics.get("ram_percent", 0) / 100.0
                gpu = metrics.get("gpu_percent")
                
                self.cpu_bar.set(cpu)
                self.cpu_label.configure(text=f"CPU: {metrics.get('cpu_percent', 0):.1f}%")
                
                self.ram_bar.set(ram)
                self.ram_label.configure(text=f"RAM: {metrics.get('ram_percent', 0):.1f}%")
                
                if gpu is not None:
                    self.gpu_bar.set(gpu / 100.0)
                    self.gpu_label.configure(text=f"GPU: {gpu:.1f}%")
                else:
                    self.gpu_label.configure(text="GPU: N/A")
            except:
                pass
        
        def update_module_status(self):
            """Update module status indicators"""
            try:
                health_monitor = get_health_monitor()
                if not health_monitor:
                    return
                
                all_health = health_monitor.get_all_health()
                for module_id, health in all_health.items():
                    if module_id in self.module_status_labels:
                        status = health.get("status", "unknown")
                        color_map = {
                            "healthy": "green",
                            "degraded": "yellow",
                            "unhealthy": "red",
                            "stopped": "gray"
                        }
                        color = color_map.get(status, "gray")
                        status_text = f"{module_id}: {status}"
                        self.module_status_labels[module_id].configure(text=status_text)
            except:
                pass
        
        def show_context_preview(self):
            """Show context graph preview"""
            try:
                graph = get_context_graph()
                preview = graph.context_preview(query=self.query_entry.get())
                
                # Show in popup
                preview_window = ctk.CTkToplevel(self)
                preview_window.title("Context Preview")
                preview_window.geometry("800x600")
                
                preview_text = ctk.CTkTextbox(preview_window, width=780, height=580)
                preview_text.pack(fill="both", expand=True, padx=10, pady=10)
                preview_text.insert("1.0", preview)
                preview_text.configure(state="disabled")
                
            except Exception as e:
                log_exception("GUI", e, "Error showing context preview")
                messagebox.showerror("Error", f"Failed to show context preview: {e}")
        
        def execute_rag_query(self):
            """Execute RAG query"""
            query = self.query_entry.get()
            if not query:
                return
            
            def query_thread():
                try:
                    # Build context
                    graph = get_context_graph()
                    context = graph.build_context(query=query, include_rag=True)
                    
                    # Call RAG API
                    import requests
                    from core.config_manager import get_auth_token
                    
                    response = requests.post(
                        "http://127.0.0.1:5000/v1/chat/completions",
                        json={
                            "messages": [{"role": "user", "content": query}],
                            "model": "llama3.2"
                        },
                        headers={"Authorization": f"Bearer {get_auth_token()}"},
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        answer = result["choices"][0]["message"]["content"]
                        
                        # Update memory with query
                        memory = get_memory_manager()
                        memory.remember("julian", f"query_{int(time.time())}", query, category="queries")
                        
                        self.response_text.insert("end", f"Query: {query}\n\n{answer}\n\n{'='*80}\n\n")
                        self.response_text.see("end")
                        
                        self.show_toast("✅ Query completed")
                    else:
                        self.show_toast(f"❌ Query failed: {response.status_code}")
                        
                except Exception as e:
                    log_exception("GUI", e, "Error executing query")
                    self.show_toast(f"❌ Error: {e}")
            
            threading.Thread(target=query_thread, daemon=True).start()
        
        def generate_garment(self):
            """Generate garment from prompt"""
            prompt = self.garment_entry.get()
            if not prompt:
                return
            
            def generate_thread():
                try:
                    import requests
                    from core.config_manager import get_auth_token
                    
                    response = requests.post(
                        "http://127.0.0.1:5001/apply_change",
                        json={"command": prompt},
                        headers={"Authorization": f"Bearer {get_auth_token()}"},
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.clo_output_text.insert("end", f"Generated: {json.dumps(result, indent=2)}\n\n")
                        self.show_toast("✅ Garment generated")
                    else:
                        self.show_toast(f"❌ Generation failed: {response.status_code}")
                        
                except Exception as e:
                    log_exception("GUI", e, "Error generating garment")
                    self.show_toast(f"❌ Error: {e}")
            
            threading.Thread(target=generate_thread, daemon=True).start()
        
        def preview_garment(self):
            """Preview latest garment"""
            try:
                import requests
                from core.config_manager import get_auth_token
                
                response = requests.post(
                    "http://127.0.0.1:5001/render",
                    json={},
                    headers={"Authorization": f"Bearer {get_auth_token()}"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    preview_path = result.get("preview_file")
                    self.show_toast(f"✅ Preview: {preview_path}")
                else:
                    self.show_toast(f"❌ Preview failed")
                    
            except Exception as e:
                log_exception("GUI", e, "Error previewing garment")
                self.show_toast(f"❌ Error: {e}")
        
        def toggle_voice(self):
            """Toggle voice control"""
            enabled = self.mic_toggle.get()
            if enabled:
                self.mic_status_indicator.configure(text="Enabled (Press F9)")
                # Start voice listener
                try:
                    from modules.voice_control.voice_listener import VoiceListener
                    self.voice_listener = VoiceListener()
                    self.voice_listener.start()
                except:
                    self.show_toast("⚠️ Voice control not available")
            else:
                self.mic_status_indicator.configure(text="Disabled")
                if hasattr(self, 'voice_listener'):
                    self.voice_listener.stop()
        
        def edit_voice_commands(self):
            """Open voice commands editor"""
            editor_window = ctk.CTkToplevel(self)
            editor_window.title("Edit Voice Commands")
            editor_window.geometry("800x600")
            
            # Load commands
            cmd_path = os.path.join(BASE_DIR, "modules", "voice_control", "config", "commands.json")
            try:
                with open(cmd_path, 'r', encoding='utf-8') as f:
                    commands_data = json.load(f)
            except:
                commands_data = {"commands": {}}
            
            # Show commands in text area (editable)
            text_area = ctk.CTkTextbox(editor_window, width=780, height=500)
            text_area.pack(fill="both", expand=True, padx=10, pady=10)
            text_area.insert("1.0", json.dumps(commands_data, indent=2))
            
            def save_commands():
                try:
                    new_data = json.loads(text_area.get("1.0", "end"))
                    with open(cmd_path, 'w', encoding='utf-8') as f:
                        json.dump(new_data, f, indent=2)
                    self.show_toast("✅ Commands saved")
                    editor_window.destroy()
                    self.load_command_list()
                except Exception as e:
                    messagebox.showerror("Error", f"Invalid JSON: {e}")
            
            save_btn = ctk.CTkButton(editor_window, text="Save", command=save_commands)
            save_btn.pack(pady=10)
        
        def load_command_list(self):
            """Load command list into display"""
            try:
                cmd_path = os.path.join(BASE_DIR, "modules", "voice_control", "config", "commands.json")
                with open(cmd_path, 'r', encoding='utf-8') as f:
                    commands_data = json.load(f)
                
                cmd_text = "Voice Commands:\n\n"
                for cmd, info in commands_data.get("commands", {}).items():
                    cmd_text += f"• {cmd}\n  → {info.get('action', 'N/A')}\n  {info.get('description', '')}\n\n"
                
                self.command_list.insert("1.0", cmd_text)
                self.command_list.configure(state="disabled")
            except:
                self.command_list.insert("1.0", "No commands found")
        
        def switch_profile(self, profile):
            """Switch active profile"""
            self.prefs["active_profile"] = profile
            self.save_preferences()
            self.show_toast(f"✅ Profile switched to: {profile}")
        
        def switch_engine(self, engine):
            """Switch engine mode"""
            try:
                engine_mgr = get_engine_manager()
                engine_mgr.set_engine(engine.lower().replace(".cpp", ".cpp"))
                self.prefs["engine_mode"] = engine
                self.save_preferences()
                self.show_toast(f"✅ Engine switched to: {engine}")
            except Exception as e:
                log_exception("GUI", e, "Error switching engine")
        
        def switch_theme(self, theme):
            """Switch theme"""
            if CTK_AVAILABLE:
                ctk.set_appearance_mode(theme.lower())
                self.prefs["theme"] = theme
                self.save_preferences()
                self.show_toast(f"✅ Theme switched to: {theme}")
        
        def run_full_test(self):
            """Run full system test"""
            def test_thread():
                try:
                    self.show_toast("🔍 Running full system test...")
                    
                    # Check all modules
                    registry = get_registry()
                    modules = registry.get_all_modules()
                    
                    results = []
                    for module in modules:
                        module_id = module.get('module_id')
                        port = module.get('port')
                        
                        if port:
                            import requests
                            try:
                                response = requests.get(
                                    f"http://127.0.0.1:{port}/health",
                                    timeout=2
                                )
                                if response.status_code == 200:
                                    results.append(f"✅ {module_id}")
                                else:
                                    results.append(f"⚠️ {module_id} (status: {response.status_code})")
                            except:
                                results.append(f"❌ {module_id} (not responding)")
                    
                    result_text = "\n".join(results)
                    messagebox.showinfo("Full System Test", result_text)
                    self.show_toast("✅ Test complete")
                    
                except Exception as e:
                    log_exception("GUI", e, "Error in full test")
                    self.show_toast(f"❌ Test error: {e}")
            
            threading.Thread(target=test_thread, daemon=True).start()
        
        def show_toast(self, message):
            """Show toast notification"""
            # Simple messagebox for now (can be enhanced)
            log(message, "GUI")
        
        def load_session(self):
            """Load last session state"""
            # Restore window size
            width = self.prefs.get("window_width", 1400)
            height = self.prefs.get("window_height", 900)
            self.geometry(f"{width}x{height}")
        
        def save_preferences(self):
            """Save user preferences"""
            try:
                prefs_path = os.path.join(BASE_DIR, "config", "user_prefs.json")
                with open(prefs_path, 'w', encoding='utf-8') as f:
                    json.dump(self.prefs, f, indent=2)
            except Exception as e:
                log(f"Error saving preferences: {e}", "GUI", level="ERROR")
        
        def on_closing(self):
            """Handle window closing"""
            # Save preferences
            width, height = self.geometry().split('x')
            self.prefs["window_width"] = int(width)
            self.prefs["window_height"] = int(height)
            self.prefs["last_tab"] = self.tabview.get()
            self.save_preferences()
            
            self.destroy()

else:
    # Fallback to Tkinter if CustomTkinter not available
    log("Using standard Tkinter (CustomTkinter not available)", "GUI")
    class JulianAssistantSuite:
        def __init__(self):
            # Fallback implementation would go here
            pass

def main():
    """Main entry point"""
    if CTK_AVAILABLE:
        app = JulianAssistantSuite()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
    else:
        log("CustomTkinter required for v3.0 GUI. Install with: pip install customtkinter", "GUI", level="ERROR")
        # Fallback to old GUI
        from RAG_Control_Panel import RAGControlPanel
        root = tk.Tk()
        app = RAGControlPanel(root)
        root.mainloop()

if __name__ == "__main__":
    main()

