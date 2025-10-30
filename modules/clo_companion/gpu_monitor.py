"""
GPU Monitor - Monitors GPU usage via psutil or nvidia-smi
"""

import os
import sys
import subprocess
from typing import Dict, Optional

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
except ImportError:
    def log(msg, category="CLO"):
        print(f"[{category}] {msg}")

class GPUMonitor:
    """Monitors GPU usage and provides throttling recommendations"""
    
    def __init__(self):
        self.nvidia_available = self._check_nvidia_available()
        log(f"GPUMonitor initialized (nvidia: {self.nvidia_available})", "CLO")
    
    def _check_nvidia_available(self) -> bool:
        """Check if nvidia-smi is available"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--version"],
                capture_output=True,
                timeout=2
            )
            return result.returncode == 0
        except:
            return False
    
    def get_gpu_status(self) -> Dict:
        """
        Get current GPU status
        
        Returns:
            Dict with utilization, memory, temperature, etc.
        """
        if not self.nvidia_available:
            return {
                "available": False,
                "utilization": 0,
                "memory_used": 0,
                "memory_total": 0,
                "temperature": 0,
                "recommendation": "cpu_mode"
            }
        
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                data = result.stdout.strip().split(', ')
                if len(data) >= 4:
                    utilization = float(data[0])
                    memory_used = float(data[1])
                    memory_total = float(data[2])
                    temperature = float(data[3])
                    
                    recommendation = "realistic_render"
                    if utilization > 85:
                        recommendation = "fast_preview"
                    elif utilization > 70:
                        recommendation = "throttle_render"
                    
                    return {
                        "available": True,
                        "utilization": utilization,
                        "memory_used": memory_used,
                        "memory_total": memory_total,
                        "memory_percent": (memory_used / memory_total * 100) if memory_total > 0 else 0,
                        "temperature": temperature,
                        "recommendation": recommendation
                    }
        except Exception as e:
            log(f"Error querying GPU: {e}", "CLO", level="WARNING")
        
        return {
            "available": False,
            "utilization": 0,
            "memory_used": 0,
            "memory_total": 0,
            "temperature": 0,
            "recommendation": "cpu_mode"
        }
    
    def should_use_fast_preview(self) -> bool:
        """Check if should fallback to fast preview"""
        status = self.get_gpu_status()
        return status.get("utilization", 0) > 85 or not status.get("available", False)
    
    def get_cpu_usage(self) -> float:
        """Get CPU usage percentage"""
        try:
            import psutil
            return psutil.cpu_percent(interval=1)
        except:
            return 0.0




