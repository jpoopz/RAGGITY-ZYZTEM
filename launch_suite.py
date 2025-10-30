"""
Julian Assistant Suite Launcher with Splash Screen
Professional startup experience with automatic Python detection
Version: 7.9.7-Julian-DynamicLLMRouter
"""

import os
import sys
import subprocess
import time
import logging
import threading
from pathlib import Path

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

LOG_DIR = os.path.join(BASE_DIR, "Logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, "launcher.log")

# Setup logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='[%(asctime)s] %(message)s',
    encoding='utf-8'
)

logging.info("===== Julian Assistant Suite Launcher Started =====")

def find_python():
    """Find Python interpreter (pythonw.exe preferred)"""
    candidates = [
        sys.executable,
        r"C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python312\pythonw.exe",
        r"C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python312\python.exe",
        r"C:\Python314\pythonw.exe",
        r"C:\Python314\python.exe",
        r"C:\Program Files\Python312\pythonw.exe",
        r"C:\Program Files\Python312\python.exe",
    ]
    
    # Try candidates first
    for p in candidates:
        if os.path.exists(p):
            logging.info(f"Python found: {p}")
            return p
    
    # Try PATH
    try:
        result = subprocess.run(["where", "pythonw.exe"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0 and result.stdout.strip():
            path = result.stdout.strip().split('\n')[0]
            if os.path.exists(path):
                logging.info(f"Python found via PATH: {path}")
                return path
    except:
        pass
    
    try:
        result = subprocess.run(["where", "python.exe"], capture_output=True, text=True, timeout=2)
        if result.returncode == 0 and result.stdout.strip():
            path = result.stdout.strip().split('\n')[0]
            if os.path.exists(path):
                logging.info(f"Python found via PATH: {path}")
                return path
    except:
        pass
    
    logging.error("Python not found.")
    return None

def show_splash():
    """Show professional splash screen"""
    try:
        splash = None
        
        # Try to create splash window
        try:
            import tkinter as tk
            from tkinter import ttk
            
            splash = tk.Tk()
            splash.overrideredirect(True)  # No title bar
            
            # Center on screen
            width, height = 450, 220
            screen_width = splash.winfo_screenwidth()
            screen_height = splash.winfo_screenheight()
            x = (screen_width - width) // 2
            y = (screen_height - height) // 2
            splash.geometry(f"{width}x{height}+{x}+{y}")
            
            splash.configure(bg="#101010")
            splash.wm_attributes("-topmost", True)
            
            # Title
            title_lbl = tk.Label(
                splash,
                text="Julian Assistant Suite",
                fg="white",
                bg="#101010",
                font=("Segoe UI", 20, "bold")
            )
            title_lbl.pack(pady=40)
            
            # Subtitle
            sub_lbl = tk.Label(
                splash,
                text="Launching Control Panel...",
                fg="#AAAAAA",
                bg="#101010",
                font=("Segoe UI", 11)
            )
            sub_lbl.pack(pady=10)
            
            # Progress indicator
            progress_lbl = tk.Label(
                splash,
                text="⏳ Initializing...",
                fg="#55FF88",
                bg="#101010",
                font=("Consolas", 10)
            )
            progress_lbl.pack(pady=10)
            
            # Pulsing animation
            dots = [".", "..", "...", "...."]
            stop_pulse = threading.Event()
            
            def pulse():
                i = 0
                while not stop_pulse.is_set():
                    try:
                        progress_lbl.config(text="⏳ Initializing" + dots[i % len(dots)])
                        splash.update_idletasks()
                        time.sleep(0.5)
                        i += 1
                    except:
                        break
            
            pulse_thread = threading.Thread(target=pulse, daemon=True)
            pulse_thread.start()
            
            # Auto-close after 3 seconds minimum
            def close_splash():
                stop_pulse.set()
                time.sleep(0.3)
                try:
                    if splash.winfo_exists():
                        splash.destroy()
                except:
                    pass
            
            splash.after(3000, close_splash)
            
            splash.update()
            splash.mainloop()
            
        except ImportError:
            logging.warning("tkinter not available, skipping splash screen")
        except Exception as e:
            logging.warning(f"Splash screen error: {e}")
    
    except Exception as e:
        logging.warning(f"Could not show splash: {e}")

def show_error_popup(msg):
    """Show error popup window with message"""
    try:
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # Hide main window
        
        messagebox.showerror(
            "Julian Assistant Suite Error",
            f"Launch failed.\n\nDetails:\n{msg}\n\n"
            f"Check Logs/launcher_error.log for full traceback."
        )
        
        root.destroy()
    except Exception as e:
        logging.error(f"Could not show error popup: {e}")
        # Last resort: print to console if available
        print(f"ERROR: {msg}")

def main():
    """Main launcher entry point"""
    try:
        # Resolve overlapping instances before launch
        logging.info("Checking for overlapping instances...")
        try:
            sys.path.insert(0, BASE_DIR)
            from core.overlap_resolver import resolve_overlaps, verify_system_ready
            
            # Resolve overlaps (skip Control Panel for graceful restart scenario)
            results = resolve_overlaps(skip_control_panel=False)
            
            if results.get("terminated"):
                logging.info(f"Terminated {len(results['terminated'])} duplicate processes")
            
            # Verify system is ready
            is_ready, warnings = verify_system_ready()
            if not is_ready and warnings:
                logging.warning(f"System warnings: {warnings}")
                # Continue anyway - user may want to resolve manually
        except Exception as overlap_error:
            logging.warning(f"Overlap resolution failed (continuing): {overlap_error}")
        
        # Find Python
        python_path = find_python()
        if not python_path:
            logging.error("Python not found - cannot launch")
            # Show error message
            try:
                import tkinter.messagebox as messagebox
                messagebox.showerror("Python Not Found", "Python interpreter not found.\n\nPlease install Python 3.8 or later.")
            except:
                pass
            sys.exit(1)
        
        # Target script
        target = os.path.join(BASE_DIR, "RAG_Control_Panel.py")
        if not os.path.exists(target):
            logging.error(f"Control Panel not found: {target}")
            # Try to show error message (optional)
            try:
                import tkinter.messagebox as messagebox
                messagebox.showerror("Control Panel Not Found", f"Control Panel script not found:\n{target}")
            except:
                print(f"ERROR: Control Panel not found: {target}")
            sys.exit(1)
        
        # Show splash screen
        logging.info("Showing splash screen...")
        splash_thread = threading.Thread(target=show_splash, daemon=True)
        splash_thread.start()
        
        # Give splash time to appear
        time.sleep(1.5)
        
        # Launch Control Panel
        cmd = [python_path, target]
        logging.info(f"Running command: {' '.join(cmd)}")
        
        # Use Popen to launch GUI with capture for error detection
        process = subprocess.Popen(
            cmd,
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        )
        
        logging.info(f"GUI process started (PID: {process.pid})")
        
        # Wait a bit for GUI to initialize
        time.sleep(4)
        
        # Check if process exited with error
        retcode = process.poll()
        if retcode is not None and retcode != 0:
            # Process exited with error - capture output
            logging.error(f"GUI exited with code {retcode}")
            
            try:
                # Try to get output if available
                out, err = process.communicate(timeout=2)
                error_output = (out or "") + "\n" + (err or "")
            except:
                error_output = f"Process exited with code {retcode}\nUnable to capture output."
            
            # Write error log
            error_log_path = os.path.join(LOG_DIR, "launcher_error.log")
            with open(error_log_path, "w", encoding="utf-8") as f:
                f.write(f"=== Julian Assistant Suite Launcher Error ===\n")
                f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Exit Code: {retcode}\n")
                f.write(f"Command: {' '.join(cmd)}\n")
                f.write(f"Working Directory: {BASE_DIR}\n")
                f.write(f"\n=== STDOUT ===\n{out or '(empty)'}\n")
                f.write(f"\n=== STDERR ===\n{err or '(empty)'}\n")
                f.write(f"\n=== ERROR OUTPUT ===\n{error_output}\n")
            
            logging.error(f"Error log written to {error_log_path}")
            
            # Try re-running with visible console (python.exe instead of pythonw.exe)
            visible_python = python_path
            if "pythonw.exe" in python_path.lower():
                visible_python = python_path.replace("pythonw.exe", "python.exe")
                # If replacement file doesn't exist, try alternatives
                if not os.path.exists(visible_python):
                    # Try finding python.exe in same directory
                    python_dir = os.path.dirname(python_path)
                    visible_python = os.path.join(python_dir, "python.exe")
                    if not os.path.exists(visible_python):
                        visible_python = "python.exe"  # Fallback to PATH
            
            # Re-launch visibly
            cmd_visible = [visible_python, target]
            logging.info(f"Re-launching with visible console: {' '.join(cmd_visible)}")
            
            try:
                subprocess.Popen(
                    cmd_visible,
                    cwd=BASE_DIR
                )
                logging.info("Re-launch attempt started with visible console")
                
                # Show error popup after a delay
                time.sleep(1)
                show_error_popup(
                    f"The Control Panel failed to launch (exit code {retcode}).\n\n"
                    f"A new window was opened to show the error.\n\n"
                    f"Full error details saved to:\n{error_log_path}"
                )
            except Exception as re_launch_error:
                logging.error(f"Failed to re-launch visibly: {re_launch_error}")
                show_error_popup(
                    f"The Control Panel failed to launch (exit code {retcode}).\n\n"
                    f"Could not open error console automatically.\n\n"
                    f"Full error details saved to:\n{error_log_path}\n\n"
                    f"Please check the log file for details."
                )
        
        elif retcode is None:
            # Process is still running - success!
            logging.info("GUI launch appears successful - process running")
        else:
            # Process exited with code 0 (normal exit)
            logging.info("GUI process exited normally")
        
        # Give splash time to close naturally
        time.sleep(1)
        
    except Exception as e:
        logging.error(f"Launcher error: {e}")
        import traceback
        logging.error(traceback.format_exc())
        # Try to show error (optional)
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror("Launch Error", f"Failed to launch Control Panel:\n{e}")
        except:
            print(f"ERROR: Failed to launch Control Panel: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

