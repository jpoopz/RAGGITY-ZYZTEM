"""
Citation formatting module using CSL (Citation Style Language).
"""

from .harvard import cite_from_dois, cite_text, render_bibliography, work_to_csl

__all__ = [
    "cite_from_dois",
    "cite_text", 
    "render_bibliography",
    "work_to_csl"
]

