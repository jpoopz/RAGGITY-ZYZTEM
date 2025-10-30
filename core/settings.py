"""
Unified settings loader with YAML + JSON + ENV precedence.

Precedence order (highest to lowest):
1. Environment variables
2. ui/config.json (UI runtime settings)
3. config.yaml (repository config)
4. Defaults from Settings schema

Security:
- Sensitive keys (API keys, cloud keys) are only loaded from environment
- save_yaml() excludes secrets to prevent accidental commits
- save_json() only persists UI-safe settings
"""

from __future__ import annotations

import os
import json
from typing import Any, Dict
from pathlib import Path

from pydantic import ValidationError

from .settings_schema import Settings
from .logger import get_logger

log = get_logger("settings")

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

ROOT = Path(__file__).parent.parent


def _load_yaml(path: str) -> Dict[str, Any]:
    """Load YAML config file"""
    if not YAML_AVAILABLE or not os.path.exists(path):
        return {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        log.error(f"Failed to load YAML from {path}: {e}")
        return {}


def _load_json(path: str) -> Dict[str, Any]:
    """Load JSON config file"""
    if not os.path.exists(path):
        return {}
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f) or {}
    except Exception as e:
        log.error(f"Failed to load JSON from {path}: {e}")
        return {}


def _env_overrides() -> Dict[str, Any]:
    """Load settings from environment variables"""
    m = {}
    
    # Environment
    env = os.getenv("APP_ENV")
    if env:
        m["env"] = env
    
    # Paths
    data_dir = os.getenv("DATA_DIR")
    if data_dir:
        m["data_dir"] = data_dir
    
    vector_dir = os.getenv("VECTOR_DIR")
    if vector_dir:
        m["vector_dir"] = vector_dir
    
    chroma_dir = os.getenv("CHROMA_DIR")
    if chroma_dir:
        m["chroma_dir"] = chroma_dir
    
    # Vector store
    vstore = os.getenv("VECTOR_STORE")
    if vstore:
        m["vector_store"] = vstore
    
    # LLM settings
    mname = os.getenv("MODEL_NAME") or os.getenv("LLM_MODEL")
    if mname:
        m["model_name"] = mname
    
    msecondary = os.getenv("MODEL_SECONDARY")
    if msecondary:
        m["model_secondary"] = msecondary
    
    emb_model = os.getenv("EMBEDDING_MODEL")
    if emb_model:
        m["embedding_model"] = emb_model
    
    prov = os.getenv("LLM_PROVIDER")
    if prov:
        m["provider"] = prov
    
    # Generation settings
    temp = os.getenv("TEMP") or os.getenv("LLM_TEMPERATURE")
    if temp:
        try:
            m["temperature"] = float(temp)
        except ValueError:
            log.warning(f"Invalid temperature value: {temp}")
    
    max_tokens = os.getenv("LLM_MAX_TOKENS")
    if max_tokens:
        try:
            m["max_tokens"] = int(max_tokens) if max_tokens != "0" else None
        except ValueError:
            log.warning(f"Invalid max_tokens value: {max_tokens}")
    
    timeout = os.getenv("LLM_TIMEOUT")
    if timeout:
        try:
            m["timeout"] = int(timeout)
        except ValueError:
            log.warning(f"Invalid timeout value: {timeout}")
    
    # Ollama
    ollama_host = os.getenv("OLLAMA_HOST")
    if ollama_host:
        m["ollama_host"] = ollama_host
    
    # OpenAI (sensitive - only from env)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        m["openai_api_key"] = openai_key
    
    openai_model = os.getenv("OPENAI_MODEL")
    if openai_model:
        m["openai_model"] = openai_model
    
    openai_emb = os.getenv("OPENAI_EMBEDDING_MODEL")
    if openai_emb:
        m["openai_embedding_model"] = openai_emb
    
    # Hybrid mode
    hybrid = os.getenv("HYBRID_MODE")
    if hybrid is not None:
        m["hybrid_mode"] = hybrid == "1" or hybrid.lower() == "true"
    
    # Cloud (sensitive - only from env)
    cloud_url = os.getenv("CLOUD_URL")
    if cloud_url:
        m["cloud_url"] = cloud_url
    
    cloud_key = os.getenv("CLOUD_KEY")
    if cloud_key:
        m["cloud_key"] = cloud_key
    
    api_key = os.getenv("API_KEY")
    if api_key:
        m["api_key"] = api_key
    
    # CORS
    cors = os.getenv("CORS_ORIGINS")
    if cors:
        m["cors_allow"] = [o.strip() for o in cors.split(",")]
    
    # UI
    theme = os.getenv("THEME")
    if theme:
        m["theme"] = theme
    
    # Performance
    batch_size = os.getenv("BATCH_SIZE")
    if batch_size:
        try:
            m["batch_size"] = int(batch_size)
        except ValueError:
            log.warning(f"Invalid batch_size value: {batch_size}")
    
    max_k = os.getenv("MAX_K")
    if max_k:
        try:
            m["max_k"] = int(max_k)
        except ValueError:
            log.warning(f"Invalid max_k value: {max_k}")
    
    # Obsidian
    obsidian_path = os.getenv("OBSIDIAN_VAULT_PATH")
    if obsidian_path:
        m["obsidian_vault_path"] = obsidian_path
    
    return m


