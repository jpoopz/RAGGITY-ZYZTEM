"""
Path configuration and directory management
"""

import os
from pathlib import Path


# Base directory (project root)
BASE_DIR = Path(__file__).parent.parent.absolute()

# Data directories
DATA_DIR = BASE_DIR / "data"
VECTOR_DIR = BASE_DIR / "vector_store"
LOGS_DIR = BASE_DIR / "Logs"
CONFIG_DIR = BASE_DIR / "config"


def ensure_dirs():
    """Ensure all required directories exist"""
    for dir_path in [DATA_DIR, VECTOR_DIR, LOGS_DIR, CONFIG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)


def get_data_dir() -> str:
    """Get data directory path as string"""
    return str(DATA_DIR)


def get_vector_dir() -> str:
    """Get vector store directory path as string"""
    return str(VECTOR_DIR)


def get_logs_dir() -> str:
    """Get logs directory path as string"""
    return str(LOGS_DIR)


def get_config_dir() -> str:
    """Get config directory path as string"""
    return str(CONFIG_DIR)

