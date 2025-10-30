"""
Create Desktop Shortcut for Julian Assistant Suite
Programmatic shortcut creation with proper paths and icon
"""

import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Try using win32com (preferred)
try:
    from win32com.client import Dispatch
    
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    shortcut_path = os.path.join(desktop, "Julian Assistant Suite.lnk")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(BASE_DIR, "LAUNCH_GUI.bat")
    icon = os.path.join(BASE_DIR, "assets", "julian_assistant.ico")
    
    # Ensure icon exists
    icon_index = 3  # Default folder icon index
    if not os.path.exists(icon):
        icon_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32", "SHELL32.dll")
        icon = f"{icon_path},{icon_index}"
    
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(shortcut_path)
    
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = BASE_DIR
    shortcut.IconLocation = icon if os.path.exists(icon) else f"{icon},{icon_index}"
    shortcut.Description = "Launch the Julian Assistant Suite Control Panel v7.9.7"
    
    shortcut.save()
    
    print(f"✅ Desktop shortcut created successfully: {shortcut_path}")
    print(f"   Target: {target}")
    print(f"   Icon: {icon}")
    
except ImportError:
    # Fallback to PowerShell method
    print("win32com not available, using PowerShell method...")
    import subprocess
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    shortcut_path = os.path.join(desktop, "Julian Assistant Suite.lnk")
    target = os.path.join(BASE_DIR, "LAUNCH_GUI.bat")
    icon = os.path.join(BASE_DIR, "assets", "julian_assistant.ico")
    
    ps_script = f'''
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{target}"
$Shortcut.WorkingDirectory = "{BASE_DIR}"
$Shortcut.IconLocation = "{icon if os.path.exists(icon) else os.path.join(os.environ.get('SystemRoot', 'C:\\\\Windows'), 'System32', 'SHELL32.dll')}"
$Shortcut.Description = "Launch the Julian Assistant Suite Control Panel v7.9.7"
$Shortcut.Save()
'''
    
    try:
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print(f"✅ Desktop shortcut created successfully: {shortcut_path}")
        else:
            print(f"❌ Failed to create shortcut: {result.stderr}")
    except Exception as e:
        print(f"❌ Error creating shortcut: {e}")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

