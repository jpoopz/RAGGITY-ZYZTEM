"""
Core configuration for LLM and embedding settings
Supports YAML config file with environment variable overrides
"""

from __future__ import annotations
import os
from typing import Optional, Any, Dict
from pathlib import Path


def _load_yaml_config() -> Dict[str, Any]:
    """Load configuration from config.yaml if it exists"""
    try:
        import yaml
        
        config_file = Path(__file__).parent.parent / "config.yaml"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
    except ImportError:
        # pyyaml not installed
        pass
    except Exception:
        # Error reading config
        pass
    
    return {}


class Config:
    """Configuration object for LLM connector"""
    
    def __init__(self):
        # Load YAML config (if available)
        yaml_config = _load_yaml_config()
        
        # Helper to get config value: env var > yaml > default
        def get_config(env_key: str, yaml_key: str, default: Any) -> Any:
            # Environment variable takes precedence
            env_value = os.getenv(env_key)
            if env_value is not None:
                return env_value
            
            # Then YAML config
            yaml_value = yaml_config.get(yaml_key)
            if yaml_value is not None:
                return yaml_value
            
            # Finally default
            return default
        
        # Provider settings (ollama or openai)
        self.provider: str = get_config("LLM_PROVIDER", "provider", "ollama")
        
        # Model settings
        self.model_name: str = get_config("LLM_MODEL", "model_name", "llama3.2")
        self.embedding_model: str = get_config("EMBEDDING_MODEL", "embedding_model", "nomic-embed-text")
        
        # Ollama settings
        self.ollama_host: str = get_config("OLLAMA_HOST", "ollama_host", "http://localhost:11434")
        
        # OpenAI settings
        self.openai_api_key: Optional[str] = get_config("OPENAI_API_KEY", "openai_api_key", None)
        self.openai_model: str = get_config("OPENAI_MODEL", "openai_model", "gpt-4o-mini")
        self.openai_embedding_model: str = get_config(
            "OPENAI_EMBEDDING_MODEL", "openai_embedding_model", "text-embedding-3-small"
        )
        
        # Generation settings
        temperature_str = get_config("LLM_TEMPERATURE", "temperature", "0.3")
        self.temperature: float = float(temperature_str) if isinstance(temperature_str, (str, int, float)) else 0.3
        
        max_tokens_str = get_config("LLM_MAX_TOKENS", "max_tokens", "0")
        self.max_tokens: Optional[int] = int(max_tokens_str) if max_tokens_str else None
        
        timeout_str = get_config("LLM_TIMEOUT", "timeout", "120")
        self.timeout: int = int(timeout_str) if isinstance(timeout_str, (str, int)) else 120
        
        # Vector store settings
        self.vector_store: str = get_config("VECTOR_STORE", "vector_store", "faiss")  # faiss or chroma
        
        # Hybrid mode settings
        hybrid_mode_str = get_config("HYBRID_MODE", "hybrid_mode", "1")
        self.hybrid_mode: bool = str(hybrid_mode_str) == "1" or str(hybrid_mode_str).lower() == "true"
        
        # Path settings
        base_dir = Path(__file__).parent.parent.absolute()
        self.data_dir: str = get_config("DATA_DIR", "data_dir", str(base_dir / "data"))
        self.vector_dir: str = get_config("VECTOR_DIR", "vector_dir", str(base_dir / "vector_store"))
        self.chroma_dir: str = get_config("CHROMA_DIR", "chroma_dir", str(base_dir / ".chromadb"))


# Global config instance
CFG = Config()

