"""
Lightweight profiling utility for measuring execution time.

Usage:
    from core.prof import span
    
    with span("load_documents"):
        docs = load_documents(path)
    
    # Logs: [SPAN] load_documents took 123.4 ms
"""

import time
from contextlib import contextmanager
from .logger import get_logger

log = get_logger("prof")


@contextmanager
def span(name: str):
    """
    Context manager for timing code blocks.
    
    Args:
        name: Descriptive name for the span
    
    Usage:
        with span("expensive_operation"):
            do_expensive_work()
    """
    t0 = time.perf_counter()
    try:
        yield
    finally:
        dt = (time.perf_counter() - t0) * 1000  # Convert to milliseconds
        log.info(f"[SPAN] {name} took {dt:.1f} ms")