def load_settings() -> Settings:
    """
    Load settings with proper precedence.
    
    Precedence (highest to lowest):
    1. Environment variables
    2. ui/config.json (UI runtime settings)
    3. config.yaml (repository config)
    4. Defaults from Settings schema
    
    Returns:
        Settings instance
    """
    # Start with defaults
    defaults = Settings().model_dump()
    
    # Load YAML config
    yaml_config = _load_yaml(os.path.join(ROOT, "config.yaml"))
    
    # Load UI JSON config
    json_config = _load_json(os.path.join(ROOT, "ui", "config.json"))
    
    # Load environment overrides
    env_config = _env_overrides()
    
    # Merge in order: defaults < yaml < json < env
    merged = {**defaults, **yaml_config, **json_config, **env_config}
    
    try:
        settings = Settings(**merged)
        log.info(f"Settings loaded: provider={settings.provider}, vector_store={settings.vector_store}, env={settings.env}")
        return settings
    except ValidationError as ve:
        log.error(f"Settings validation failed: {ve}")
        # Fall back to defaults
        return Settings(**defaults)


def save_yaml(s: Settings) -> bool:
    """
    Save settings to config.yaml.
    
    Only persists application-level settings.
    Excludes secrets (API keys, cloud keys) to prevent accidental commits.
    
    Args:
        s: Settings instance
    
    Returns:
        True if successful
    """
    if not YAML_AVAILABLE:
        log.warning("PyYAML not installed, cannot save YAML config")
        return False
    
    path = os.path.join(ROOT, "config.yaml")
    
    # Only persist safe, durable app-level items
    data = s.model_dump(include={
        "env", "data_dir", "vector_dir", "chroma_dir", "vector_store",
        "model_name", "model_secondary", "embedding_model", "provider",
        "temperature", "max_tokens", "timeout",
        "ollama_host", "openai_model", "openai_embedding_model",
        "hybrid_mode", "cors_allow", "theme", "batch_size", "max_k",
        "show_advanced"
    })
    
    # Remove None values for cleaner YAML
    data = {k: v for k, v in data.items() if v is not None}
    
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
        log.info(f"Settings saved to {path}")
        return True
    except Exception as e:
        log.error(f"Failed to save YAML config: {e}")
        return False


def save_json(s: Settings) -> bool:
    """
    Save UI runtime settings to ui/config.json.
    
    Only persists UI-specific toggles that can safely change at runtime.
    
    Args:
        s: Settings instance
    
    Returns:
        True if successful
    """
    path = os.path.join(ROOT, "ui", "config.json")
    
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Only persist UI-safe runtime settings
        data = s.model_dump(include={
            "theme",
            "show_advanced",
            "vector_store",
            "max_k"
        })
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        
        log.info(f"UI settings saved to {path}")
        return True
    except Exception as e:
        log.error(f"Failed to save UI config: {e}")
        return False

