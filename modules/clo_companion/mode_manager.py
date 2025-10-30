"""
Mode Manager - Tracks and manages CHAT/CLO_WIZARD mode transitions
"""

import os
import sys
from typing import Literal

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
    from modules.clo_companion.prompt_router import get_prompt_router, PromptRouter
except ImportError:
    def log(msg, category="MODE"):
        print(f"[{category}] {msg}")
    PromptRouter = None
    def get_prompt_router():
        return None

class ModeManager:
    """Manages mode transitions between CHAT and CLO_WIZARD"""
    
    def __init__(self):
        self.current_mode: Literal["CHAT", "CLO_WIZARD"] = "CHAT"
        self.prompt_router: Optional[PromptRouter] = get_prompt_router()
        
        log("ModeManager initialized", "MODE")
    
    def set_mode(self, mode: Literal["CHAT", "CLO_WIZARD"], reason: str = ""):
        """
        Set current mode and update prompt router
        
        Args:
            mode: Target mode ("CHAT" or "CLO_WIZARD")
            reason: Optional reason for mode switch
        """
        if mode not in ["CHAT", "CLO_WIZARD"]:
            log(f"Invalid mode: {mode}", "MODE", level="ERROR")
            return
        
        old_mode = self.current_mode
        
        if mode != old_mode:
            self.current_mode = mode
            
            # Update prompt router
            if self.prompt_router:
                self.prompt_router.set_mode(mode)
                current_prompt = self.prompt_router.get_prompt(mode)
                tools = self.prompt_router.attach_tools(mode)
                
                log(f"[MODE] Entered {mode}" + (f" ({reason})" if reason else ""), "MODE")
                
                if mode == "CLO_WIZARD":
                    log(f"[MODE] Loaded CLO_WIZARD prompt ({len(current_prompt)} chars)", "MODE", print_to_console=False)
                    log(f"[MODE] Attached {len(tools)} tools", "MODE", print_to_console=False)
                else:
                    log(f"[MODE] Returned to CHAT", "MODE")
                    log(f"[MODE] Loaded CHAT prompt ({len(current_prompt)} chars)", "MODE", print_to_console=False)
            else:
                log(f"[MODE] Switched to {mode} (prompt router unavailable)", "MODE", level="WARNING")
    
    def get_mode(self) -> Literal["CHAT", "CLO_WIZARD"]:
        """Get current mode"""
        return self.current_mode
    
    def get_current_prompt(self) -> str:
        """Get current system prompt"""
        if self.prompt_router:
            return self.prompt_router.get_prompt(self.current_mode)
        return ""
    
    def detect_mode_from_input(self, input_text: str) -> Literal["CHAT", "CLO_WIZARD"]:
        """Detect appropriate mode from user input"""
        if self.prompt_router:
            detected = self.prompt_router.route_prompt(input_text, self.current_mode)
            if detected != self.current_mode:
                self.set_mode(detected, f"Auto-detected from input: {input_text[:50]}")
            return detected
        return self.current_mode
    
    def return_to_chat(self, reason: str = ""):
        """Explicitly return to CHAT mode"""
        if self.current_mode != "CHAT":
            self.set_mode("CHAT", reason or "Auto-return after command execution")

# Global instance
_mode_manager_instance = None

def get_mode_manager() -> ModeManager:
    """Get global mode manager instance (singleton)"""
    global _mode_manager_instance
    if _mode_manager_instance is None:
        _mode_manager_instance = ModeManager()
    return _mode_manager_instance




