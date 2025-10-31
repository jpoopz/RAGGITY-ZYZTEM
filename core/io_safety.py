"""
Safe I/O stream handling for GUI and background processes.

Prevents crashes when stdout/stderr are None (e.g., pythonw.exe on Windows).
"""

import sys


def safe_reconfigure_streams(encoding="utf-8"):
    """
    Safely reconfigure stdout and stderr encoding.
    
    Only reconfigures if the stream is a TextIOWrapper with .reconfigure() method.
    Safe to call in GUI mode (pythonw.exe) where streams may be None.
    
    Args:
        encoding: Target encoding (default: utf-8)
    """
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is None:
            continue
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding=encoding)
            except Exception:
                # Silently ignore errors (stream may not support reconfiguration)
                pass


def ensure_stream_encoding():
    """
    Convenience wrapper for safe_reconfigure_streams().
    Call this at the top of any script that may run in GUI mode.
    """
    safe_reconfigure_streams()

