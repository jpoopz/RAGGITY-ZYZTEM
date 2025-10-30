"""
UI Theme Configuration
Reusable dark theme colors and settings for CustomTkinter
"""

import customtkinter as ctk


# Base theme colors
DARK_BG = "#0e0e10"
LIGHT_BG = "#1b1b1f"
ACCENT = "#5ac8fa"
TEXT = "#f0f0f0"
MUTED = "#9a9a9a"


def apply_theme():
    """Apply dark theme to CustomTkinter"""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

