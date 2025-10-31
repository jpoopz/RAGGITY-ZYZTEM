from pydantic import BaseModel
from typing import Optional, Dict, Any


class HealthFull(BaseModel):
    api: Dict[str, Any]
    clo: Dict[str, Any]
    vector_store: str
    ollama: Dict[str, Any]
    sys: Dict[str, Any]


