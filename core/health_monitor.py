"""
Health Monitor - Centralized health checking for all modules
Polls module /health endpoints and tracks status
"""

import threading
import time
import requests
import socket
import sys
import subprocess
import psutil

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

try:
    from logger import log
except ImportError:
    def log(msg, category="HEALTH"):
        print(f"[{category}] {msg}")

from core.module_registry import get_registry
from core.config_manager import get_suite_config

class HealthMonitor:
    """Monitors health of all registered modules"""
    
    def __init__(self, interval_seconds=30):
        self.interval = interval_seconds
        self.running = False
        self.monitor_thread = None
        self.health_status = {}  # module_id -> health info
        self.lock = threading.Lock()
        self.ollama_running = False
        self.ollama_port = 11434
    
    def start(self):
        """Start health monitoring in background thread"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        log(f"Health monitor started (interval: {self.interval}s)", "HEALTH")
    
    def stop(self):
        """Stop health monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        log("Health monitor stopped", "HEALTH")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                self.check_all_modules()
                self.check_ollama()
            except Exception as e:
                log(f"Error in health monitor loop: {e}", "HEALTH", level="ERROR")
            
            time.sleep(self.interval)
    
    def check_module(self, module_id):
        """Check health of a single module"""
        registry = get_registry()
        module = registry.get_module(module_id)
        
        if not module:
            return {
                "status": "unknown",
                "message": "Module not registered"
            }
        
        port = module.get('port')
        process_id = module.get('process_id')
        
        health_info = {
            "module_id": module_id,
            "port": port,
            "process_id": process_id,
            "status": "unknown",
            "checks": {}
        }
        
        # Check 1: Process alive
        if process_id:
            try:
                process = psutil.Process(process_id)
                if process.is_running():
                    health_info["checks"]["process"] = True
                else:
                    health_info["checks"]["process"] = False
                    health_info["status"] = "unhealthy"
                    health_info["message"] = "Process not running"
                    self._update_health_status(module_id, health_info)
                    return health_info
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                health_info["checks"]["process"] = False
                health_info["status"] = "unhealthy"
                health_info["message"] = "Process not found"
                self._update_health_status(module_id, health_info)
                return health_info
        else:
            health_info["checks"]["process"] = None  # Not started
            if module.get('status') == 'running':
                # Process should exist but doesn't
                health_info["status"] = "error"
                health_info["message"] = "Process ID missing"
                self._update_health_status(module_id, health_info)
                return health_info
        
        # Check 2: Port responding
        if port:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('127.0.0.1', port))
                sock.close()
                port_open = (result == 0)
                health_info["checks"]["port"] = port_open
                
                if not port_open:
                    health_info["status"] = "unhealthy"
                    health_info["message"] = "Port not responding"
                    self._update_health_status(module_id, health_info)
                    return health_info
            except Exception as e:
                health_info["checks"]["port"] = False
                health_info["status"] = "error"
                health_info["message"] = f"Port check failed: {e}"
                self._update_health_status(module_id, health_info)
                return health_info
        
        # Check 3: HTTP health endpoint
        if port and health_info["checks"].get("port"):
            try:
                response = requests.get(
                    f"http://127.0.0.1:{port}/health",
                    timeout=2
                )
                if response.status_code == 200:
                    health_data = response.json()
                    health_info["checks"]["health_endpoint"] = True
                    health_info["health_data"] = health_data
                    health_info["status"] = health_data.get("status", "healthy")
                else:
                    health_info["checks"]["health_endpoint"] = False
                    health_info["status"] = "degraded"
                    health_info["message"] = f"Health endpoint returned {response.status_code}"
            except requests.exceptions.RequestException as e:
                health_info["checks"]["health_endpoint"] = False
                health_info["status"] = "degraded"
                health_info["message"] = f"Health endpoint unreachable: {e}"
        else:
            health_info["checks"]["health_endpoint"] = None
        
        # Determine overall status
        if health_info["status"] == "unknown":
            if health_info["checks"].get("health_endpoint"):
                health_info["status"] = "healthy"
            elif health_info["checks"].get("port") and not process_id:
                health_info["status"] = "stopped"  # Not started yet
            else:
                health_info["status"] = "unhealthy"
        
        self._update_health_status(module_id, health_info)
        return health_info
    
    def check_all_modules(self):
        """Check health of all registered modules"""
        registry = get_registry()
        modules = registry.get_all_modules()
        
        for module in modules:
            module_id = module.get('module_id')
            if module_id:
                self.check_module(module_id)
    
    def check_ollama(self):
        """Check if Ollama is running"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', self.ollama_port))
            sock.close()
            
            self.ollama_running = (result == 0)
        except:
            self.ollama_running = False
    
    def _update_health_status(self, module_id, health_info):
        """Update health status cache"""
        with self.lock:
            self.health_status[module_id] = health_info
            
            # Update registry status
            registry = get_registry()
            if health_info["status"] == "healthy":
                registry.set_module_status(module_id, "running")
            elif health_info["status"] == "unhealthy":
                registry.set_module_status(module_id, "error")
            elif health_info["status"] == "stopped":
                registry.set_module_status(module_id, "stopped")
    
    def get_module_health(self, module_id):
        """Get cached health status for a module"""
        with self.lock:
            return self.health_status.get(module_id, {
                "status": "unknown",
                "message": "Not checked yet"
            })
    
    def get_all_health(self):
        """Get health status for all modules"""
        with self.lock:
            return self.health_status.copy()
    
    def is_ollama_running(self):
        """Check if Ollama is running"""
        return self.ollama_running

# Global health monitor instance
_health_monitor_instance = None

def get_health_monitor():
    """Get global health monitor instance (singleton)"""
    global _health_monitor_instance
    if _health_monitor_instance is None:
        suite_config = get_suite_config()
        interval = suite_config.get("monitoring", {}).get("health_check_interval_seconds", 30)
        _health_monitor_instance = HealthMonitor(interval_seconds=interval)
    return _health_monitor_instance




