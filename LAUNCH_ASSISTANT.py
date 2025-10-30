"""
Julian Assistant Suite - Smart Launcher
Handles initialization, dependency checking, and startup
Version: 7.8.0-Julian-SmartLauncher
"""

import os
import sys
import subprocess
import time
import threading
from pathlib import Path

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

LOG_FILE = os.path.join(BASE_DIR, "Logs", "launcher.log")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def log(message, level="INFO"):
    """Log to launcher.log"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{level}] {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except:
        pass

log("==========================================")
log("Julian Assistant Suite Launcher Starting")
log("Version: 7.9.7-Julian-DynamicLLMRouter")
log("==========================================")

# Create splash screen
splash = None
try:
    import tkinter as tk
    from tkinter import ttk
    
    splash = tk.Tk()
    splash.title("Julian Assistant Suite")
    splash.geometry("400x250")
    splash.configure(bg="#1a1a1a")
    
    # Center on screen
    splash.update_idletasks()
    x = (splash.winfo_screenwidth() // 2) - (400 // 2)
    y = (splash.winfo_screenheight() // 2) - (250 // 2)
    splash.geometry(f"400x250+{x}+{y}")
    
    # Remove title bar decorations
    splash.overrideredirect(True)
    
    # Title
    title_label = tk.Label(splash, text="Julian Assistant Suite", 
                          font=("Arial", 18, "bold"), 
                          bg="#1a1a1a", fg="#4CAF50")
    title_label.pack(pady=30)
    
    # Status text
    status_label = tk.Label(splash, text="Initializing modules...", 
                           font=("Arial", 10), 
                           bg="#1a1a1a", fg="#ffffff")
    status_label.pack(pady=10)
    
    # Version
    version_label = tk.Label(splash, text="v7.9.7-Julian-DynamicLLMRouter", 
                            font=("Arial", 8), 
                            bg="#1a1a1a", fg="#888888")
    version_label.pack(pady=5)
    
    # Progress bar
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(splash, variable=progress_var, 
                                   maximum=100, length=300, 
                                   mode='indeterminate')
    progress_bar.pack(pady=20)
    progress_bar.start()
    
    splash.update()
    
    def update_status(text):
        """Update splash status text"""
        if splash and splash.winfo_exists():
            status_label.config(text=text)
            splash.update()
    
    def close_splash():
        """Close splash screen"""
        try:
            if splash and splash.winfo_exists():
                time.sleep(0.5)  # Brief delay for smooth transition
                splash.destroy()
        except:
            pass
    
except Exception as e:
    log(f"Splash screen error (continuing): {e}", "WARNING")
    splash = None
    update_status = lambda x: None
    close_splash = lambda: None

def check_python_version():
    """Check Python version"""
    try:
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            log("Python version too old (need 3.8+)", "ERROR")
            return False
        log(f"Python {version.major}.{version.minor}.{version.micro} ✓", "INFO")
        return True
    except:
        return False

def check_dependencies():
    """Check and install missing dependencies"""
    required_packages = {
        "flask": "flask",
        "chromadb": "chromadb",
        "fastapi": "fastapi",
        "uvicorn": "uvicorn",
        "requests": "requests",
        "PIL": "pillow",
        "ttk": None  # ttk is part of tkinter
    }
    
    missing = []
    
    if splash:
        update_status("Checking dependencies...")
    
    for module_name, package_name in required_packages.items():
        if package_name is None:
            # Skip modules that don't need installation
            continue
        
        try:
            __import__(module_name)
            log(f"{module_name} ✓", "INFO")
        except ImportError:
            missing.append(package_name if package_name else module_name)
            log(f"{module_name} ✗ (missing)", "WARNING")
    
    if missing:
        if splash:
            update_status(f"Installing {len(missing)} missing packages...")
        log(f"Missing packages: {', '.join(missing)}", "INFO")
        
        try:
            # Install missing packages
            for package in missing:
                log(f"Installing {package}...", "INFO")
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--quiet", package],
                    capture_output=True,
                    timeout=120,
                    cwd=BASE_DIR
                )
                if result.returncode == 0:
                    log(f"{package} installed ✓", "INFO")
                else:
                    log(f"{package} installation failed: {result.stderr}", "ERROR")
                    return False
            
            log("All dependencies installed ✓", "INFO")
        except Exception as e:
            log(f"Error installing dependencies: {e}", "ERROR")
            return False
    
    return True

def check_tkinter():
    """Check tkinter availability"""
    try:
        import tkinter
        log("tkinter available ✓", "INFO")
        return True
    except ImportError:
        log("tkinter not available", "ERROR")
        return False

def verify_environment():
    """Verify environment setup"""
    if splash:
        update_status("Verifying environment...")
    
    # Check Python
    if not check_python_version():
        return False
    
    # Check tkinter
    if not check_tkinter():
        return False
    
    # Check dependencies
    if not check_dependencies():
        return False
    
    return True

def start_gui():
    """Start the main GUI application"""
    if splash:
        update_status("Starting Control Panel...")
    
    control_panel_path = os.path.join(BASE_DIR, "RAG_Control_Panel.py")
    
    if not os.path.exists(control_panel_path):
        log(f"Control Panel not found: {control_panel_path}", "ERROR")
        return False
    
    try:
        log("Launching RAG_Control_Panel.py", "INFO")
        
        # Start GUI in separate process
        process = subprocess.Popen(
            [sys.executable, control_panel_path],
            cwd=BASE_DIR,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        log(f"GUI process started (PID: {process.pid})", "INFO")
        
        # Wait a bit for GUI to initialize
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            log("GUI process running ✓", "INFO")
            
            # Wait a bit more for full initialization
            time.sleep(1)
            
            # Check API endpoints (optional, non-blocking)
            def check_apis():
                try:
                    import requests
                    time.sleep(3)  # Give APIs more time to start
                    
                    # Check RAG API
                    try:
                        response = requests.get("http://127.0.0.1:5000/health", timeout=2)
                        if response.status_code == 200:
                            log("RAG API responding ✓", "INFO")
                    except:
                        log("RAG API not responding (may start later)", "INFO")
                    
                    # Check CLO API
                    try:
                        response = requests.get("http://127.0.0.1:5001/health", timeout=2)
                        if response.status_code == 200:
                            log("CLO API responding ✓", "INFO")
                    except:
                        log("CLO API not responding (may start later)", "INFO")
                
                except ImportError:
                    pass  # requests not available, skip API check
            
            # Check APIs in background
            threading.Thread(target=check_apis, daemon=True).start()
            
            return True
        else:
            log(f"GUI process exited with code: {process.returncode}", "ERROR")
            return False
    
    except Exception as e:
        log(f"Error starting GUI: {e}", "ERROR")
        return False

def main():
    """Main launcher entry point"""
    try:
        # Verify environment
        if not verify_environment():
            if splash:
                update_status("Error: Environment check failed")
                time.sleep(2)
            log("Environment verification failed", "ERROR")
            close_splash()
            return False
        
        # Start GUI
        if splash:
            update_status("Launching Control Panel...")
        
        success = start_gui()
        
        if success:
            log("✅ Launch successful", "INFO")
            if splash:
                update_status("Launch successful!")
                time.sleep(0.5)
            close_splash()
            return True
        else:
            log("❌ Launch failed", "ERROR")
            
            # If GUI fails, try opening Troubleshooter
            if splash:
                update_status("GUI failed. Opening Troubleshooter...")
            
            try:
                troubleshooter_path = os.path.join(BASE_DIR, "modules", "smart_troubleshooter", "troubleshooter_core.py")
                if os.path.exists(troubleshooter_path):
                    subprocess.Popen([sys.executable, troubleshooter_path], 
                                   cwd=BASE_DIR,
                                   creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                    log("Troubleshooter opened as fallback", "INFO")
            except:
                pass
            
            time.sleep(2)
            close_splash()
            return False
    
    except Exception as e:
        log(f"Launcher error: {e}", "ERROR")
        if splash:
            update_status(f"Error: {str(e)[:30]}")
            time.sleep(2)
        close_splash()
        return False

if __name__ == "__main__":
    try:
        success = main()
        # Keep process alive briefly to allow GUI to start
        if success:
            time.sleep(3)
    except KeyboardInterrupt:
        log("Launcher interrupted by user", "INFO")
        close_splash()
    except Exception as e:
        log(f"Critical launcher error: {e}", "ERROR")
        close_splash()

