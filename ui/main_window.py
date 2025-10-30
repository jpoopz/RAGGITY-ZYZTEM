"""
Main UI Window - CustomTkinter interface for RAG System
Provides tabs for Ingest, Query, Logs, and System monitoring
"""

import os
import sys
import threading
import time
from pathlib import Path
from tkinter import filedialog

# Add parent to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

try:
    import customtkinter as ctk
    import requests
except ImportError as e:
    print(f"Error: Missing dependencies - {e}")
    print("Please run: pip install customtkinter requests")
    sys.exit(1)

# API Configuration
API_BASE = "http://localhost:8000"
API_TIMEOUT = 30


class RAGSystemUI(ctk.CTk):
    """Main UI window for RAG System"""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("RAG System Control Panel")
        self.geometry("1000x700")
        
        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Status variables
        self.api_status = ctk.StringVar(value="Checking...")
        self.gpu_status = ctk.StringVar(value="Unknown")
        
        # Build UI
        self.create_status_bar()
        self.create_tabs()
        
        # Start background updates
        self.running = True
        self.update_thread = threading.Thread(target=self.update_status_loop, daemon=True)
        self.update_thread.start()
    
    def create_status_bar(self):
        """Create top status bar"""
        status_frame = ctk.CTkFrame(self, height=50)
        status_frame.pack(fill="x", padx=10, pady=5)
        
        # API Status
        api_label = ctk.CTkLabel(
            status_frame,
            text="API:",
            font=("Arial", 12, "bold")
        )
        api_label.pack(side="left", padx=10)
        
        self.api_status_label = ctk.CTkLabel(
            status_frame,
            textvariable=self.api_status,
            font=("Arial", 12)
        )
        self.api_status_label.pack(side="left", padx=5)
        
        # GPU Status
        gpu_label = ctk.CTkLabel(
            status_frame,
            text="GPU:",
            font=("Arial", 12, "bold")
        )
        gpu_label.pack(side="left", padx=20)
        
        self.gpu_status_label = ctk.CTkLabel(
            status_frame,
            textvariable=self.gpu_status,
            font=("Arial", 12)
        )
        self.gpu_status_label.pack(side="left", padx=5)
    
    def create_tabs(self):
        """Create main tab view"""
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        self.tabview.add("Ingest")
        self.tabview.add("Query")
        self.tabview.add("Logs")
        self.tabview.add("System")
        
        # Build each tab
        self.build_ingest_tab()
        self.build_query_tab()
        self.build_logs_tab()
        self.build_system_tab()
    
    def build_ingest_tab(self):
        """Build the Ingest tab"""
        tab = self.tabview.tab("Ingest")
        
        # Instructions
        instructions = ctk.CTkLabel(
            tab,
            text="Select a file to ingest into the RAG system",
            font=("Arial", 14)
        )
        instructions.pack(pady=20)
        
        # File picker button
        self.select_file_btn = ctk.CTkButton(
            tab,
            text="Select File",
            command=self.select_and_ingest_file,
            width=200,
            height=40
        )
        self.select_file_btn.pack(pady=10)
        
        # Status text
        self.ingest_status = ctk.CTkTextbox(tab, height=400)
        self.ingest_status.pack(fill="both", expand=True, padx=20, pady=10)
        self.ingest_status.insert("1.0", "No file ingested yet.\n")
    
    def build_query_tab(self):
        """Build the Query tab"""
        tab = self.tabview.tab("Query")
        
        # Query input
        query_label = ctk.CTkLabel(
            tab,
            text="Enter your query:",
            font=("Arial", 14)
        )
        query_label.pack(pady=10)
        
        self.query_input = ctk.CTkEntry(tab, width=600, height=40)
        self.query_input.pack(pady=10)
        
        # Query button
        query_btn = ctk.CTkButton(
            tab,
            text="Submit Query",
            command=self.submit_query,
            width=200,
            height=40
        )
        query_btn.pack(pady=10)
        
        # Results
        results_label = ctk.CTkLabel(
            tab,
            text="Results:",
            font=("Arial", 12, "bold")
        )
        results_label.pack(pady=5)
        
        self.query_results = ctk.CTkTextbox(tab, height=400)
        self.query_results.pack(fill="both", expand=True, padx=20, pady=10)
        self.query_results.insert("1.0", "No queries yet.\n")
    
    def build_logs_tab(self):
        """Build the Logs tab"""
        tab = self.tabview.tab("Logs")
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            tab,
            text="Refresh Logs",
            command=self.refresh_logs,
            width=150,
            height=35
        )
        refresh_btn.pack(pady=10)
        
        # Log viewer
        self.log_viewer = ctk.CTkTextbox(tab, height=550)
        self.log_viewer.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Load logs
        self.refresh_logs()
    
    def build_system_tab(self):
        """Build the System tab"""
        tab = self.tabview.tab("System")
        
        # Stats display
        stats_label = ctk.CTkLabel(
            tab,
            text="System Statistics",
            font=("Arial", 16, "bold")
        )
        stats_label.pack(pady=20)
        
        self.stats_text = ctk.CTkTextbox(tab, height=500)
        self.stats_text.pack(fill="both", expand=True, padx=20, pady=10)
        self.stats_text.insert("1.0", "Loading system stats...\n")
        
        # Auto-refresh every 5 seconds
        self.update_system_stats()
    
    # ========== API Methods ==========
    
    def check_api_status(self):
        """Check if API is reachable"""
        try:
            response = requests.get(f"{API_BASE}/health", timeout=2)
            if response.status_code == 200:
                self.api_status.set("✓ Connected")
                return True
            else:
                self.api_status.set("✗ Error")
                return False
        except requests.exceptions.RequestException:
            self.api_status.set("✗ Offline")
            return False
    
    def check_gpu_status(self):
        """Check GPU status from API"""
        try:
            response = requests.get(f"{API_BASE}/system-stats", timeout=2)
            if response.status_code == 200:
                data = response.json()
                gpu = data.get("gpu", {})
                if gpu.get("available"):
                    name = gpu.get("name", "Unknown")
                    util = gpu.get("utilization", 0)
                    self.gpu_status.set(f"{name} ({util:.0f}%)")
                else:
                    self.gpu_status.set("Not Available")
            else:
                self.gpu_status.set("Unknown")
        except requests.exceptions.RequestException:
            self.gpu_status.set("Unknown")
    
    def select_and_ingest_file(self):
        """Select and ingest a file"""
        filename = filedialog.askopenfilename(
            title="Select file to ingest",
            filetypes=[
                ("Text files", "*.txt"),
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )
        
        if not filename:
            return
        
        self.ingest_status.delete("1.0", "end")
        self.ingest_status.insert("1.0", f"Ingesting: {filename}\n\n")
        
        # Ingest file in background
        thread = threading.Thread(target=self._ingest_file_thread, args=(filename,))
        thread.start()
    
    def _ingest_file_thread(self, filepath):
        """Background thread for file ingestion"""
        try:
            with open(filepath, 'rb') as f:
                files = {'f': (os.path.basename(filepath), f)}
                response = requests.post(
                    f"{API_BASE}/ingest-file",
                    files=files,
                    timeout=API_TIMEOUT
                )
            
            if response.status_code == 200:
                result = response.json()
                self.ingest_status.insert("end", f"✓ Success!\n\n{result}\n")
            else:
                self.ingest_status.insert("end", f"✗ Error: {response.status_code}\n{response.text}\n")
        except Exception as e:
            self.ingest_status.insert("end", f"✗ Error: {e}\n")
    
    def submit_query(self):
        """Submit a query to the API"""
        query = self.query_input.get().strip()
        
        if not query:
            return
        
        self.query_results.delete("1.0", "end")
        self.query_results.insert("1.0", f"Query: {query}\n\nSearching...\n")
        
        # Query in background
        thread = threading.Thread(target=self._query_thread, args=(query,))
        thread.start()
    
    def _query_thread(self, query):
        """Background thread for querying"""
        try:
            response = requests.get(
                f"{API_BASE}/query",
                params={"q": query, "k": 5},
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "No answer")
                contexts = result.get("contexts", [])
                
                self.query_results.delete("1.0", "end")
                self.query_results.insert("1.0", f"Query: {query}\n\n")
                self.query_results.insert("end", f"Answer:\n{answer}\n\n")
                self.query_results.insert("end", f"Contexts ({len(contexts)}):\n")
                for i, ctx in enumerate(contexts[:3], 1):
                    self.query_results.insert("end", f"\n[{i}] {ctx[:200]}...\n")
            else:
                self.query_results.delete("1.0", "end")
                self.query_results.insert("1.0", f"Error: {response.status_code}\n{response.text}\n")
        except Exception as e:
            self.query_results.delete("1.0", "end")
            self.query_results.insert("1.0", f"Error: {e}\n")
    
    def refresh_logs(self):
        """Refresh the logs display"""
        log_file = BASE_DIR / "Logs" / "app.log"
        
        self.log_viewer.delete("1.0", "end")
        
        if log_file.exists():
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    # Show last 100 lines
                    tail_lines = lines[-100:] if len(lines) > 100 else lines
                    self.log_viewer.insert("1.0", "".join(tail_lines))
            except Exception as e:
                self.log_viewer.insert("1.0", f"Error reading logs: {e}\n")
        else:
            self.log_viewer.insert("1.0", "Log file not found.\n")
    
    def update_system_stats(self):
        """Update system statistics"""
        if not self.running:
            return
        
        try:
            response = requests.get(f"{API_BASE}/system-stats", timeout=2)
            if response.status_code == 200:
                data = response.json()
                
                # Format stats
                stats_text = "=== System Statistics ===\n\n"
                stats_text += f"CPU Usage: {data.get('cpu_percent', 0):.1f}%\n"
                stats_text += f"Memory Usage: {data.get('mem_percent', 0):.1f}%\n"
                stats_text += f"Memory: {data.get('mem_used_mb', 0)} / {data.get('mem_total_mb', 0)} MB\n\n"
                
                gpu = data.get("gpu", {})
                if gpu.get("available"):
                    stats_text += f"GPU: {gpu.get('name', 'Unknown')}\n"
                    stats_text += f"GPU Utilization: {gpu.get('utilization', 0):.1f}%\n"
                    stats_text += f"GPU Memory: {gpu.get('memory_used', 0):.0f} / {gpu.get('memory_total', 0):.0f} MB\n"
                    if gpu.get('temperature'):
                        stats_text += f"GPU Temperature: {gpu.get('temperature')}°C\n"
                else:
                    stats_text += "GPU: Not Available\n"
                
                stats_text += f"\nOllama: {'✓ Running' if data.get('ollama_running') else '✗ Not Running'}\n"
                
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", stats_text)
            else:
                self.stats_text.delete("1.0", "end")
                self.stats_text.insert("1.0", f"Error: {response.status_code}\n")
        except Exception as e:
            self.stats_text.delete("1.0", "end")
            self.stats_text.insert("1.0", f"Error: {e}\n")
        
        # Schedule next update
        self.after(5000, self.update_system_stats)
    
    def update_status_loop(self):
        """Background loop to update status bar"""
        while self.running:
            self.check_api_status()
            self.check_gpu_status()
            time.sleep(5)
    
    def on_closing(self):
        """Handle window closing"""
        self.running = False
        self.destroy()


def main():
    """Main entry point"""
    app = RAGSystemUI()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()

