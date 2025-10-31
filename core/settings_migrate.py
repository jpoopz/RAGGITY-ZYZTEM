"""
Settings migration utility.

Safely upgrades legacy config files to the new unified settings format.
Backs up old files and merges values into new structure.
"""

from __future__ import annotations

import os
import sys
import json
import shutil
from typing import Dict, Any, Tuple

from .settings import load_settings, save_yaml, save_json

# Add parent directory to path to import logger
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logger import get_logger

log = get_logger("settings_migrate")

# Legacy config file locations (relative to root)
LEGACY_PATHS = [
    ("", "settings.json"),      # Root settings.json
    ("ui", "settings.json"),    # UI-specific settings.json
    ("", ".env"),               # .env file (only to inform user)
]


def find_legacy(root: str) -> Dict[str, str]:
    """
    Find legacy configuration files.
    
    Args:
        root: Project root directory
    
    Returns:
        Dictionary mapping filename to full path
    """
    hits = {}
    
    for folder, name in LEGACY_PATHS:
        if folder:
            path = os.path.join(root, folder, name)
        else:
            path = os.path.join(root, name)
        
        if os.path.exists(path):
            hits[name] = path
    
    return hits


def migrate(root: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Migrate legacy config files to unified settings format.
    
    Process:
    1. Find legacy config files
    2. Load current settings as baseline
    3. Merge legacy values using key mappings
    4. Save to new format (JSON + YAML)
    5. Backup legacy files (.bak)
    
    Args:
        root: Project root directory
    
    Returns:
        Tuple of (success: bool, details: dict)
    """
    hits = find_legacy(root)
    
    if not hits:
        return False, {"message": "No legacy config files detected."}
    
    log.info(f"Found {len(hits)} legacy config files")
    
    # Start from current validated Settings as baseline
    try:
        s = load_settings()
    except Exception as e:
        log.error(f"Failed to load current settings: {e}")
        return False, {"message": f"Failed to load settings: {e}"}
    
    changed = False
    notes = []
    
    # Legacy key mappings (old_key -> new_key)
    mapping = {
        # Environment
        "env": "env",
        "ENV": "env",
        
        # Paths
        "DATA_DIR": "data_dir",
        "VECTOR_DIR": "vector_dir",
        "CHROMA_DIR": "chroma_dir",
        
        # Vector store
        "VECTOR_STORE": "vector_store",
        
        # LLM
        "MODEL_NAME": "model_name",
        "LLM_MODEL": "model_name",
        "MODEL_SECONDARY": "model_secondary",
        "EMBEDDING_MODEL": "embedding_model",
        "LLM_PROVIDER": "provider",
        
        # Generation
        "TEMP": "temperature",
        "LLM_TEMPERATURE": "temperature",
        "LLM_MAX_TOKENS": "max_tokens",
        "LLM_TIMEOUT": "timeout",
        
        # Ollama
        "OLLAMA_HOST": "ollama_host",
        
        # OpenAI (skip - should come from env only)
        # "OPENAI_API_KEY": skip
        # "CLOUD_KEY": skip
        # "API_KEY": skip
        
        # Hybrid
        "HYBRID_MODE": "hybrid_mode",
        
        # UI
        "THEME": "theme",
        "SHOW_ADVANCED": "show_advanced",
        
        # Performance
        "BATCH_SIZE": "batch_size",
        "MAX_K": "max_k",
        "max_k": "max_k",
        
        # Legacy
        "vector_store": "vector_store",
        "auto_backup": None,  # Deprecated, ignore
    }
    
    # Process each legacy file
    for fname, path in hits.items():
        if fname.endswith(".json"):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f) or {}
                
                # Map legacy keys to new schema
                mapped = {}
                skipped_secrets = []
                
                for old_key, value in data.items():
                    new_key = mapping.get(old_key)
                    
                    # Skip deprecated fields
                    if new_key is None:
                        continue
                    
                    # Skip secrets (should come from env)
                    if old_key in ["OPENAI_API_KEY", "CLOUD_KEY", "API_KEY"]:
                        skipped_secrets.append(old_key)
                        continue
                    
                    # Type conversion for known fields
                    if new_key in ["temperature", "timeout", "batch_size", "max_k"]:
                        try:
                            value = float(value) if new_key == "temperature" else int(value)
                        except (ValueError, TypeError):
                            log.warning(f"Invalid value for {new_key}: {value}")
                            continue
                    
                    if new_key in ["hybrid_mode", "show_advanced"]:
                        if isinstance(value, str):
                            value = value == "1" or value.lower() == "true"
                        value = bool(value)
                    
                    mapped[new_key] = value
                
                # Apply mapped values
                if mapped:
                    for key, value in mapped.items():
                        try:
                            setattr(s, key, value)
                            changed = True
                        except Exception as e:
                            log.warning(f"Failed to set {key}={value}: {e}")
                    
                    notes.append(f"Merged {path}: {list(mapped.keys())}")
                
                if skipped_secrets:
                    notes.append(f"Skipped secrets in {path}: {skipped_secrets} (set via env)")
                
            except Exception as e:
                notes.append(f"Skipped {path}: {e}")
                log.error(f"Error processing {path}: {e}")
        
        elif fname == ".env":
            # Just inform user - don't parse .env
            notes.append(f"Found {path} - values should be in environment variables")
    
    # Save migrated settings
    if changed:
        # Save to both formats
        save_json(s)  # ui/config.json
        save_yaml(s)  # config.yaml
        
        notes.append("Saved migrated settings to ui/config.json and config.yaml")
        
        # Backup legacy files
        for fname, path in hits.items():
            if fname != ".env":  # Don't backup .env
                backup_path = path + ".bak"
                try:
                    shutil.copy2(path, backup_path)
                    notes.append(f"Backed up {path} -> {backup_path}")
                    log.info(f"Created backup: {backup_path}")
                except Exception as e:
                    notes.append(f"Backup failed for {path}: {e}")
                    log.warning(f"Failed to backup {path}: {e}")
        
        return True, {
            "message": "Migration complete",
            "migrated_files": list(hits.keys()),
            "notes": notes
        }
    
    return False, {
        "message": "Legacy files found but nothing to migrate",
        "found_files": list(hits.keys()),
        "notes": notes
    }


def auto_migrate_on_startup(root: str) -> bool:
    """
    Automatically migrate legacy configs on startup if detected.
    
    Args:
        root: Project root directory
    
    Returns:
        True if migration was performed
    """
    success, details = migrate(root)
    
    if success:
        log.info("Auto-migration completed")
        log.info(f"Details: {details}")
        return True
    
    return False


