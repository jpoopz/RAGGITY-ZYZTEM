"""
Knowledge Profiles - Manage multiple vault subsets for different courses/contexts
"""

import os
import json
import sys
from pathlib import Path

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

try:
    from logger import log
except ImportError:
    def log(msg, category="PROFILES"):
        print(f"[{category}] {msg}")

from core.config_manager import get_module_config, save_module_config

class KnowledgeProfile:
    """Represents a knowledge profile (course/context subset)"""
    
    def __init__(self, name, vault_path, active=False, filter_paths=None):
        self.name = name
        self.vault_path = vault_path
        self.active = active
        self.filter_paths = filter_paths or []  # Subdirectories to include
    
    def to_dict(self):
        return {
            "name": self.name,
            "vault_path": self.vault_path,
            "active": self.active,
            "filter_paths": self.filter_paths
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get("name", ""),
            vault_path=data.get("vault_path", ""),
            active=data.get("active", False),
            filter_paths=data.get("filter_paths", [])
        )

class ProfileManager:
    """Manages knowledge profiles"""
    
    def __init__(self):
        self.profiles = []
        self.load_profiles()
    
    def load_profiles(self):
        """Load profiles from module config"""
        module_config = get_module_config("academic_rag")
        profiles_data = module_config.get("knowledge_profiles", [])
        
        self.profiles = [KnowledgeProfile.from_dict(p) for p in profiles_data]
        
        # If no profiles, create default
        if not self.profiles:
            default_vault = module_config.get("vault_path", r"C:\Users\Julian Poopat\Documents\Obsidian")
            self.profiles.append(KnowledgeProfile(
                name="Default",
                vault_path=default_vault,
                active=True
            ))
            self.save_profiles()
    
    def save_profiles(self):
        """Save profiles to module config"""
        module_config = get_module_config("academic_rag")
        module_config["knowledge_profiles"] = [p.to_dict() for p in self.profiles]
        save_module_config("academic_rag", module_config)
    
    def get_active_profile(self):
        """Get the currently active profile"""
        for profile in self.profiles:
            if profile.active:
                return profile
        return None
    
    def set_active_profile(self, profile_name):
        """Set active profile by name"""
        for profile in self.profiles:
            profile.active = (profile.name == profile_name)
        self.save_profiles()
    
    def add_profile(self, profile):
        """Add a new profile"""
        self.profiles.append(profile)
        self.save_profiles()
    
    def remove_profile(self, profile_name):
        """Remove a profile"""
        self.profiles = [p for p in self.profiles if p.name != profile_name]
        self.save_profiles()
    
    def get_all_profiles(self):
        """Get all profiles"""
        return self.profiles

# Global profile manager instance
_profile_manager = None

def get_profile_manager():
    """Get global profile manager (singleton)"""
    global _profile_manager
    if _profile_manager is None:
        _profile_manager = ProfileManager()
    return _profile_manager




