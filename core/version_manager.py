"""
Version Manager - Handles versioning and update checking
Manages suite and module versions
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
    def log(msg, category="VERSION"):
        print(f"[{category}] {msg}")

from core.module_registry import get_registry

class VersionManager:
    """Manages versioning for suite and modules"""
    
    def __init__(self):
        self.suite_version = "2.0.0"
        self.module_versions = {}
    
    def get_suite_version(self):
        """Get suite version"""
        return self.suite_version
    
    def load_module_versions(self):
        """Load versions from all registered modules"""
        registry = get_registry()
        modules = registry.get_all_modules()
        
        for module in modules:
            module_id = module.get('module_id')
            metadata = module.get('metadata', {})
            version = metadata.get('version', 'unknown')
            self.module_versions[module_id] = version
        
        return self.module_versions
    
    def get_module_version(self, module_id):
        """Get version for a specific module"""
        if module_id in self.module_versions:
            return self.module_versions[module_id]
        
        # Try to load from module_info.json
        registry = get_registry()
        module = registry.get_module(module_id)
        if module:
            metadata = module.get('metadata', {})
            version = metadata.get('version', 'unknown')
            self.module_versions[module_id] = version
            return version
        
        return 'unknown'
    
    def check_compatibility(self, module_id):
        """Check if module version is compatible with suite"""
        module_version = self.get_module_version(module_id)
        suite_version = self.get_suite_version()
        
        # Simple compatibility check (can be enhanced)
        if module_version == 'unknown':
            return False, "Module version unknown"
        
        # Suite 2.0.0 should be compatible with module 1.x+
        major_suite = int(suite_version.split('.')[0])
        try:
            major_module = int(module_version.split('.')[0])
            if major_module >= 1:
                return True, "Compatible"
            else:
                return False, f"Module version {module_version} too old"
        except:
            return True, "Version format unknown, assuming compatible"
    
    def get_version_matrix(self):
        """Get version compatibility matrix"""
        registry = get_registry()
        modules = registry.get_all_modules()
        
        matrix = {
            "suite_version": self.suite_version,
            "modules": {}
        }
        
        for module in modules:
            module_id = module.get('module_id')
            version = self.get_module_version(module_id)
            is_compatible, message = self.check_compatibility(module_id)
            
            matrix["modules"][module_id] = {
                "version": version,
                "compatible": is_compatible,
                "message": message
            }
        
        return matrix

# Global version manager instance
_version_manager_instance = None

def get_version_manager():
    """Get global version manager instance (singleton)"""
    global _version_manager_instance
    if _version_manager_instance is None:
        _version_manager_instance = VersionManager()
        _version_manager_instance.load_module_versions()
    return _version_manager_instance

def get_current_version():
    """Get current suite version (convenience function)"""
    return get_version_manager().get_suite_version()




