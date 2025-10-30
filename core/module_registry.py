"""
Module Registry - Auto-discovers and manages modules
Handles module registration, port allocation, and lifecycle
"""

import os
import json
import socket
import sys
from pathlib import Path

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

try:
    from logger import log
except ImportError:
    def log(msg, category="REGISTRY"):
        print(f"[{category}] {msg}")

from core.config_manager import CONFIG_DIR, MODULES_REGISTRY_PATH, get_suite_config

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULES_DIR = os.path.join(BASE_DIR, "modules")

os.makedirs(CONFIG_DIR, exist_ok=True)

class ModuleRegistry:
    """Manages module discovery, registration, and port allocation"""
    
    def __init__(self):
        self.modules = {}
        self.port_allocations = {}
        self.load_registry()
    
    def discover_modules(self):
        """Scan modules/ directory and discover all modules"""
        discovered = []
        
        if not os.path.exists(MODULES_DIR):
            log(f"Modules directory not found: {MODULES_DIR}", "REGISTRY", level="WARNING")
            return discovered
        
        for item in os.listdir(MODULES_DIR):
            module_path = os.path.join(MODULES_DIR, item)
            if os.path.isdir(module_path):
                module_info_path = os.path.join(module_path, "module_info.json")
                if os.path.exists(module_info_path):
                    try:
                        with open(module_info_path, 'r', encoding='utf-8') as f:
                            module_info = json.load(f)
                        
                        module_info['path'] = module_path
                        module_info['module_id'] = module_info.get('module_id', item)
                        discovered.append(module_info)
                        log(f"Discovered module: {module_info['module_id']}", "REGISTRY")
                    except Exception as e:
                        log(f"Error reading module_info.json for {item}: {e}", "REGISTRY", level="ERROR")
        
        return discovered
    
    def validate_module(self, module_info):
        """Validate module has required fields and files"""
        module_id = module_info.get('module_id')
        if not module_id:
            return False, "Missing module_id"
        
        # Check required fields
        required_fields = ['name', 'version', 'ports']
        for field in required_fields:
            if field not in module_info:
                return False, f"Missing required field: {field}"
        
        # Check entry points
        entry_points = module_info.get('entry_points', {})
        if 'api' not in entry_points:
            return False, "Missing API entry point"
        
        api_file = os.path.join(module_info['path'], entry_points['api'])
        if not os.path.exists(api_file):
            log(f"Warning: API file not found for {module_id}: {api_file}", "REGISTRY", level="WARNING")
            # Don't fail validation for stubs
        
        return True, "OK"
    
    def check_port_available(self, port):
        """Check if port is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            return result != 0  # Port is available if connection fails
        except:
            return False
    
    def allocate_port(self, module_id, preferred_port=None):
        """Allocate port for module with conflict resolution"""
        # Check if already allocated
        if module_id in self.port_allocations:
            allocated_port = self.port_allocations[module_id]
            if self.check_port_available(allocated_port):
                return allocated_port  # Reuse existing allocation
            else:
                # Port is in use, need to reallocate
                log(f"Port {allocated_port} in use for {module_id}, reallocating", "REGISTRY", level="WARNING")
        
        # Use preferred port if specified and available
        if preferred_port and self.check_port_available(preferred_port):
            self.port_allocations[module_id] = preferred_port
            return preferred_port
        
        # Find first available port in range 5000-5999
        for port in range(5000, 6000):
            if port not in self.port_allocations.values() and self.check_port_available(port):
                self.port_allocations[module_id] = port
                log(f"Allocated port {port} for {module_id}", "REGISTRY")
                return port
        
        # No ports available
        log(f"ERROR: No available ports for {module_id}", "REGISTRY", level="ERROR")
        return None
    
    def register_module(self, module_info):
        """Register a module in the registry"""
        module_id = module_info['module_id']
        
        # Validate
        is_valid, message = self.validate_module(module_info)
        if not is_valid:
            log(f"Module {module_id} validation failed: {message}", "REGISTRY", level="ERROR")
            return False
        
        # Allocate port
        preferred_port = module_info.get('ports', {}).get('api')
        allocated_port = self.allocate_port(module_id, preferred_port)
        
        if not allocated_port:
            return False
        
        # Register module
        self.modules[module_id] = {
            "module_id": module_id,
            "path": module_info['path'],
            "status": "registered",
            "port": allocated_port,
            "process_id": None,
            "last_health_check": None,
            "metadata": module_info
        }
        
        log(f"Registered module: {module_id} on port {allocated_port}", "REGISTRY")
        return True
    
    def register_all(self):
        """Discover and register all modules"""
        discovered = self.discover_modules()
        registered_count = 0
        
        for module_info in discovered:
            if self.register_module(module_info):
                registered_count += 1
        
        self.save_registry()
        log(f"Registered {registered_count}/{len(discovered)} modules", "REGISTRY")
        return registered_count
    
    def get_module(self, module_id):
        """Get module info by ID"""
        return self.modules.get(module_id)
    
    def get_all_modules(self):
        """Get all registered modules"""
        return list(self.modules.values())
    
    def set_module_process_id(self, module_id, process_id):
        """Set process ID for running module"""
        if module_id in self.modules:
            self.modules[module_id]['process_id'] = process_id
            self.save_registry()
    
    def set_module_status(self, module_id, status):
        """Set module status (registered, running, stopped, error)"""
        if module_id in self.modules:
            self.modules[module_id]['status'] = status
            self.save_registry()
    
    def free_port(self, module_id):
        """Free port when module stops"""
        if module_id in self.port_allocations:
            port = self.port_allocations.pop(module_id)
            log(f"Freed port {port} from {module_id}", "REGISTRY")
            self.save_registry()
    
    def load_registry(self):
        """Load registry from disk"""
        if os.path.exists(MODULES_REGISTRY_PATH):
            try:
                with open(MODULES_REGISTRY_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.modules = data.get('modules', {})
                self.port_allocations = data.get('port_allocations', {})
                
                # Convert port_allocations from list format if needed
                if isinstance(self.port_allocations, list):
                    # Legacy format, convert
                    self.port_allocations = {k: v for k, v in self.port_allocations}
                elif isinstance(self.port_allocations, dict):
                    # Already correct format
                    # Reverse lookup: port -> module_id
                    reverse = {v: k for k, v in self.port_allocations.items()}
                    self.port_allocations = {k: v for k, v in reverse.items()}
                    # Fix: should be module_id -> port
                    self.port_allocations = {v: k for k, v in reverse.items()}
                
                log(f"Loaded registry: {len(self.modules)} modules", "REGISTRY")
            except Exception as e:
                log(f"Error loading registry: {e}", "REGISTRY", level="ERROR")
                self.modules = {}
                self.port_allocations = {}
        else:
            self.modules = {}
            self.port_allocations = {}
    
    def save_registry(self):
        """Save registry to disk"""
        try:
            data = {
                "version": "2.0.0",
                "registered_modules": list(self.modules.values()),
                "port_allocations": self.port_allocations
            }
            
            with open(MODULES_REGISTRY_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log(f"Error saving registry: {e}", "REGISTRY", level="ERROR")

# Global registry instance
_registry_instance = None

def get_registry():
    """Get global registry instance (singleton)"""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ModuleRegistry()
    return _registry_instance




