"""
UI Theme Configuration
Premium dark theme with typography helpers and status colors
"""

import customtkinter as ctk


# ========== Premium Color Palette ==========

# Base theme colors
DARK_BG = "#0e0e10"          # Darkest background
LIGHT_BG = "#1b1b1f"         # Panel/card background
CARD_BG = "#242429"          # Elevated card background
ACCENT = "#5ac8fa"           # Primary accent (blue)
ACCENT_HOVER = "#6fd5ff"     # Accent hover state
TEXT = "#f0f0f0"             # Primary text (near white)
TEXT_SECONDARY = "#9a9a9a"   # Secondary text (muted)
BORDER = "#2d2d32"           # Subtle borders

# Status colors
STATUS_OK = "#4ade80"        # Green (success)
STATUS_WARN = "#fbbf24"      # Yellow (warning)
STATUS_ERROR = "#ef4444"     # Red (error)
STATUS_INFO = "#60a5fa"      # Blue (info)

# Semantic colors
SUCCESS = STATUS_OK
WARNING = STATUS_WARN
ERROR = STATUS_ERROR
INFO = STATUS_INFO


# ========== Typography ==========

# Font families
FONT_FAMILY = "Segoe UI"
FONT_FAMILY_MONO = "Consolas"

# Font sizes
FONT_SIZE_HEADING = 20
FONT_SIZE_SUBHEADING = 16
FONT_SIZE_BODY = 13
FONT_SIZE_SMALL = 11

# Font weights
FONT_WEIGHT_BOLD = "bold"
FONT_WEIGHT_NORMAL = "normal"


def heading() -> tuple:
    """
    Returns font tuple for headings
    
    Returns:
        Tuple of (family, size, weight)
    
    Example:
        label = ctk.CTkLabel(parent, text="Title", font=heading())
    """
    return (FONT_FAMILY, FONT_SIZE_HEADING, FONT_WEIGHT_BOLD)


def subheading() -> tuple:
    """
    Returns font tuple for subheadings
    
    Returns:
        Tuple of (family, size, weight)
    """
    return (FONT_FAMILY, FONT_SIZE_SUBHEADING, FONT_WEIGHT_BOLD)


def body() -> tuple:
    """
    Returns font tuple for body text
    
    Returns:
        Tuple of (family, size)
    """
    return (FONT_FAMILY, FONT_SIZE_BODY)


def mono() -> tuple:
    """
    Returns font tuple for monospace text (code, logs)
    
    Returns:
        Tuple of (family, size)
    """
    return (FONT_FAMILY_MONO, FONT_SIZE_BODY)


def small() -> tuple:
    """
    Returns font tuple for small text
    
    Returns:
        Tuple of (family, size)
    """
    return (FONT_FAMILY, FONT_SIZE_SMALL)


# ========== Component Helpers ==========

class Card(ctk.CTkFrame):
    """
    Premium card component with elevated appearance
    
    Features:
        - Subtle shadow-style background
        - Rounded corners
        - Proper spacing
    
    Example:
        card = Card(parent)
        card.pack(padx=20, pady=10, fill="both", expand=True)
        
        label = ctk.CTkLabel(card, text="Content", font=body())
        label.pack(pady=10)
    """
    
    def __init__(self, parent, **kwargs):
        # Default card styling
        defaults = {
            "fg_color": CARD_BG,
            "corner_radius": 10,
            "border_width": 1,
            "border_color": BORDER
        }
        
        # Override with user kwargs
        defaults.update(kwargs)
        
        super().__init__(parent, **defaults)


class StatusLabel(ctk.CTkLabel):
    """
    Status label with color-coded text
    
    Example:
        status = StatusLabel(parent, status="ok", text="Connected")
        status.pack()
        
        # Update status
        status.set_status("error", "Disconnected")
    """
    
    def __init__(self, parent, status="info", **kwargs):
        super().__init__(parent, **kwargs)
        self.set_status(status)
    
    def set_status(self, status: str, text: str = None):
        """
        Set status color and optional text
        
        Args:
            status: One of "ok", "warn", "error", "info"
            text: Optional text to display
        """
        color_map = {
            "ok": STATUS_OK,
            "success": STATUS_OK,
            "warn": STATUS_WARN,
            "warning": STATUS_WARN,
            "error": STATUS_ERROR,
            "info": STATUS_INFO
        }
        
        color = color_map.get(status.lower(), TEXT_SECONDARY)
        self.configure(text_color=color)
        
        if text:
            self.configure(text=text)


def apply_theme():
    """Apply dark theme to CustomTkinter"""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


# ========== Usage Examples ==========
"""
Example 1: Premium Card with Typography

    card = Card(parent)
    card.pack(padx=20, pady=10, fill="both")
    
    title = ctk.CTkLabel(card, text="System Status", font=heading())
    title.pack(pady=10)
    
    subtitle = ctk.CTkLabel(card, text="Live Metrics", font=subheading())
    subtitle.pack(pady=5)
    
    content = ctk.CTkLabel(card, text="CPU: 45.2%", font=body())
    content.pack(pady=5)

Example 2: Status Indicators

    status = StatusLabel(parent, status="ok", text="✓ Connected")
    status.pack()
    
    # Later update
    status.set_status("error", "✗ Disconnected")

Example 3: Color-coded Components

    # Success button
    btn = ctk.CTkButton(parent, text="Submit", fg_color=SUCCESS)
    
    # Warning label
    label = ctk.CTkLabel(parent, text="Warning!", text_color=WARNING)
    
    # Error message
    error = ctk.CTkLabel(parent, text="Failed!", text_color=ERROR)
"""
