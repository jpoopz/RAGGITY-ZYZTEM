"""
Auto Fixer - Safe fix executor (pip installs, cache clears, service restarts)
"""

import os
import sys
import subprocess
import shutil
from typing import Dict, Optional, Tuple

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
except ImportError:
    def log(msg, category="TROUBLE"):
        print(f"[{category}] {msg}")

# Import cloud bridge for telemetry
try:
    from core.cloud_bridge import bridge
    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False

class AutoFixer:
    """Safely executes automatic fixes"""
    
    # Safe operations that can be auto-fixed
    SAFE_OPERATIONS = ["pip_install", "clear_cache", "restart_service"]
    
    def __init__(self):
        self.backup_dir = os.path.join(BASE_DIR, "backups", "troubleshooter")
        os.makedirs(self.backup_dir, exist_ok=True)
        
        log("AutoFixer initialized", "TROUBLE")
    
    def apply_fix(self, issue: Dict, fix: Dict) -> Tuple[bool, str]:
        """
        Apply a fix safely
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not fix.get("safe", False):
            return (False, "Fix is not marked as safe for auto-execution")
        
        fix_type = fix.get("fix_type", "")
        
        if fix_type not in self.SAFE_OPERATIONS:
            return (False, f"Fix type '{fix_type}' is not in safe operations list")
        
        try:
            if fix_type == "pip_install":
                return self._pip_install(fix)
            elif fix_type == "clear_cache":
                return self._clear_cache(issue)
            elif fix_type == "restart_service":
                return self._restart_service(issue)
            else:
                return (False, f"Unknown fix type: {fix_type}")
        
        except Exception as e:
            log(f"Error applying fix: {e}", "TROUBLE", level="ERROR")
            return (False, f"Error: {e}")
    
    def _pip_install(self, fix: Dict) -> Tuple[bool, str]:
        """Install Python package via pip"""
        command = fix.get("command")
        if not command:
            return (False, "No install command specified")
        
        try:
            # Backup current environment state
            self._backup_environment()
            
            # Run pip install
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                log(f"Successfully installed: {command}", "TROUBLE")
                
                # Send telemetry event
                if BRIDGE_AVAILABLE:
                    try:
                        bridge.send_event("auto_fix", {
                            "issue": issue.get("type", "unknown"),
                            "fix": "pip_install",
                            "command": command,
                            "success": True
                        })
                    except Exception as e:
                        log(f"Failed to send auto_fix event: {e}", "TROUBLE")
                
                return (True, f"Successfully installed package: {command}")
            else:
                error_msg = result.stderr or result.stdout
                return (False, f"Installation failed: {error_msg}")
        
        except subprocess.TimeoutExpired:
            return (False, "Installation timed out")
        except Exception as e:
            return (False, f"Error: {e}")
    
    def _clear_cache(self, issue: Dict) -> Tuple[bool, str]:
        """Clear cache (with backup)"""
        try:
            # Backup cache directories
            cache_dirs = [
                os.path.join(BASE_DIR, ".chromadb"),
                os.path.join(BASE_DIR, "__pycache__"),
                os.path.join(BASE_DIR, ".pytest_cache")
            ]
            
            cleared = []
            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    # Create backup
                    backup_path = os.path.join(self.backup_dir, os.path.basename(cache_dir) + "_backup")
                    if os.path.exists(backup_path):
                        shutil.rmtree(backup_path)
                    shutil.copytree(cache_dir, backup_path)
                    
                    # Clear cache
                    shutil.rmtree(cache_dir)
                    cleared.append(os.path.basename(cache_dir))
            
            if cleared:
                log(f"Cleared caches: {', '.join(cleared)}", "TROUBLE")
                
                # Send telemetry event
                if BRIDGE_AVAILABLE:
                    try:
                        bridge.send_event("auto_fix", {
                            "issue": issue.get("type", "unknown"),
                            "fix": "clear_cache",
                            "cleared": cleared,
                            "success": True
                        })
                    except Exception as e:
                        log(f"Failed to send auto_fix event: {e}", "TROUBLE")
                
                return (True, f"Cleared caches: {', '.join(cleared)}")
            else:
                return (False, "No cache directories found to clear")
        
        except Exception as e:
            return (False, f"Error clearing cache: {e}")
    
    def _restart_service(self, issue: Dict) -> Tuple[bool, str]:
        """Restart service (non-destructive)"""
        # This is handled by the API server restart logic
        # AutoFixer doesn't kill processes, only suggests
        return (False, "Service restart requires manual intervention for safety")
    
    def _backup_environment(self):
        """Backup environment state before fixes"""
        try:
            import json
            from datetime import datetime
            
            env_state = {
                "timestamp": datetime.now().isoformat(),
                "python_version": sys.version,
                "path": sys.path
            }
            
            backup_file = os.path.join(self.backup_dir, f"env_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(env_state, f, indent=2)
        
        except Exception as e:
            log(f"Error backing up environment: {e}", "TROUBLE", level="WARNING")




