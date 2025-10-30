"""
System Monitor - Real-time CPU, RAM, and GPU monitoring using psutil
"""

import os
import sys
import threading
import time
import psutil
import socket
from typing import Dict, Any

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from logger import get_logger

# Import GPU status from core
try:
    from core.gpu import get_gpu_status
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False
    def get_gpu_status():
        return {"available": False}

log = get_logger("system_monitor")


class SystemMonitor:
    """Monitors system resources (CPU, RAM, GPU) and processes"""
    
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.metrics = {
            "cpu_percent": 0.0,
            "mem_percent": 0.0,
            "mem_used_mb": 0,
            "mem_total_mb": 0,
            "gpu": {"available": False},
            "ollama_running": False,
            "timestamp": None
        }
        self.update_interval = 5.0  # seconds
        
        log.info("SystemMonitor initialized")
    
    def check_port(self, port: int) -> bool:
        """Check if a port is listening"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result == 0
        except (OSError, socket.error) as e:
            log.warning(f"Port check failed for {port}: {e}")
            return False
    
    def get_snapshot(self) -> Dict[str, Any]:
        """
        Get current system metrics snapshot
        
        Returns:
            Dictionary with:
                - cpu_percent: CPU usage percentage
                - mem_percent: Memory usage percentage
                - mem_used_mb: Memory used in MB
                - mem_total_mb: Total memory in MB
                - gpu: GPU status dict (from core.gpu.get_gpu_status)
                - ollama_running: Boolean if Ollama is accessible
                - timestamp: Unix timestamp
        """
        try:
            # CPU and RAM using psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory()
            
            # GPU status from core module
            gpu_status = get_gpu_status() if GPU_AVAILABLE else {"available": False}
            
            # Check Ollama availability
            ollama_running = self.check_port(11434)
            
            snapshot = {
                "cpu_percent": round(cpu_percent, 2),
                "mem_percent": round(mem.percent, 2),
                "mem_used_mb": int(mem.used / (1024 * 1024)),
                "mem_total_mb": int(mem.total / (1024 * 1024)),
                "gpu": gpu_status,
                "ollama_running": ollama_running,
                "timestamp": time.time()
            }
            
            return snapshot
            
        except Exception as e:
            log.error(f"Error getting snapshot: {e}")
            return {
                "cpu_percent": 0.0,
                "mem_percent": 0.0,
                "mem_used_mb": 0,
                "mem_total_mb": 0,
                "gpu": {"available": False},
                "ollama_running": False,
                "timestamp": time.time(),
                "error": str(e)
            }
    
    def update_metrics(self):
        """Update cached metrics (for background monitoring)"""
        try:
            self.metrics = self.get_snapshot()
        except Exception as e:
            log.error(f"Error updating metrics: {e}")
    
    def monitor_loop(self):
        """Main monitoring loop (runs in background thread)"""
        while self.running:
            try:
                self.update_metrics()
            except Exception as e:
                log.error(f"Error in monitor loop: {e}")
                import traceback
                log.error(traceback.format_exc())
            
            time.sleep(self.update_interval)
    
    def start(self):
        """Start background monitoring"""
        if self.running:
            log.warning("Monitor already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitor_thread.start()
        log.info("System monitor started")
    
    def stop(self):
        """Stop background monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        log.info("System monitor stopped")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cached metrics (from background thread)"""
        return self.metrics.copy()


# Global monitor instance
_monitor_instance = None


def get_system_monitor() -> SystemMonitor:
    """Get global system monitor (singleton)"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SystemMonitor()
    return _monitor_instance
