"""
LLM Connector - Abstracts LLM providers with Ollama as default and OpenAI optional
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional

# Import settings - try new unified settings, fallback to legacy config
try:
    from .settings import load_settings
    SETTINGS = load_settings()
    CFG = SETTINGS  # Compatibility alias
except ImportError:
    from .config import CFG
    SETTINGS = CFG

from logger import get_logger

log = get_logger("llm")


class LLMConnector:
    """Unified connector for LLM and embedding operations"""
    
    def __init__(self, provider: str | None = None, model: str | None = None, settings = None):
        # Use provided settings or global
        self.settings = settings or SETTINGS
        self.provider = provider or self.settings.provider
        self.model = model or self.settings.model_name

    def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts
        
        Args:
            texts: List of strings to embed
            
        Returns:
            List of embedding vectors
        """
        if self.provider == "ollama":
            return self._embed_ollama(texts)
        elif self.provider == "openai":
            return self._embed_openai(texts)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    def chat(self, messages: List[Dict[str, str]]) -> str:
        """
        Send chat completion request
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            
        Returns:
            Response text from the model
        """
        if self.provider == "ollama":
            return self._chat_ollama(messages)
        elif self.provider == "openai":
            return self._chat_openai(messages)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")

    # ---- Ollama Provider Implementation ----
    
    def _embed_ollama(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using Ollama"""
        import requests
        
        embeddings = []
        model = self.settings.embedding_model
        
        for text in texts:
            try:
                res = requests.post(
                    f"{self.settings.ollama_host}/api/embeddings",
                    json={"model": model, "prompt": text},
                    timeout=self.settings.timeout
                )
                res.raise_for_status()
                data = res.json()
                
                # Ollama returns embedding in 'embedding' key
                if "embedding" in data:
                    embeddings.append(data["embedding"])
                else:
                    log.error(f"Unexpected Ollama response format: {data}")
                    # Return zero vector as fallback
                    embeddings.append([0.0] * 768)
            except Exception as e:
                log.error(f"Ollama embedding error: {e}")
                # Return zero vector as fallback
                embeddings.append([0.0] * 768)
        
        return embeddings

    def _chat_ollama(self, messages: List[Dict[str, str]]) -> str:
        """Chat completion using Ollama"""
        import requests
        
        try:
            res = requests.post(
                f"{self.settings.ollama_host}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                },
                timeout=self.settings.timeout
            )
            res.raise_for_status()
            data = res.json()
            
            # Ollama returns message content in nested structure
            if "message" in data and "content" in data["message"]:
                return data["message"]["content"]
            else:
                log.error(f"Unexpected Ollama response format: {data}")
                return "Error: Invalid response format from Ollama"
        except Exception as e:
            log.error(f"Ollama chat error: {e}")
            return f"Error: {str(e)}"

    # ---- OpenAI Provider Implementation ----
    
    def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI"""
        import os
        
        try:
            from openai import OpenAI
        except ImportError:
            log.error("openai package not installed. Run: pip install openai")
            raise RuntimeError("openai package required for OpenAI provider")
        
        api_key = CFG.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        
        client = OpenAI(api_key=api_key)
        embeddings = []
        
        for text in texts:
            try:
                resp = client.embeddings.create(
                    model=CFG.openai_embedding_model,
                    input=text
                )
                embeddings.append(resp.data[0].embedding)
            except Exception as e:
                log.error(f"OpenAI embedding error: {e}")
                raise
        
        return embeddings

    def _chat_openai(self, messages: List[Dict[str, str]]) -> str:
        """Chat completion using OpenAI"""
        import os
        
        try:
            from openai import OpenAI
        except ImportError:
            log.error("openai package not installed. Run: pip install openai")
            raise RuntimeError("openai package required for OpenAI provider")
        
        api_key = CFG.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        
        client = OpenAI(api_key=api_key)
        
        try:
            resp = client.chat.completions.create(
                model=CFG.openai_model,
                messages=messages,
                temperature=CFG.temperature,
                max_tokens=CFG.max_tokens
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            log.error(f"OpenAI chat error: {e}")
            return f"Error: {str(e)}"


# Global LLM connector instance
llm = LLMConnector()

