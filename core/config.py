"""
Core configuration for LLM and embedding settings
"""

from __future__ import annotations
import os
from typing import Optional
from pathlib import Path


class Config:
    """Configuration object for LLM connector"""
    
    def __init__(self):
        # Provider settings (ollama or openai)
        self.provider: str = os.getenv("LLM_PROVIDER", "ollama")
        
        # Model settings
        self.model_name: str = os.getenv("LLM_MODEL", "llama3.2")
        self.embedding_model: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        
        # Ollama settings
        self.ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        # OpenAI settings
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.openai_embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        
        # Generation settings
        self.temperature: float = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.max_tokens: Optional[int] = int(os.getenv("LLM_MAX_TOKENS", "0")) or None
        self.timeout: int = int(os.getenv("LLM_TIMEOUT", "120"))
        
        # Path settings
        base_dir = Path(__file__).parent.parent.absolute()
        self.data_dir: str = os.getenv("DATA_DIR", str(base_dir / "data"))
        self.vector_dir: str = os.getenv("VECTOR_DIR", str(base_dir / "vector_store"))


# Global config instance
CFG = Config()

