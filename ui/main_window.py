"""
RAGGITY ZYZTEM 2.0 - Main UI Window
Modern dark UI with sidebar navigation and non-blocking async operations
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

from ui.theme import apply_theme
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
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.title("RAGGITY ZYZTEM 2.0")
        self.geometry("1100x700")
        self.resizable(True, True)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Create layout
        self.sidebar = Sidebar(self)
        self.sidebar.pack(side="left", fill="y")
        
        self.container = Container(self)
        self.container.pack(side="right", fill="both", expand=True)
        
        # Start status updates (scheduled via after)
        self.after(2000, self.update_status)

    def update_status(self):
        """Update API and GPU status in sidebar (non-blocking)"""
        def check_status():
            try:
                r = requests.get("http://localhost:8000/health", timeout=1)
                api_status = "🟢 API Online" if r.ok else "🔴 API Down"
            except Exception as e:
                api_status = "🔴 API Down"
                log(f"UI: API health check failed: {e}", "UI")
            
            try:
                gpu = get_gpu_status()
                gpu_line = f"GPU: {gpu.get('name','CPU Mode')}" if gpu["available"] else "GPU: CPU Only"
            except Exception as e:
                gpu_line = "GPU: Error"
                log(f"UI: GPU status check failed: {e}", "UI")
            
            # Update UI on main thread
            self.after(0, lambda: self.sidebar.status_label.configure(
                text=f"{api_status}  |  {gpu_line}"
            ))
        
        # Run check in background thread
        threading.Thread(target=check_status, daemon=True).start()
        
        # Schedule next update
        self.after(5000, self.update_status)

    def on_close(self):
        """Handle window close"""
        log("UI: Window closing", "UI")
        self.destroy()


class Sidebar(ctk.CTkFrame):
    """Left sidebar with navigation buttons"""
    
    def __init__(self, master):
        super().__init__(master, width=220, fg_color="#111")
        self.pack_propagate(False)
        
        # Logo
        self.logo = ctk.CTkLabel(self, text="⚙️ RAGGITY", font=("Segoe UI", 20, "bold"))
        self.logo.pack(pady=25)
        
        # Navigation buttons
        self.buttons = []
        for name in ["Ingest", "Query", "System", "Logs", "Bridge"]:
            b = ctk.CTkButton(
                self,
                text=name,
                command=lambda n=name: master.container.show_tab(n)
            )
            b.pack(pady=5, padx=15, fill="x")
            self.buttons.append(b)
        
        # Status at bottom
        self.status_label = ctk.CTkLabel(self, text="Connecting...", text_color="#999")
        self.status_label.pack(side="bottom", pady=15)


class Container(ctk.CTkFrame):
    """Main content container with tabs"""
    
    def __init__(self, master):
        super().__init__(master)
        
        # Create all tabs
        self.tabs = {
            "Ingest": IngestTab(self),
            "Query": QueryTab(self),
            "System": SystemTab(self),
            "Logs": LogsTab(self),
            "Bridge": BridgeTab(self),
        }
        
        # Place all tabs in same location
        for t in self.tabs.values():
            t.place(relwidth=1, relheight=1)
        
        # Show Query tab by default
        self.show_tab("Query")

    def show_tab(self, name):
        """Show the specified tab"""
        # Hide all tabs
        for k, v in self.tabs.items():
            v.lower()
        for t in self.tabs.values():
            t.place_forget()
        
        # Show selected tab
        self.tabs[name].place(relwidth=1, relheight=1)
        log(f"UI: Switched to {name} tab", "UI")


# ========== Tab Implementations ==========

class IngestTab(ctk.CTkFrame):
    """File ingestion tab"""
    
    def __init__(self, master):
        super().__init__(master)
        
        # Title
        ctk.CTkLabel(self, text="Ingest Files", font=("Segoe UI", 18)).pack(pady=10)
        
        # Path entry
        self.entry = ctk.CTkEntry(self, placeholder_text="Drag a file or enter path")
        self.entry.pack(padx=20, pady=10, fill="x")
        
        # Ingest button
        self.ingest_btn = ctk.CTkButton(self, text="Ingest", command=self.do_ingest)
        self.ingest_btn.pack(pady=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(self, text="", text_color="#999")
        self.status_label.pack(pady=5)
        
        # Output console
        self.output = ctk.CTkTextbox(self, height=200)
        self.output.pack(fill="both", padx=20, pady=10, expand=True)

    def do_ingest(self):
        """Trigger file ingestion (non-blocking)"""
        path = self.entry.get().strip('" ')
        
        if not os.path.exists(path):
            self.output.insert("end", f"[!] Path not found: {path}\n")
            log(f"UI: Ingest failed - path not found: {path}", "UI")
            return
        
        # Show loading status
        self.status_label.configure(text="⏳ Ingesting...")
        self.ingest_btn.configure(state="disabled")
        
        def run():
            try:
                log(f"UI: Starting ingestion of {path}", "UI")
                self.output.insert("end", f"[→] Ingesting: {path}\n")
                
                r = requests.post(
                    "http://localhost:8000/ingest-path",
                    json={"path": path},
                    timeout=60
                )
                
                # Update UI on main thread
                def update_ui():
                    if r.ok:
                        self.output.insert("end", f"[+] Success! Ingested: {path}\n")
                        self.status_label.configure(text="✓ Complete")
                        log(f"UI: Ingestion successful: {path}", "UI")
                    else:
                        self.output.insert("end", f"[x] Error {r.status_code}: {r.text}\n")
                        self.status_label.configure(text="✗ Failed")
                        log(f"UI: Ingestion failed {r.status_code}: {path}", "UI")
                    
                    # Re-enable button
                    self.ingest_btn.configure(state="normal")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: Ingestion exception: {e}", "UI")
                
                def update_ui():
                    self.output.insert("end", f"[x] Error: {e}\n")
                    self.status_label.configure(text="✗ Error")
                    self.ingest_btn.configure(state="normal")
                
                self.after(0, update_ui)
        
        # Run in background thread
        threading.Thread(target=run, daemon=True).start()


class QueryTab(ctk.CTkFrame):
    """Query interface tab"""
    
    def __init__(self, master):
        super().__init__(master)
        
        # Title
        ctk.CTkLabel(self, text="Ask a Question", font=("Segoe UI", 18)).pack(pady=10)
        
        # Query input
        self.q = ctk.CTkEntry(self, placeholder_text="Enter question...")
        self.q.pack(padx=20, pady=10, fill="x")
        self.q.bind("<Return>", lambda e: self.ask())
        
        # Query button
        self.query_btn = ctk.CTkButton(self, text="Query", command=self.ask)
        self.query_btn.pack()
        
        # Status label
        self.status_label = ctk.CTkLabel(self, text="", text_color="#999")
        self.status_label.pack(pady=5)
        
        # Answer display
        self.a = ctk.CTkTextbox(self, wrap="word")
        self.a.pack(fill="both", expand=True, padx=20, pady=10)

    def ask(self):
        """Submit query to API (non-blocking)"""
        q = self.q.get().strip()
        if not q:
            return
        
        # Show loading status
        self.a.delete("1.0", "end")
        self.a.insert("end", "⏳ Fetching...\n")
        self.status_label.configure(text="⏳ Querying...")
        self.query_btn.configure(state="disabled")
        
        def run():
            try:
                log(f"UI: Query submitted: {q[:100]}", "UI")
                
                r = requests.get(
                    "http://localhost:8000/query",
                    params={"q": q, "k": 5},
                    timeout=60
                )
                
                # Update UI on main thread
                def update_ui():
                    if r.ok:
                        ans = r.json()
                        self.a.delete("1.0", "end")
                        self.a.insert("end", f"Q: {q}\n\n")
                        self.a.insert("end", f"A: {ans['answer']}\n\n---\n\n")
                        
                        contexts = ans.get("contexts", [])
                        for i, c in enumerate(contexts[:3], 1):
                            self.a.insert("end", f"[Context {i}]\n{c[:300]}...\n\n")
                        
                        self.status_label.configure(text=f"✓ {len(contexts)} contexts")
                        log(f"UI: Query successful, {len(contexts)} contexts", "UI")
                    else:
                        self.a.delete("1.0", "end")
                        self.a.insert("end", f"Error {r.status_code}: {r.text}\n")
                        self.status_label.configure(text="✗ Error")
                        log(f"UI: Query failed {r.status_code}", "UI")
                    
                    # Re-enable button
                    self.query_btn.configure(state="normal")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: Query exception: {e}", "UI")
                
                def update_ui():
                    self.a.delete("1.0", "end")
                    self.a.insert("end", f"Error: {e}\n")
                    self.status_label.configure(text="✗ Connection Error")
                    self.query_btn.configure(state="normal")
                
                self.after(0, update_ui)
        
        # Run in background thread
        threading.Thread(target=run, daemon=True).start()


class SystemTab(ctk.CTkFrame):
    """System statistics tab with auto-refresh"""
    
    def __init__(self, master):
        super().__init__(master)
        
        # Title
        ctk.CTkLabel(self, text="System Monitor", font=("Segoe UI", 18)).pack(pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(self, text="⏳ Loading...", text_color="#999")
        self.status_label.pack(pady=5)
        
        # Stats display
        self.text = ctk.CTkTextbox(self)
        self.text.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Start auto-refresh (scheduled via after)
        self.after(500, self.update_stats)

    def update_stats(self):
        """Update system statistics (non-blocking)"""
        def fetch_stats():
            try:
                r = requests.get("http://localhost:8000/system-stats", timeout=3)
                
                if r.ok:
                    data = r.json()
                    
                    # Format stats
                    stats = "=== System Statistics ===\n\n"
                    stats += f"CPU: {data.get('cpu_percent', 0):.1f}%\n"
                    stats += f"Memory: {data.get('mem_percent', 0):.1f}% "
                    stats += f"({data.get('mem_used_mb', 0)} / {data.get('mem_total_mb', 0)} MB)\n\n"
                    
                    gpu = data.get("gpu", {})
                    if gpu.get("available"):
                        stats += f"GPU: {gpu.get('name', 'Unknown')}\n"
                        stats += f"GPU Utilization: {gpu.get('utilization', 0):.1f}%\n"
                        stats += f"GPU Memory: {gpu.get('memory_used', 0):.0f} / {gpu.get('memory_total', 0):.0f} MB "
                        stats += f"({gpu.get('memory_percent', 0):.1f}%)\n"
                        if gpu.get('temperature'):
                            stats += f"GPU Temp: {gpu.get('temperature')}°C\n"
                    else:
                        stats += "GPU: Not Available\n"
                    
                    stats += f"\nOllama: {'✓ Running' if data.get('ollama_running') else '✗ Stopped'}\n"
                    stats += f"\nVector Store: {CFG.vector_store.upper()}\n"
                    stats += f"Provider: {CFG.provider.upper()}\n"
                    stats += f"Model: {CFG.model_name}\n"
                    
                    # Update UI on main thread
                    def update_ui():
                        self.text.delete("1.0", "end")
                        self.text.insert("end", stats)
                        self.status_label.configure(text="✓ Updated")
                    
                    self.after(0, update_ui)
                else:
                    log(f"UI: System stats API error {r.status_code}", "UI")
                    
                    def update_ui():
                        self.text.delete("1.0", "end")
                        self.text.insert("end", f"API Error: {r.status_code}\n{r.text}\n")
                        self.status_label.configure(text="✗ API Error")
                    
                    self.after(0, update_ui)
                    
            except Exception as e:
                log(f"UI: System stats exception: {e}", "UI")
                
                def update_ui():
                    self.text.delete("1.0", "end")
                    self.text.insert("end", f"Connection Error: {e}\n")
                    self.status_label.configure(text="✗ Connection Error")
                
                self.after(0, update_ui)
        
        # Run fetch in background thread
        threading.Thread(target=fetch_stats, daemon=True).start()
        
        # Schedule next update (after callback)
        self.after(4000, self.update_stats)


class LogsTab(ctk.CTkFrame):
    """Live logs viewer tab with scheduled refresh"""
    
    def __init__(self, master):
        super().__init__(master)
        
        # Title
        ctk.CTkLabel(self, text="Live Logs", font=("Segoe UI", 18)).pack(pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(self, text="", text_color="#999")
        self.status_label.pack(pady=5)
        
        # Log viewer
        self.box = ctk.CTkTextbox(self, wrap="word")
        self.box.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Start auto-refresh (scheduled via after)
        self.after(1000, self.refresh)

    def refresh(self):
        """Refresh log display (non-blocking)"""
        log_file = os.path.join(BASE_DIR, "Logs", "app.log")
        
        def read_logs():
            try:
                if os.path.exists(log_file):
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()[-40:]
                    
                    content = "".join(lines) if lines else "Log file is empty.\n"
                    
                    # Update UI on main thread
                    def update_ui():
                        self.box.delete("1.0", "end")
                        self.box.insert("end", content)
                        self.status_label.configure(text=f"✓ {len(lines)} lines")
                    
                    self.after(0, update_ui)
                else:
                    log(f"UI: Log file not found: {log_file}", "UI")
                    
                    def update_ui():
                        self.box.delete("1.0", "end")
                        self.box.insert("end", f"Log file not found: {log_file}\n")
                        self.status_label.configure(text="✗ Not Found")
                    
                    self.after(0, update_ui)
                    
            except Exception as e:
                log(f"UI: Error reading logs: {e}", "UI")
                
                def update_ui():
                    self.status_label.configure(text="✗ Read Error")
                
                self.after(0, update_ui)
        
        # Run read in background thread
        threading.Thread(target=read_logs, daemon=True).start()
        
        # Schedule next refresh (after callback)
        self.after(4000, self.refresh)


class BridgeTab(ctk.CTkFrame):
    """Cloud Bridge tab for health monitoring and backup controls"""
    
    def __init__(self, master):
        super().__init__(master)
        
        # Title
        ctk.CTkLabel(self, text="Cloud Bridge", font=("Segoe UI", 18)).pack(pady=10)
        
        # Bridge availability
        if not BRIDGE_AVAILABLE:
            ctk.CTkLabel(
                self,
                text="⚠️ Cloud Bridge not available",
                text_color="#ff6b6b"
            ).pack(pady=20)
            return
        
        # Cloud URL display
        cloud_url = os.getenv("CLOUD_URL", "Not configured")
        ctk.CTkLabel(
            self,
            text=f"Cloud URL: {cloud_url}",
            text_color="#999"
        ).pack(pady=5)
        
        # Status label
        self.status_label = ctk.CTkLabel(self, text="⏳ Checking...", text_color="#999")
        self.status_label.pack(pady=10)
        
        # Control buttons frame
        controls_frame = ctk.CTkFrame(self)
        controls_frame.pack(pady=20)
        
        # Test event button
        self.test_btn = ctk.CTkButton(
            controls_frame,
            text="Send Test Event",
            command=self.send_test_event,
            width=180
        )
        self.test_btn.grid(row=0, column=0, padx=10, pady=5)
        
        # Push backup button
        self.backup_btn = ctk.CTkButton(
            controls_frame,
            text="Push Vector Backup",
            command=self.push_backup,
            width=180
        )
        self.backup_btn.grid(row=0, column=1, padx=10, pady=5)
        
        # Auto backup toggle
        self.auto_backup_var = ctk.BooleanVar(value=self.load_auto_backup_setting())
        self.auto_backup_toggle = ctk.CTkCheckBox(
            controls_frame,
            text="Auto Backup on Ingest",
            variable=self.auto_backup_var,
            command=self.toggle_auto_backup
        )
        self.auto_backup_toggle.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Output console
        self.output = ctk.CTkTextbox(self, wrap="word", height=400)
        self.output.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.output.insert("end", "Cloud Bridge Status Monitor\n\n")
        self.output.insert("end", f"URL: {cloud_url}\n")
        self.output.insert("end", f"API Key: {'✓ Set' if os.getenv('CLOUD_KEY') else '✗ Not Set'}\n\n")
        
        # Start health checks
        self.after(1000, self.check_health)
    
    def load_auto_backup_setting(self) -> bool:
        """Load auto backup setting from config file"""
        config_file = os.path.join(BASE_DIR, "ui", "config.json")
        try:
            if os.path.exists(config_file):
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                return config.get("auto_backup", False)
        except Exception as e:
            log(f"UI: Error loading auto backup setting: {e}", "UI")
        return False
    
    def save_auto_backup_setting(self, value: bool):
        """Save auto backup setting to config file"""
        config_file = os.path.join(BASE_DIR, "ui", "config.json")
        try:
            # Load existing config
            config = {}
            if os.path.exists(config_file):
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            # Update setting
            config["auto_backup"] = value
            
            # Save
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(config, f, indent=2)
            
            # Set environment variable for current session
            os.environ["AUTO_BACKUP"] = "true" if value else "false"
            
            log(f"UI: Auto backup set to {value}", "UI")
        except Exception as e:
            log(f"UI: Error saving auto backup setting: {e}", "UI")
    
    def toggle_auto_backup(self):
        """Handle auto backup toggle"""
        value = self.auto_backup_var.get()
        self.save_auto_backup_setting(value)
        status = "enabled" if value else "disabled"
        self.output.insert("end", f"[•] Auto backup {status}\n")
    
    def check_health(self):
        """Check cloud bridge health (non-blocking)"""
        def check():
            try:
                health = bridge.health()
                
                def update_ui():
                    if health.get("status") == "ok":
                        self.status_label.configure(text="🟢 Cloud Online", text_color="#4ade80")
                    else:
                        self.status_label.configure(text="🟡 Cloud Degraded", text_color="#fbbf24")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: Bridge health check failed: {e}", "UI")
                
                def update_ui():
                    self.status_label.configure(text="🔴 Cloud Offline", text_color="#ef4444")
                
                self.after(0, update_ui)
        
        # Run in background
        threading.Thread(target=check, daemon=True).start()
        
        # Schedule next check
        self.after(5000, self.check_health)
    
    def send_test_event(self):
        """Send test event to cloud bridge"""
        self.test_btn.configure(state="disabled")
        self.output.insert("end", "[→] Sending test event...\n")
        
        def run():
            try:
                result = bridge.send_event("ui_test", {
                    "source": "ui",
                    "timestamp": time.time(),
                    "message": "Test event from RAGGITY UI"
                })
                
                def update_ui():
                    self.output.insert("end", f"[+] Test event sent! Response: {result.get('ack')}\n")
                    self.test_btn.configure(state="normal")
                
                self.after(0, update_ui)
                log("UI: Test event sent successfully", "UI")
                
            except Exception as e:
                log(f"UI: Test event failed: {e}", "UI")
                
                def update_ui():
                    self.output.insert("end", f"[x] Test event failed: {e}\n")
                    self.test_btn.configure(state="normal")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()
    
    def push_backup(self):
        """Push vector backup to cloud"""
        self.backup_btn.configure(state="disabled")
        self.output.insert("end", "[→] Pushing vector backup...\n")
        
        def run():
            try:
                # Find vector store path
                vector_path = os.path.join(BASE_DIR, "vector_store", "faiss.index")
                
                if not os.path.exists(vector_path):
                    def update_ui():
                        self.output.insert("end", "[!] Vector index not found. Ingest documents first.\n")
                        self.backup_btn.configure(state="normal")
                    
                    self.after(0, update_ui)
                    return
                
                # Get file size
                size_mb = os.path.getsize(vector_path) / (1024 * 1024)
                
                self.output.insert("end", f"[•] Uploading {size_mb:.2f} MB...\n")
                
                result = bridge.push_vector_backup(vector_path)
                
                def update_ui():
                    self.output.insert("end", f"[+] Backup complete! Stored: {result.get('stored')}\n")
                    self.output.insert("end", f"[•] Size: {result.get('size')} bytes\n")
                    self.backup_btn.configure(state="normal")
                
                self.after(0, update_ui)
                log(f"UI: Vector backup pushed ({size_mb:.2f} MB)", "UI")
                
            except FileNotFoundError as e:
                log(f"UI: Backup file not found: {e}", "UI")
                
                def update_ui():
                    self.output.insert("end", f"[x] File not found: {e}\n")
                    self.backup_btn.configure(state="normal")
                
                self.after(0, update_ui)
                
            except Exception as e:
                log(f"UI: Backup failed: {e}", "UI")
                
                def update_ui():
                    self.output.insert("end", f"[x] Backup failed: {e}\n")
                    self.backup_btn.configure(state="normal")
                
                self.after(0, update_ui)
        
        threading.Thread(target=run, daemon=True).start()


if __name__ == "__main__":
    apply_theme()
    log("UI: Starting RAGGITY ZYZTEM 2.0", "UI")
    app = RaggityUI()
    app.mainloop()
