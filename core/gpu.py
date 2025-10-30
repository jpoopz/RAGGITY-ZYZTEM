"""
GPU Status Module
Provides unified GPU monitoring with optional pynvml support
"""

import subprocess
from typing import Dict, Optional


def get_gpu_status() -> Dict:
    """
    Get GPU status using nvidia-smi (fallback) or pynvml (preferred)
    
    Returns:
        Dictionary with GPU metrics:
            - available: bool - GPU detected and accessible
            - utilization: float - GPU usage percentage
            - memory_used: float - Memory used in MB
            - memory_total: float - Total memory in MB
            - memory_percent: float - Memory usage percentage
            - temperature: Optional[float] - GPU temperature in Celsius
            - name: Optional[str] - GPU name
            - driver_version: Optional[str] - Driver version
    """
    # Try pynvml first (more detailed info)
    try:
        import pynvml
        
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        
        if device_count == 0:
            pynvml.nvmlShutdown()
            return _unavailable_gpu()
        
        # Get first GPU
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        
        # Get GPU info
        name = pynvml.nvmlDeviceGetName(handle)
        if isinstance(name, bytes):
            name = name.decode('utf-8')
        
        mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        
        # Try to get temperature (may not be available on all systems)
        try:
            temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        except:
            temp = None
        
        # Try to get driver version
        try:
            driver_version = pynvml.nvmlSystemGetDriverVersion()
            if isinstance(driver_version, bytes):
                driver_version = driver_version.decode('utf-8')
        except:
            driver_version = None
        
        pynvml.nvmlShutdown()
        
        return {
            "available": True,
            "utilization": float(util.gpu),
            "memory_used": float(mem_info.used / (1024 * 1024)),  # MB
            "memory_total": float(mem_info.total / (1024 * 1024)),  # MB
            "memory_percent": float((mem_info.used / mem_info.total) * 100),
            "temperature": temp,
            "name": name,
            "driver_version": driver_version
        }
        
    except ImportError:
        # pynvml not available, try nvidia-smi
        pass
    except Exception:
        # pynvml failed, try nvidia-smi
        pass
    
    # Fallback to nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,name", 
             "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            data = result.stdout.strip().split(', ')
            if len(data) >= 5:
                return {
                    "available": True,
                    "utilization": float(data[0]),
                    "memory_used": float(data[1]),
                    "memory_total": float(data[2]),
                    "memory_percent": (float(data[1]) / float(data[2]) * 100) if float(data[2]) > 0 else 0,
                    "temperature": float(data[3]) if data[3] else None,
                    "name": data[4].strip() if len(data) > 4 else "Unknown GPU",
                    "driver_version": None
                }
    except FileNotFoundError:
        # nvidia-smi not installed
        pass
    except Exception:
        # nvidia-smi failed
        pass
    
    # No GPU available
    return _unavailable_gpu()


def _unavailable_gpu() -> Dict:
    """Return dict for unavailable GPU"""
    return {
        "available": False,
        "utilization": 0.0,
        "memory_used": 0.0,
        "memory_total": 0.0,
        "memory_percent": 0.0,
        "temperature": None,
        "name": None,
        "driver_version": None
    }

