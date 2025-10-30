"""
Engine Manager - Handles Ollama and llama.cpp backend switching
"""

import os
import sys
import subprocess
import psutil

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
    from core.config_manager import get_suite_config
except ImportError:
    def log(msg, category="ENGINE"):
        print(f"[{category}] {msg}")
    def get_suite_config():
        return {}

class EngineManager:
    """Manages LLM engine selection (Ollama / llama.cpp / Auto)"""
    
    def __init__(self):
        self.config = get_suite_config()
        self.resources = self.config.get("resources", {})
        self.current_engine = self.config.get("engine", {}).get("backend", "auto")
        self.low_power_mode = False
        
        self.check_system_resources()
    
    def check_system_resources(self):
        """Check if system should use low-power mode"""
        try:
            # Check RAM
            ram_gb = psutil.virtual_memory().total / (1024**3)
            
            # Check GPU availability
            has_gpu = self.check_gpu_available()
            
            # Low-power mode if: RAM < 10GB or no GPU
            if ram_gb < 10 or not has_gpu:
                self.low_power_mode = True
                log(f"Low-power mode enabled (RAM: {ram_gb:.1f}GB, GPU: {has_gpu})", "ENGINE")
            else:
                self.low_power_mode = False
        except Exception as e:
            log(f"Error checking system resources: {e}", "ENGINE", level="ERROR")
            self.low_power_mode = False
    
    def check_gpu_available(self):
        """Check if GPU (CUDA) is available"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            # Check nvidia-smi
            try:
                result = subprocess.run(
                    ["nvidia-smi"],
                    capture_output=True,
                    timeout=2
                )
                return result.returncode == 0
            except:
                return False
        except Exception:
            return False
    
    def check_ollama_running(self):
        """Check if Ollama service is running"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', 11434))
            sock.close()
            return result == 0
        except:
            return False
    
    def check_llama_cpp_available(self):
        """Check if llama.cpp is available"""
        possible_paths = [
            os.path.join(BASE_DIR, "local_engines", "llama_cpp", "llama-cpp-python"),
            os.path.join(BASE_DIR, "local_engines", "llama_cpp", "llama-cli"),
            "llama-cpp-python",
            "llama-cli"
        ]
        
        for path in possible_paths:
            if os.path.exists(path) or self._command_exists(path):
                return True
        
        return False
    
    def _command_exists(self, cmd):
        """Check if command exists"""
        try:
            result = subprocess.run(
                ["where" if os.name == "nt" else "which", cmd.split()[0]],
                capture_output=True,
                timeout=1
            )
            return result.returncode == 0
        except:
            return False
    
    def get_active_engine(self):
        """Get currently active engine based on mode"""
        if self.current_engine == "auto":
            # Auto-select based on resources
            if self.low_power_mode:
                if self.check_llama_cpp_available():
                    return "llama.cpp"
                else:
                    log("No engines available, falling back to Ollama", "ENGINE", level="WARNING")
                    return "ollama"
            else:
                if self.check_ollama_running():
                    return "ollama"
                elif self.check_llama_cpp_available():
                    return "llama.cpp"
                else:
                    return "ollama"  # Default fallback
        else:
            return self.current_engine
    
    def call_llm(self, prompt, model="llama3.2"):
        """Call LLM using active engine"""
        engine = self.get_active_engine()
        
        if engine == "ollama":
            return self._call_ollama(prompt, model)
        elif engine == "llama.cpp":
            return self._call_llama_cpp(prompt, model)
        else:
            log(f"Unknown engine: {engine}", "ENGINE", level="ERROR")
            return None
    
    def _call_ollama(self, prompt, model):
        """Call Ollama"""
        try:
            result = subprocess.run(
                ["ollama", "run", model, prompt],
                capture_output=True,
                text=True,
                timeout=120,
                encoding="utf-8"
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                log(f"Ollama error: {result.stderr}", "ENGINE", level="ERROR")
                return None
        except Exception as e:
            log(f"Error calling Ollama: {e}", "ENGINE", level="ERROR")
            return None
    
    def _call_llama_cpp(self, prompt, model):
        """Call llama.cpp (CPU fallback)"""
        try:
            # Try pyllamacpp first
            try:
                from pyllamacpp.model import Model as LlamaModel
                
                model_path = os.path.join(
                    BASE_DIR,
                    "local_engines",
                    "llama_cpp",
                    "models",
                    f"{model}.bin"
                )
                
                if not os.path.exists(model_path):
                    log(f"Model not found: {model_path}", "ENGINE", level="ERROR")
                    return None
                
                llama_model = LlamaModel(ggml_model=model_path, n_ctx=2048)
                response = llama_model.generate(prompt, n_predict=256)
                return response
                
            except ImportError:
                # Fallback to CLI
                llama_cli = os.path.join(
                    BASE_DIR,
                    "local_engines",
                    "llama_cpp",
                    "llama-cli"
                )
                
                model_path = os.path.join(
                    BASE_DIR,
                    "local_engines",
                    "llama_cpp",
                    "models",
                    f"{model}.bin"
                )
                
                if not os.path.exists(llama_cli) or not os.path.exists(model_path):
                    log("llama.cpp not properly configured", "ENGINE", level="ERROR")
                    return None
                
                result = subprocess.run(
                    [llama_cli, "-m", model_path, "-p", prompt],
                    capture_output=True,
                    text=True,
                    timeout=120,
                    encoding="utf-8"
                )
                
                if result.returncode == 0:
                    return result.stdout.strip()
                else:
                    log(f"llama.cpp error: {result.stderr}", "ENGINE", level="ERROR")
                    return None
                    
        except Exception as e:
            log(f"Error calling llama.cpp: {e}", "ENGINE", level="ERROR")
            return None
    
    def set_engine(self, engine):
        """Set engine backend (ollama / llama.cpp / auto)"""
        if engine not in ["ollama", "llama.cpp", "auto"]:
            log(f"Invalid engine: {engine}", "ENGINE", level="ERROR")
            return False
        
        self.current_engine = engine
        
        # Save to config
        suite_config = get_suite_config()
        suite_config.setdefault("engine", {})["backend"] = engine
        from core.config_manager import save_suite_config
        save_suite_config(suite_config)
        
        log(f"Engine set to: {engine}", "ENGINE")
        
        # Publish event
        try:
            from core.event_bus import publish_event
            publish_event("engine.switch", "engine_manager", {"engine": engine})
        except:
            pass
        
        return True

# Global engine manager instance
_engine_manager = None

def get_engine_manager():
    """Get global engine manager (singleton)"""
    global _engine_manager
    if _engine_manager is None:
        _engine_manager = EngineManager()
    return _engine_manager

