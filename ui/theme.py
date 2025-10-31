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
STATUS_WARNING = STATUS_WARN  # Additional alias for compatibility
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


def heading(text_color=TEXT) -> dict:
    """
    Returns kwargs dict for heading labels
    
    Args:
        text_color: Optional text color (defaults to TEXT)
    
    Returns:
        Dict with font and text_color for **unpacking
    
    Example:
        label = ctk.CTkLabel(parent, text="Title", **heading())
    """
    return {
        "font": (FONT_FAMILY, FONT_SIZE_HEADING, FONT_WEIGHT_BOLD),
        "text_color": text_color
    }


def subheading(text_color=TEXT) -> dict:
    """
    Returns kwargs dict for subheading labels
    
    Args:
        text_color: Optional text color (defaults to TEXT)
    
    Returns:
        Dict with font and text_color for **unpacking
    """
    return {
        "font": (FONT_FAMILY, FONT_SIZE_SUBHEADING, FONT_WEIGHT_BOLD),
        "text_color": text_color
    }


def body(text_color=TEXT) -> dict:
    """
    Returns kwargs dict for body text labels
    
    Args:
        text_color: Optional text color (defaults to TEXT)
    
    Returns:
        Dict with font and text_color for **unpacking
    """
    return {
        "font": (FONT_FAMILY, FONT_SIZE_BODY),
        "text_color": text_color
    }


def mono(text_color=TEXT) -> dict:
    """
    Returns kwargs dict for monospace text (code, logs)
    
    Args:
        text_color: Optional text color (defaults to TEXT)
    
    Returns:
        Dict with font and text_color for **unpacking
    """
    return {
        "font": (FONT_FAMILY_MONO, FONT_SIZE_BODY),
        "text_color": text_color
    }


def small(text_color=TEXT) -> dict:
    """
    Returns kwargs dict for small text labels
    
    Args:
        text_color: Optional text color (defaults to TEXT)
    
    Returns:
        Dict with font and text_color for **unpacking
    """
    return {
        "font": (FONT_FAMILY, FONT_SIZE_SMALL),
        "text_color": text_color
    }


# ========== Font-Only Helpers (for widgets with custom text_color) ==========

def heading_font() -> tuple:
    """Returns just the font tuple for headings (no text_color)"""
    return (FONT_FAMILY, FONT_SIZE_HEADING, FONT_WEIGHT_BOLD)


def subheading_font() -> tuple:
    """Returns just the font tuple for subheadings (no text_color)"""
    return (FONT_FAMILY, FONT_SIZE_SUBHEADING, FONT_WEIGHT_BOLD)


def body_font() -> tuple:
    """Returns just the font tuple for body text (no text_color)"""
    return (FONT_FAMILY, FONT_SIZE_BODY)


def mono_font() -> tuple:
    """Returns just the font tuple for monospace text (no text_color)"""
    return (FONT_FAMILY_MONO, FONT_SIZE_BODY)


def small_font() -> tuple:
    """Returns just the font tuple for small text (no text_color)"""
    return (FONT_FAMILY, FONT_SIZE_SMALL)


# ========== Component Helpers ==========

class Card(ctk.CTkFrame):
    """
    Premium card component with elevated appearance
    
    Features:
        - Subtle shadow-style background
        - Rounded corners
        - Proper spacing
        - Optional title
    
    Example:
        card = Card(parent)
        card.pack(padx=20, pady=10, fill="both", expand=True)
        
        # With title
        card = Card(parent, title="My Card")
        
        label = ctk.CTkLabel(card, text="Content", **body())
        label.pack(pady=10)
    """
    
    def __init__(self, parent, title=None, **kwargs):
        # Extract title before passing to parent
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
        
        # Add optional title
        if title:
            title_label = ctk.CTkLabel(self, text=title, **subheading())
            title_label.pack(pady=(15, 10), padx=20, anchor="w")


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
    
    def set_success(self, text: str):
        """Convenience method for success status"""
        self.set_status("success", text)
    
    def set_error(self, text: str):
        """Convenience method for error status"""
        self.set_status("error", text)
    
    def set_warning(self, text: str):
        """Convenience method for warning status"""
        self.set_status("warning", text)
    
    def set_warn(self, text: str):
        """Alias for set_warning"""
        self.set_warning(text)
    
    def set_info(self, text: str):
        """Convenience method for info status"""
        self.set_status("info", text)


def apply_theme():
    """Apply dark theme to CustomTkinter"""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")


# ========== Usage Examples ==========
"""
Example 1: Premium Card with Typography

    card = Card(parent)
    card.pack(padx=20, pady=10, fill="both")
    
    title = ctk.CTkLabel(card, text="System Status", **heading())
    title.pack(pady=10)
    
    subtitle = ctk.CTkLabel(card, text="Live Metrics", **subheading())
    subtitle.pack(pady=5)
    
    content = ctk.CTkLabel(card, text="CPU: 45.2%", **body())
    content.pack(pady=5)
    
    # With custom colors
    warning_text = ctk.CTkLabel(card, text="Warning", **body(STATUS_WARN))
    warning_text.pack(pady=5)

Example 2: Status Indicators

    status = StatusLabel(parent, status="ok", text="✓ Connected")
    status.pack()
    
    # Later update
    status.set_status("error", "✗ Disconnected")

Example 3: Color-coded Components

    # Success button
    btn = ctk.CTkButton(parent, text="Submit", fg_color=SUCCESS)
    
    # Warning label
    label = ctk.CTkLabel(parent, text="Warning!", **body(WARNING))
    
    # Error message
    error = ctk.CTkLabel(parent, text="Failed!", **body(ERROR))
"""
