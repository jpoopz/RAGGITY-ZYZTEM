"""
Complete Tkinter Fix for Python 3.14 on Windows
Finds and configures Tcl/Tk libraries automatically
"""

import os
import sys
import subprocess
from pathlib import Path

def find_python_installation():
    """Find the actual Python installation directory"""
    python_exe = sys.executable
    python_dir = os.path.dirname(python_exe)
    
    # If it's a Windows Store Python, find the actual installation
    if "WindowsApps" in python_exe:
        # Try common installation locations
        possible_paths = [
            os.path.expanduser(r"C:\Users\Julian Poopat\AppData\Local\Programs\Python\Python314"),
            r"C:\Python314",
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Python", "Python314"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.path.exists(os.path.join(path, "python.exe")):
                return path
    
    return python_dir

def find_tcl_tk(python_dir):
    """Find Tcl and Tk directories"""
    tcl_path = None
    tk_path = None
    
    # Common locations to check
    search_paths = [
        os.path.join(python_dir, "tcl"),
        os.path.join(python_dir, "Lib", "tcl8.6"),
        os.path.join(python_dir, "DLLs"),
    ]
    
    # Search for init.tcl (indicates tcl installation)
    for search_path in search_paths:
        if not os.path.exists(search_path):
            continue
        
        # Look for init.tcl
        for root, dirs, files in os.walk(search_path):
            if "init.tcl" in files:
                tcl_dir = root
                # Find corresponding tk directory
                tcl_parent = os.path.dirname(tcl_dir)
                for tk_dir_name in os.listdir(tcl_parent):
                    tk_full = os.path.join(tcl_parent, tk_dir_name)
                    if tk_dir_name.startswith("tk") and os.path.isdir(tk_full):
                        if os.path.exists(os.path.join(tk_full, "tk.tcl")):
                            tk_path = tk_full
                            break
                if tk_path:
                    tcl_path = tcl_dir
                    break
        
        if tcl_path and tk_path:
            break
    
    return tcl_path, tk_path

def install_tcl_tk():
    """Attempt to install Tcl/Tk components"""
    print("Attempting to install Tcl/Tk support...")
    
    # Try pip install python-tk (if available)
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "python-tk"], 
                      check=False, capture_output=True)
    except:
        pass
    
    # Alternative: Try downloading from python.org or use ensurepip
    print("If pip install doesn't work, you may need to:")
    print("1. Reinstall Python from python.org")
    print("2. Ensure 'tcl/tk and IDLE' option is selected")
    print("3. Or download Tcl/Tk separately and place in Python\\tcl\\")

def fix_tkinter():
    """Main fix function"""
    print("=== Tkinter Fix Utility ===\n")
    
    # Find Python installation
    python_dir = find_python_installation()
    print(f"Python directory: {python_dir}")
    
    # Find Tcl/Tk
    tcl_path, tk_path = find_tcl_tk(python_dir)
    
    if tcl_path and tk_path:
        print(f"\n✓ Found Tcl: {tcl_path}")
        print(f"✓ Found Tk: {tk_path}")
        
        # Set environment variables
        os.environ["TCL_LIBRARY"] = tcl_path
        os.environ["TK_LIBRARY"] = tk_path
        
        # Also set as user environment variables (permanent)
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                               r"Environment", 0, 
                               winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "TCL_LIBRARY", 0, winreg.REG_EXPAND_SZ, tcl_path)
            winreg.SetValueEx(key, "TK_LIBRARY", 0, winreg.REG_EXPAND_SZ, tk_path)
            winreg.CloseKey(key)
            print("\n✓ Environment variables set permanently")
        except Exception as e:
            print(f"\n⚠ Could not set permanent env vars: {e}")
            print("Setting for current session only")
        
        # Test Tkinter
        print("\nTesting Tkinter...")
        try:
            import tkinter
            root = tkinter.Tk()
            root.withdraw()
            root.destroy()
            print("✓ Tkinter works!")
            return True
        except Exception as e:
            print(f"✗ Tkinter still fails: {e}")
            return False
    else:
        print("\n✗ Tcl/Tk not found in standard locations")
        print("\nAttempting installation...")
        install_tcl_tk()
        return False

if __name__ == "__main__":
    success = fix_tkinter()
    if success:
        print("\n✓ Fix complete! You can now run RAG_Control_Panel.py")
    else:
        print("\n✗ Automatic fix failed. Manual steps required:")
        print("  1. Verify Python installation includes Tcl/Tk")
        print("  2. Or reinstall Python with full components")
        sys.exit(1)




