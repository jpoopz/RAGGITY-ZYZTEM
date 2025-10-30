"""
Configuration Manager - Centralized JSON config handling
Manages suite-wide and per-module configurations
"""

import os
import json
import sys
from pathlib import Path

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Import logger
try:
    from logger import log
except ImportError:
    def log(msg, category="CONFIG"):
        print(f"[{category}] {msg}")

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
SUITE_CONFIG_PATH = os.path.join(CONFIG_DIR, "suite_config.json")
MODULES_REGISTRY_PATH = os.path.join(CONFIG_DIR, "modules.json")

# Ensure config directory exists
os.makedirs(CONFIG_DIR, exist_ok=True)

# Default suite config
DEFAULT_SUITE_CONFIG = {
    "suite_version": "2.0.0",
    "user_profile": {
        "name": "Julian Poopat",
        "obsidian_vault_path": r"C:\Users\Julian Poopat\Documents\Obsidian",
        "preferred_llm": "llama3.2",
        "ollama_host": "http://localhost:11434"
    },
    "startup": {
        "auto_start_modules": ["academic_rag", "system_monitor"],
        "show_dashboard_on_start": True,
        "minimize_to_tray": False
    },
    "logging": {
        "level": "INFO",
        "rotation_size_mb": 5,
        "retention_days": 30,
        "module_specific_logs": True
    },
    "monitoring": {
        "health_check_interval_seconds": 30,
        "resource_check_interval_seconds": 10,
        "alert_on_module_crash": True
    },
    "security": {
        "auth_token": None,  # Will be generated on first run
        "bind_localhost_only": True,
        "cors_enabled": False
    },
    "resources": {
        "max_concurrent_workers": 4,
        "prefer_gpu": False,
        "max_ram_mb": 4096,
        "default_model": "llama3.2"
    },
    "modules": {
        "academic_rag": {
            "enabled": True,
            "auto_start": True,
            "config_file": "academic_rag_config.json"
        },
        "clo_companion": {
            "enabled": False,
            "auto_start": False,
            "config_file": "clo_companion_config.json"
        },
        "web_retriever": {
            "enabled": True,
            "auto_start": False,
            "config_file": "web_retriever_config.json"
        },
        "automation_hub": {
            "enabled": True,
            "auto_start": False,
            "config_file": "automation_hub_config.json"
        },
        "system_monitor": {
            "enabled": True,
            "auto_start": True,
            "config_file": None
        }
    },
    "inter_module": {
        "enable_bus": True,
        "message_queue_size": 100,
        "event_logging": True
    },
    "gui": {
        "theme": "light",
        "window_width": 1200,
        "window_height": 800,
        "last_tab": "Dashboard"
    },
    "updates": {
        "check_on_startup": True,
        "check_interval_hours": 24,
        "update_source": "local_git"
    }
}

def generate_auth_token():
    """Generate a random auth token for inter-module communication"""
    import secrets
    return secrets.token_urlsafe(32)

def load_suite_config():
    """Load suite configuration, creating default if not exists"""
    try:
        if os.path.exists(SUITE_CONFIG_PATH):
            with open(SUITE_CONFIG_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Generate auth token if missing
            if not config.get("security", {}).get("auth_token"):
                config.setdefault("security", {})["auth_token"] = generate_auth_token()
                save_suite_config(config)
                log("Generated new auth token", "CONFIG")
            
            return config
        else:
            # Create default config
            config = DEFAULT_SUITE_CONFIG.copy()
            config["security"]["auth_token"] = generate_auth_token()
            save_suite_config(config)
            log("Created default suite config", "CONFIG")
            return config
    except Exception as e:
        log(f"Error loading suite config: {e}", "CONFIG")
        return DEFAULT_SUITE_CONFIG.copy()

def save_suite_config(config):
    """Save suite configuration"""
    try:
        with open(SUITE_CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        log(f"Error saving suite config: {e}", "CONFIG")
        return False

def get_suite_config():
    """Get current suite configuration (singleton pattern)"""
    if not hasattr(get_suite_config, '_config'):
        get_suite_config._config = load_suite_config()
    return get_suite_config._config

def reload_suite_config():
    """Reload suite configuration from disk"""
    get_suite_config._config = load_suite_config()
    return get_suite_config._config

def get_module_config(module_id):
    """Load per-module configuration"""
    try:
        suite_config = get_suite_config()
        module_info = suite_config.get("modules", {}).get(module_id, {})
        config_file = module_info.get("config_file")
        
        if not config_file:
            return {}
        
        config_path = os.path.join(CONFIG_DIR, config_file)
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Return empty config if file doesn't exist
            return {}
    except Exception as e:
        log(f"Error loading module config for {module_id}: {e}", "CONFIG")
        return {}

def save_module_config(module_id, config):
    """Save per-module configuration"""
    try:
        suite_config = get_suite_config()
        module_info = suite_config.get("modules", {}).get(module_id, {})
        config_file = module_info.get("config_file")
        
        if not config_file:
            config_file = f"{module_id}_config.json"
            suite_config.setdefault("modules", {}).setdefault(module_id, {})["config_file"] = config_file
            save_suite_config(suite_config)
        
        config_path = os.path.join(CONFIG_DIR, config_file)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        log(f"Error saving module config for {module_id}: {e}", "CONFIG")
        return False

def get_auth_token():
    """Get suite auth token"""
    return get_suite_config().get("security", {}).get("auth_token", "")

def get_module_enabled(module_id):
    """Check if module is enabled"""
    suite_config = get_suite_config()
    return suite_config.get("modules", {}).get(module_id, {}).get("enabled", False)

def set_module_enabled(module_id, enabled):
    """Enable/disable a module"""
    suite_config = get_suite_config()
    suite_config.setdefault("modules", {}).setdefault(module_id, {})["enabled"] = enabled
    return save_suite_config(suite_config)

def get_auto_start_modules():
    """Get list of modules to auto-start"""
    suite_config = get_suite_config()
    auto_start = suite_config.get("startup", {}).get("auto_start_modules", [])
    # Filter to only enabled modules
    return [m for m in auto_start if get_module_enabled(m)]




