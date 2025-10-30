"""
Prompt Router - Adaptive dual-prompt logic for CHAT and CLO_WIZARD modes
Manages system prompts, context assembly, and mode detection
"""

import os
import sys
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Literal

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
except ImportError:
    def log(msg, category="PROMPT_ROUTER"):
        print(f"[{category}] {msg}")

# System Prompts
CHAT_PROMPT = """You are Julian's creative design and research assistant.

Engage in open conversation, brainstorm garment ideas, combine academic reasoning,
and respond naturally. When user feedback includes actionable garment modifications
(e.g. color, fabric, fit, sleeve, logo), suggest entering CLO_WIZARD mode.

Output in conversational text only.
"""

CLO_WIZARD_PROMPT = """You are CLO WIZARD — a procedural garment-generation AI controlling Python tools:
garment_gen.py, garment_editor.py, and preview_manager.

Respond **only** in structured JSON commands.

Use the schema:
{
  "mode": "CLO_WIZARD",
  "commands": [
    {"action": "adjust_sleeve_length", "value": "+3cm"},
    {"action": "change_color", "value": "navy"}
  ]
}

Never output natural language.

You can query design_state.json for current values.

After command execution, the system will revert to CHAT mode automatically.
"""

class PromptRouter:
    """Routes prompts between CHAT and CLO_WIZARD modes"""
    
    def __init__(self):
        self.current_mode: Literal["CHAT", "CLO_WIZARD"] = "CHAT"
        self.log_file = os.path.join(BASE_DIR, "Logs", "clo_prompt_router.log")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        log("PromptRouter initialized", "PROMPT_ROUTER")
    
    def get_prompt(self, mode: Literal["CHAT", "CLO_WIZARD"]) -> str:
        """Get system prompt for specified mode"""
        if mode == "CLO_WIZARD":
            return CLO_WIZARD_PROMPT
        else:
            return CHAT_PROMPT
    
    def route_prompt(self, input_text: str, current_mode: str = None) -> Literal["CHAT", "CLO_WIZARD"]:
        """
        Detect if user input should trigger mode switch using intent classifier
        
        Returns:
            "CLO_WIZARD" if EDIT intent detected
            "CHAT" otherwise
        """
        try:
            from modules.clo_companion.intent_classifier import get_intent_classifier
            
            classifier = get_intent_classifier()
            intent, confidence = classifier.detect_intent(input_text)
            
            # Convert intent to mode
            if intent == "EDIT":
                detected_mode = "CLO_WIZARD"
            else:
                detected_mode = "CHAT"
            
            # Log routing decision
            self.log_router_action("auto_route", f"{current_mode or 'CHAT'} → {detected_mode}", input_text)
            
            return detected_mode
            
        except ImportError:
            # Fallback to old pattern matching if classifier unavailable
            if current_mode is None:
                current_mode = self.current_mode
            
            input_lower = input_text.lower().strip()
            
            # Mode switch triggers (actionable design commands)
            wizard_triggers = [
                r"make (sleeve|sleeves)",
                r"adjust (sleeve|hem|length|width|fit)",
                r"change (color|colour|material|fabric)",
                r"shorten|longer|wider|narrower",
                r"make it (fitted|oversized|tighter|looser)",
                r"add (logo|belt|hood)",
                r"remove (logo|belt)",
                r"resize (logo|sleeve)",
                r"v\d+|version \d+",
                r"undo|revert",
                r"edit|modify|update"
            ]
            
            # Check for wizard triggers
            for pattern in wizard_triggers:
                if re.search(pattern, input_lower):
                    self.log_router_action("mode_switch", "CHAT → CLO_WIZARD", input_text)
                    return "CLO_WIZARD"
            
            # Default: CHAT
            return "CHAT"
    
    def build_context(self, mode: str, design_state: Optional[Dict] = None, 
                     chat_history: Optional[List[Dict]] = None) -> str:
        """
        Assemble trimmed context for LLM
        
        Args:
            mode: Current mode (CHAT or CLO_WIZARD)
            design_state: Current design state dict
            chat_history: List of recent chat messages
        
        Returns:
            Formatted context string
        """
        context_parts = []
        
        # Add design context (essential keys only)
        if design_state:
            design_context = self._extract_design_context(design_state)
            if design_context:
                context_parts.append(f"Current Design:\n{design_context}")
        
        # Add last 6 messages from chat history
        if chat_history:
            recent_messages = chat_history[-6:] if len(chat_history) > 6 else chat_history
            messages_str = "\n".join([
                f"{msg.get('role', 'unknown')}: {msg.get('message', '')}"
                for msg in recent_messages
            ])
            if messages_str:
                context_parts.append(f"Recent Conversation:\n{messages_str}")
        
        # Combine
        context = "\n\n".join(context_parts)
        
        self.log_router_action("context_built", f"mode={mode}, parts={len(context_parts)}", "")
        
        return context
    
    def _extract_design_context(self, design_state: Dict) -> str:
        """Extract essential design keys for context"""
        essential_keys = ["current_file", "version", "attributes", "last_prompt"]
        
        context_items = []
        
        # File info
        if design_state.get("current_file"):
            filename = os.path.basename(design_state["current_file"])
            version = design_state.get("version", 1)
            context_items.append(f"File: {filename} (v{version})")
        
        # Attributes (color, fabric, fit, etc.)
        attributes = design_state.get("attributes", {})
        if attributes:
            attr_str = ", ".join([f"{k}: {v}" for k, v in attributes.items() if k in ["color", "material", "fit", "garment_type", "sleeve_length"]])
            if attr_str:
                context_items.append(f"Attributes: {attr_str}")
        
        # Last prompt
        last_prompt = design_state.get("last_prompt", "")
        if last_prompt:
            context_items.append(f"Original prompt: {last_prompt}")
        
        return "\n".join(context_items) if context_items else ""
    
    def attach_tools(self, mode: Literal["CHAT", "CLO_WIZARD"]) -> Dict:
        """
        Bind correct toolset to mode
        
        Returns:
            Dict with tool definitions and configurations
        """
        if mode == "CLO_WIZARD":
            tools = {
                "garment_gen": {
                    "description": "Generate new garment from prompt",
                    "function": "generate_garment",
                    "params": ["prompt", "seed"]
                },
                "garment_editor": {
                    "description": "Edit existing garment OBJ file",
                    "function": "apply_edit",
                    "params": ["model_path", "edit_commands"]
                },
                "preview_manager": {
                    "description": "Generate preview images",
                    "function": "generate_preview",
                    "params": ["obj_file", "output_path"]
                },
                "design_state": {
                    "description": "Query current design state",
                    "function": "get_current_state",
                    "params": []
                }
            }
            self.log_router_action("tools_attached", f"CLO_WIZARD ({len(tools)} tools)", "")
            return tools
        else:
            # CHAT mode - no tools, conversational only
            self.log_router_action("tools_attached", "CHAT (no tools)", "")
            return {}
    
    def set_mode(self, mode: Literal["CHAT", "CLO_WIZARD"]):
        """Set current mode and log transition"""
        if mode != self.current_mode:
            old_mode = self.current_mode
            self.current_mode = mode
            self.log_router_action("mode_set", f"{old_mode} → {mode}", "")
            log(f"[MODE] Switched: {old_mode} → {mode}", "PROMPT_ROUTER")
    
    def get_mode(self) -> Literal["CHAT", "CLO_WIZARD"]:
        """Get current mode"""
        return self.current_mode
    
    def log_router_action(self, action: str, details: str, input_text: str = ""):
        """Log router actions to dedicated log file"""
        try:
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            log_entry = f"[{timestamp}] [{action}] {details}"
            if input_text:
                log_entry += f" | Input: {input_text[:100]}"
            log_entry += "\n"
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            # Don't fail if logging fails
            pass

# Global instance
_prompt_router_instance = None

def get_prompt_router() -> PromptRouter:
    """Get global prompt router instance (singleton)"""
    global _prompt_router_instance
    if _prompt_router_instance is None:
        _prompt_router_instance = PromptRouter()
    return _prompt_router_instance

