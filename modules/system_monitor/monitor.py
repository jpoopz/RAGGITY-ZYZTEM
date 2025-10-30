"""
System Monitor - Real process and resource monitoring
"""

import os
import sys
import threading
import time
import psutil
import socket

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
    from core.module_registry import get_registry
    from core.health_monitor import get_health_monitor
except ImportError:
    def log(msg, category="SYSTEM"):
        print(f"[{category}] {msg}")
    def get_registry():
        return None
    def get_health_monitor():
        return None

class SystemMonitor:
    """Monitors system resources and processes"""
    
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.metrics = {
            "cpu_percent": 0.0,
            "ram_percent": 0.0,
            "ram_mb": 0,
            "gpu_percent": None,
            "ollama_running": False,
            "module_ports": {},
            "timestamp": None
        }
        self.update_interval = 5.0  # seconds
    
    def check_gpu(self):
        """Check GPU usage if nvidia-smi available"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                gpu_percent = float(result.stdout.strip())
                return gpu_percent
        except:
            pass
        return None
    
    def check_port(self, port):
        """Check if port is listening"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except:
            return False
    
    def update_metrics(self):
        """Update all system metrics"""
        try:
            # CPU and RAM
            cpu_percent = psutil.cpu_percent(interval=0.1)
            ram = psutil.virtual_memory()
            
            # GPU
            gpu_percent = self.check_gpu()
            
            # Ollama
            ollama_running = self.check_port(11434)
            
            # Module ports
            registry = get_registry()
            module_ports = {}
            if registry:
                modules = registry.get_all_modules()
                for module in modules:
                    module_id = module.get('module_id')
                    port = module.get('port')
                    if port:
                        module_ports[module_id] = {
                            "port": port,
                            "listening": self.check_port(port)
                        }
            
            self.metrics = {
                "cpu_percent": cpu_percent,
                "ram_percent": ram.percent,
                "ram_mb": int(ram.used / (1024 * 1024)),
                "ram_total_mb": int(ram.total / (1024 * 1024)),
                "gpu_percent": gpu_percent,
                "ollama_running": ollama_running,
                "module_ports": module_ports,
                "timestamp": time.time()
            }
            
        except Exception as e:
            log(f"Error updating metrics: {e}", "SYSTEM", level="ERROR")
    
    def monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self.update_metrics()
            except Exception as e:
                log(f"Error in monitor loop: {e}", "SYSTEM", level="ERROR")
            
            time.sleep(self.update_interval)
    
    def start(self):
        """Start monitoring"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        log("System monitor started", "SYSTEM")
    
    def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        log("System monitor stopped", "SYSTEM")
    
    def get_metrics(self):
        """Get current metrics"""
        return self.metrics.copy()

import subprocess

# Global monitor instance
_monitor_instance = None

def get_system_monitor():
    """Get global system monitor (singleton)"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SystemMonitor()
    return _monitor_instance




