"""
Cursor Bridge Connector - Automated self-repair via Cursor
Listens for troubleshooter events and forwards to Cursor for automated fixes
"""

import os
import sys
import json
import subprocess
import time
import threading
from typing import Dict, Optional, List
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
    from core.event_bus import get_event_bus, publish_event
except ImportError:
    def log(msg, category="CURSOR_BRIDGE"):
        print(f"[{category}] {msg}")
    def publish_event(event_type, sender, data=None):
        pass

class CursorBridge:
    """Bridges troubleshooter events to Cursor for automated fixes"""
    
    def __init__(self):
        self.config_file = os.path.join(BASE_DIR, "config", "cursor_bridge.json")
        self.prompts_file = os.path.join(BASE_DIR, "auto_prompts.json")
        self.log_file = os.path.join(BASE_DIR, "Logs", "auto_fix.log")
        
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
        
        self.config = self._load_config()
        self.running = False
        self.listen_thread = None
        
        # Subscribe to event bus
        try:
            event_bus = get_event_bus()
            event_bus.subscribe("trouble.alert", self._on_trouble_alert)
            event_bus.subscribe("module.fail", self._on_module_fail)
        except:
            pass
        
        log("CursorBridge initialized", "CURSOR_BRIDGE")
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON"""
        default_config = {
            "auto_mode": True,
            "ask_before_fix": True,
            "cursor_cli_path": "C:/Users/Julian Poopat/AppData/Local/Programs/Cursor/resources/app/bin/cursor.exe",
            "retry_count": 3,
            "retry_delay": 30,
            "enabled": True
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            log(f"Error loading config: {e}", "CURSOR_BRIDGE", level="WARNING")
        
        # Save default config if missing
        if not os.path.exists(self.config_file):
            self._save_config(default_config)
        
        return default_config
    
    def _save_config(self, config: Dict):
        """Save configuration to JSON"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log(f"Error saving config: {e}", "CURSOR_BRIDGE", level="ERROR")
    
    def start_listening(self):
        """Start listening for events"""
        if self.running:
            return
        
        if not self.config.get("enabled", True):
            log("Cursor Bridge is disabled in config", "CURSOR_BRIDGE")
            return
        
        self.running = True
        self.listen_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listen_thread.start()
        log("Cursor Bridge listening started", "CURSOR_BRIDGE")
    
    def stop_listening(self):
        """Stop listening for events"""
        self.running = False
        if self.listen_thread:
            self.listen_thread.join(timeout=5)
        log("Cursor Bridge listening stopped", "CURSOR_BRIDGE")
    
    def _listen_loop(self):
        """Main listening loop"""
        while self.running:
            try:
                # Check for prompts file changes
                self._check_prompt_file()
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                log(f"Error in listen loop: {e}", "CURSOR_BRIDGE", level="ERROR")
                time.sleep(10)
    
    def _on_trouble_alert(self, event):
        """Handle trouble.alert event"""
        try:
            if not self.config.get("auto_mode", True):
                return
            
            issue = event.get("data", {}).get("issue", {})
            fix = event.get("data", {}).get("fix", {})
            
            # Only auto-fix safe operations if enabled
            if fix.get("safe", False) and not self.config.get("ask_before_fix", True):
                self._apply_safe_fix(issue, fix)
            else:
                # Generate Cursor prompt
                prompt = self._generate_cursor_prompt(issue, fix)
                self._send_to_cursor(prompt, issue)
        
        except Exception as e:
            log(f"Error handling trouble alert: {e}", "CURSOR_BRIDGE", level="ERROR")
    
    def _on_module_fail(self, event):
        """Handle module.fail event"""
        try:
            if not self.config.get("auto_mode", True):
                return
            
            module_data = event.get("data", {})
            prompt = self._generate_module_fix_prompt(module_data)
            self._send_to_cursor(prompt, module_data)
        
        except Exception as e:
            log(f"Error handling module fail: {e}", "CURSOR_BRIDGE", level="ERROR")
    
    def _apply_safe_fix(self, issue: Dict, fix: Dict):
        """Apply safe fixes automatically"""
        try:
            from modules.smart_troubleshooter.auto_fixer import AutoFixer
            
            fixer = AutoFixer()
            success, message = fixer.apply_fix(issue, fix)
            
            self._log_result("AUTO_FIX", {
                "issue": issue.get("type", "unknown"),
                "fix": fix.get("fix_type", "unknown"),
                "success": success,
                "message": message
            })
            
            if success:
                publish_event("trouble.fixed", "cursor_bridge", {
                    "issue": issue,
                    "fix": fix,
                    "method": "auto_fix"
                })
        
        except Exception as e:
            log(f"Error applying safe fix: {e}", "CURSOR_BRIDGE", level="ERROR")
    
    def _generate_cursor_prompt(self, issue: Dict, fix: Optional[Dict] = None) -> str:
        """Generate Cursor prompt from issue"""
        try:
            from modules.smart_troubleshooter.prompt_generator import PromptGenerator
            
            generator = PromptGenerator()
            return generator.generate_cursor_prompt(issue, fix)
        
        except Exception as e:
            log(f"Error generating prompt: {e}", "CURSOR_BRIDGE", level="ERROR")
            return f"Fix issue: {issue.get('message', 'Unknown issue')}"
    
    def _generate_module_fix_prompt(self, module_data: Dict) -> str:
        """Generate prompt for module failure"""
        module_name = module_data.get("module", "unknown")
        error = module_data.get("error", "Unknown error")
        
        prompt = f"""# Module Fix Request - Julian Assistant Suite

**Module:** {module_name}
**Error:** {error}
**Timestamp:** {datetime.now().isoformat()}

Please review and fix the module failure.
"""
        return prompt
    
    def read_prompt(self) -> Optional[str]:
        """Read latest prompt from auto_prompts.json"""
        try:
            if os.path.exists(self.prompts_file):
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Get most recent prompt
                    if isinstance(data, list) and len(data) > 0:
                        return data[-1].get("prompt", "")
                    elif isinstance(data, dict):
                        return data.get("latest_prompt", "")
            
            return None
        
        except Exception as e:
            log(f"Error reading prompt: {e}", "CURSOR_BRIDGE", level="ERROR")
            return None
    
    def _send_to_cursor(self, prompt: str, context: Dict):
        """Send prompt to Cursor via CLI or API"""
        if not prompt:
            return
        
        # Save prompt to file for Cursor to read
        try:
            prompts_data = []
            if os.path.exists(self.prompts_file):
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    prompts_data = json.load(f)
                    if not isinstance(prompts_data, list):
                        prompts_data = []
            
            prompts_data.append({
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt,
                "context": context,
                "status": "pending"
            })
            
            # Keep only last 50 prompts
            prompts_data = prompts_data[-50:]
            
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(prompts_data, f, indent=2, ensure_ascii=False)
            
            log(f"Prompt saved to {self.prompts_file}", "CURSOR_BRIDGE")
            
            # Try to open in Cursor if CLI path is configured
            cursor_path = self.config.get("cursor_cli_path")
            if cursor_path and os.path.exists(cursor_path):
                try:
                    # Open Cursor with the prompts file
                    subprocess.Popen([cursor_path, self.prompts_file], 
                                   creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
                    log("Cursor opened with prompt file", "CURSOR_BRIDGE")
                except Exception as e:
                    log(f"Error opening Cursor: {e}", "CURSOR_BRIDGE", level="WARNING")
            
            # Retry mechanism
            if self.config.get("retry_count", 3) > 0:
                threading.Thread(target=self._retry_send, args=(prompt, context), daemon=True).start()
        
        except Exception as e:
            log(f"Error sending to Cursor: {e}", "CURSOR_BRIDGE", level="ERROR")
    
    def _retry_send(self, prompt: str, context: Dict):
        """Retry sending prompt with delay"""
        retry_count = self.config.get("retry_count", 3)
        retry_delay = self.config.get("retry_delay", 30)
        
        for attempt in range(retry_count):
            time.sleep(retry_delay)
            
            # Check if prompt was processed (status changed)
            try:
                if os.path.exists(self.prompts_file):
                    with open(self.prompts_file, 'r', encoding='utf-8') as f:
                        prompts_data = json.load(f)
                        if isinstance(prompts_data, list):
                            latest = prompts_data[-1] if prompts_data else {}
                            if latest.get("status") != "pending":
                                log(f"Prompt processed after {attempt + 1} retries", "CURSOR_BRIDGE")
                                return
            except:
                pass
            
            log(f"Retry {attempt + 1}/{retry_count} - waiting for Cursor response", "CURSOR_BRIDGE", print_to_console=False)
    
    def _check_prompt_file(self):
        """Check for updated prompts and process results"""
        try:
            if not os.path.exists(self.prompts_file):
                return
            
            with open(self.prompts_file, 'r', encoding='utf-8') as f:
                prompts_data = json.load(f)
            
            if not isinstance(prompts_data, list):
                return
            
            # Check for completed prompts
            for prompt_entry in prompts_data:
                if prompt_entry.get("status") == "completed" and not prompt_entry.get("logged", False):
                    self._log_result("CURSOR_FIX", {
                        "prompt": prompt_entry.get("prompt", "")[:100],
                        "result": prompt_entry.get("result", "unknown"),
                        "timestamp": prompt_entry.get("timestamp")
                    })
                    prompt_entry["logged"] = True
            
            # Save updated data
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(prompts_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            log(f"Error checking prompt file: {e}", "CURSOR_BRIDGE", level="WARNING")
    
    def _log_result(self, action_type: str, data: Dict):
        """Log action result to auto_fix.log"""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "action": action_type,
                "data": data
            }
            
            log_line = f"[{timestamp}] [{action_type}] {json.dumps(data, ensure_ascii=False)}\n"
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_line)
            
            log(f"Logged {action_type}: {data.get('issue', data.get('prompt', 'action'))[:50]}", "CURSOR_BRIDGE", print_to_console=False)
        
        except Exception as e:
            log(f"Error logging result: {e}", "CURSOR_BRIDGE", level="ERROR")

# Global instance
_cursor_bridge_instance = None

def get_cursor_bridge() -> CursorBridge:
    """Get global Cursor Bridge instance"""
    global _cursor_bridge_instance
    if _cursor_bridge_instance is None:
        _cursor_bridge_instance = CursorBridge()
    return _cursor_bridge_instance




