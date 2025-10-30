"""
Settings schema for RAGGITY ZYZTEM using Pydantic.

Provides type-safe configuration with validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class Settings(BaseModel):
    """
    Complete settings schema for RAGGITY ZYZTEM.
    
    Precedence order:
    1. Environment variables (highest)
    2. ui/config.json
    3. config.yaml
    4. Defaults (lowest)
    """
    
    # Environment
    env: Literal["dev", "prod"] = Field(
        default="dev",
        description="Environment: dev or prod"
    )
    
    # Paths
    data_dir: str = Field(
        default="data",
        description="Data directory for documents"
    )
    
    vector_dir: str = Field(
        default="vectorstore",
        description="Vector store directory"
    )
    
    chroma_dir: str = Field(
        default=".chromadb",
        description="ChromaDB storage directory"
    )
    
    # Vector Store
    vector_store: Literal["faiss", "chroma"] = Field(
        default="faiss",
        description="Vector database backend"
    )
    
    # LLM Configuration
    model_name: str = Field(
        default="llama3.2",
        description="Primary LLM model name"
    )
    
    model_secondary: Optional[str] = Field(
        default=None,
        description="Secondary model for complex queries"
    )
    
    embedding_model: str = Field(
        default="nomic-embed-text",
        description="Embedding model name"
    )
    
    provider: Literal["ollama", "openai"] = Field(
        default="ollama",
        description="LLM provider"
    )
    
    # Generation Settings
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="LLM temperature (0.0-2.0)"
    )
    
    max_tokens: Optional[int] = Field(
        default=None,
        description="Max tokens (None = unlimited)"
    )
    
    timeout: int = Field(
        default=120,
        description="LLM request timeout in seconds"
    )
    
    # Ollama Settings
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Ollama API host"
    )
    
    # OpenAI Settings (optional)
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key"
    )
    
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model name"
    )
    
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model"
    )
    
    # Hybrid Mode
    hybrid_mode: bool = Field(
        default=True,
        description="Enable cloud query delegation"
    )
    
    # API / Security
    cors_allow: list[str] = Field(
        default_factory=lambda: ["http://localhost", "http://127.0.0.1"],
        description="CORS allowed origins"
    )
    
    cloud_url: Optional[str] = Field(
        default=None,
        description="Cloud bridge URL"
    )
    
    cloud_key: Optional[str] = Field(
        default=None,
        description="Cloud bridge authentication key"
    )
    
    api_key: Optional[str] = Field(
        default=None,
        description="API authentication key"
    )
    
    # UI Settings
    theme: Literal["dark", "light", "auto"] = Field(
        default="dark",
        description="UI theme"
    )
    
    show_advanced: bool = Field(
        default=False,
        description="Show advanced options in UI"
    )
    
    # Performance
    batch_size: int = Field(
        default=64,
        ge=1,
        le=512,
        description="Embedding batch size"
    )
    
    max_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of contexts to retrieve"
    )
    
    # Obsidian (legacy)
    obsidian_vault_path: Optional[str] = Field(
        default=None,
        description="Path to Obsidian vault (optional)"
    )
    
    class Config:
        """Pydantic config"""
        validate_assignment = True
        extra = "ignore"  # Ignore unknown fields

