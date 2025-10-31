import os
from typing import Optional
from pydantic import BaseModel

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


class Settings(BaseModel):
    APP_ENV: str = os.getenv("APP_ENV", "local")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    CLO_BRIDGE_PORT: int = int(os.getenv("CLO_BRIDGE_PORT", "9933"))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"


settings = Settings()


