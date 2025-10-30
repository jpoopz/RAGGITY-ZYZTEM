"""
Design State Tracker - Maintains current design state and history
Manages design_state.json and chat history
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
except ImportError:
    def log(msg, category="CLO"):
        print(f"[{category}] {msg}")

class DesignStateTracker:
    """Tracks design state and chat history"""
    
    def __init__(self):
        self.context_dir = os.path.join(BASE_DIR, "modules", "clo_companion", "context")
        os.makedirs(self.context_dir, exist_ok=True)
        
        self.state_file = os.path.join(self.context_dir, "design_state.json")
        self.chat_file = os.path.join(self.context_dir, "clo_chat_history.json")
        
        log("DesignStateTracker initialized", "CLO")
    
    def get_current_state(self) -> Dict:
        """Get current design state"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._default_state()
        except Exception as e:
            log(f"Error reading design state: {e}", "CLO", level="ERROR")
            return self._default_state()
    
    def update_state(self, current_file: str, prompt: Optional[str] = None,
                    attributes: Optional[Dict] = None, version: int = 1):
        """Update design state after generation or iteration"""
        try:
            state = self.get_current_state()
            
            # Update current file
            if current_file not in state["history"]:
                state["history"].append(current_file)
            
            state["current_file"] = current_file
            state["version"] = version
            state["last_update"] = datetime.now().isoformat()
            
            if prompt:
                state["last_prompt"] = prompt
            if attributes:
                state["attributes"].update(attributes)
            
            # Save
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            log(f"Updated design state: {os.path.basename(current_file)} (v{version})", "CLO")
            
        except Exception as e:
            log(f"Error updating design state: {e}", "CLO", level="ERROR")
    
    def add_to_history(self, file_path: str):
        """Add file to history (for undo)"""
        state = self.get_current_state()
        if file_path not in state["history"]:
            state["history"].append(file_path)
            self._save_state(state)
    
    def get_previous_version(self) -> Optional[str]:
        """Get previous version file path for undo"""
        state = self.get_current_state()
        history = state.get("history", [])
        if len(history) >= 2:
            return history[-2]  # Second to last
        return None
    
    def _default_state(self) -> Dict:
        """Return default empty state"""
        return {
            "current_file": None,
            "history": [],
            "attributes": {},
            "last_prompt": "",
            "version": 1,
            "last_update": None
        }
    
    def _save_state(self, state: Dict):
        """Save state to file"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log(f"Error saving design state: {e}", "CLO", level="ERROR")
    
    def add_chat_message(self, role: str, message: str, timestamp: Optional[str] = None):
        """Add message to chat history"""
        try:
            # Load existing chat
            chat_history = []
            if os.path.exists(self.chat_file):
                with open(self.chat_file, 'r', encoding='utf-8') as f:
                    chat_history = json.load(f)
            
            # Add new message
            if timestamp is None:
                timestamp = datetime.now().isoformat()
            
            chat_history.append({
                "role": role,  # "user" or "ai"
                "message": message,
                "timestamp": timestamp
            })
            
            # Keep last 50 messages (reduced for performance)
            if len(chat_history) > 50:
                chat_history = chat_history[-50:]
            
            # Save
            with open(self.chat_file, 'w', encoding='utf-8') as f:
                json.dump(chat_history, f, indent=2, ensure_ascii=False)
            
            log(f"Added {role} chat message", "CLO", print_to_console=False)
            
        except Exception as e:
            log(f"Error adding chat message: {e}", "CLO", level="ERROR")
    
    def get_chat_history(self, limit: int = 50) -> List[Dict]:
        """Get chat history"""
        try:
            if os.path.exists(self.chat_file):
                with open(self.chat_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    return history[-limit:] if limit else history
            return []
        except Exception as e:
            log(f"Error reading chat history: {e}", "CLO", level="ERROR")
            return []
    
    def get_design_context(self) -> Dict:
        """
        Get essential design context for prompt assembly
        
        Returns:
            Dict with keys: color, fabric, fit, version, current_file, garment_type
        """
        state = self.get_current_state()
        
        context = {
            "current_file": state.get("current_file"),
            "version": state.get("version", 1),
            "last_prompt": state.get("last_prompt", "")
        }
        
        # Extract essential attributes
        attributes = state.get("attributes", {})
        context.update({
            "garment_type": attributes.get("garment_type", "unknown"),
            "color": attributes.get("material", ""),  # Material often indicates color
            "fabric": attributes.get("material", "cotton"),
            "fit": "oversized" if "oversized" in str(attributes.values()) else "regular"
        })
        
        # Try to extract color from material if available
        material = attributes.get("material", "")
        if material and material.lower() in ["beige", "white", "black", "denim"]:
            context["color"] = material.lower()
        
        return context
    
    def clear_chat(self):
        """Clear chat history"""
        try:
            if os.path.exists(self.chat_file):
                os.remove(self.chat_file)
            log("Chat history cleared", "CLO")
        except Exception as e:
            log(f"Error clearing chat: {e}", "CLO", level="ERROR")

