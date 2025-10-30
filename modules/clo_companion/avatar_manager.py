"""
Avatar Manager - Handles default avatars and parametric scaling
"""

import os
import sys
import json
from typing import Dict, Optional, Literal

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
except ImportError:
    def log(msg, category="CLO"):
        print(f"[{category}] {msg}")

class AvatarManager:
    """Manages avatar templates and parametric scaling"""
    
    def __init__(self):
        self.avatar_dir = os.path.join(BASE_DIR, "modules", "clo_companion", "avatars")
        os.makedirs(self.avatar_dir, exist_ok=True)
        
        self.default_avatars = {
            "male": {
                "height": 175.0,  # cm
                "chest": 100.0,
                "waist": 85.0,
                "hips": 95.0
            },
            "female": {
                "height": 165.0,
                "chest": 90.0,
                "waist": 70.0,
                "hips": 95.0
            },
            "unisex": {
                "height": 170.0,
                "chest": 95.0,
                "waist": 80.0,
                "hips": 90.0
            }
        }
        
        log("AvatarManager initialized", "CLO")
    
    def get_avatar_params(self, avatar_type: Literal["male", "female", "unisex"] = "unisex",
                         scale: float = 1.0) -> Dict:
        """
        Get avatar parameters with optional scaling
        
        Args:
            avatar_type: Avatar type
            scale: Scale factor (1.0 = default)
        
        Returns:
            Dict with parametric measurements
        """
        base_params = self.default_avatars.get(avatar_type, self.default_avatars["unisex"]).copy()
        
        # Apply scaling
        scaled = {}
        for key, value in base_params.items():
            scaled[key] = value * scale
        
        return scaled
    
    def save_avatar_config(self, config: Dict, filename: str = "current_avatar.json"):
        """Save avatar configuration"""
        try:
            config_file = os.path.join(self.avatar_dir, filename)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            log(f"Avatar config saved: {filename}", "CLO")
        except Exception as e:
            log(f"Error saving avatar config: {e}", "CLO", level="ERROR")
    
    def load_avatar_config(self, filename: str = "current_avatar.json") -> Optional[Dict]:
        """Load avatar configuration"""
        try:
            config_file = os.path.join(self.avatar_dir, filename)
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            log(f"Error loading avatar config: {e}", "CLO", level="WARNING")
        return None




