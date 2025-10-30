"""
CLO 3D Companion Module

Integration layer for CLO 3D garment design software.
Supports two modes:
- Mode A: External bridge with persistent TCP listener
- Mode B: Direct script generation and execution
"""

from .config import (
    CLO_HOST,
    CLO_PORT,
    CLO_TIMEOUT,
    CLO_SCRIPT_DIR,
    BRIDGE_ENABLED
)

__version__ = "1.0.0"
__all__ = [
    "CLO_HOST",
    "CLO_PORT",
    "CLO_TIMEOUT",
    "CLO_SCRIPT_DIR",
    "BRIDGE_ENABLED"
]
