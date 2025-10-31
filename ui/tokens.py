"""
Design tokens - Single source of truth for theme values.

Provides consistent colors, spacing, radii, and typography across the UI.
"""

# Color tokens (dark-first design system)
COLOR = {
    # Backgrounds (layered depth)
    "bg/0": "#0d0f12",      # Deepest background
    "bg/1": "#13161a",      # Mid-layer background
    "bg/2": "#1b1f24",      # Surface background
    "card": "#151a1f",      # Card/panel background
    "border": "#272c33",    # Borders and hairlines
    
    # Text
    "text": "#eef2f7",      # Primary text
    "muted": "#9aa3ad",     # Secondary/muted text
    
    # Brand
    "accent": "#5ac8fa",    # Primary accent color
    
    # Status colors
    "ok": "#2ecc71",        # Success/healthy state
    "warn": "#f1c40f",      # Warning state
    "error": "#e74c3c",     # Error/danger state
    "info": "#4da3ff",      # Info/neutral state
}

# Spacing scale (pixels)
# Usage: padding, margin, gap
SPACE = {
    "0": 0,
    "xs": 4,
    "sm": 8,
    "md": 12,
    "lg": 16,
    "xl": 24,
    "2xl": 32,
    "3xl": 48
}

# Border radius scale (pixels)
# Usage: corner_radius
RADIUS = {
    "sm": 6,
    "md": 10,
    "lg": 14,
    "xl": 18
}

# Typography tokens
# Each entry is (font_family, size, weight)
FONT = {
    "family": "Segoe UI",
    "family_mono": "Cascadia Mono",
    
    # Headings
    "h1": ("Segoe UI", 22, "bold"),
    "h2": ("Segoe UI", 18, "bold"),
    "h3": ("Segoe UI", 16, "bold"),
    
    # Body text
    "body": ("Segoe UI", 13, "normal"),
    "body-lg": ("Segoe UI", 14, "normal"),
    "body-sm": ("Segoe UI", 11, "normal"),
    
    # Monospace
    "mono": ("Cascadia Mono", 12, "normal"),
    "mono-sm": ("Cascadia Mono", 11, "normal"),
}


def token_usage_doc():
    """
    Design token usage guide:
    
    Colors:
    - Backgrounds: COLOR["bg/0"], COLOR["bg/1"], COLOR["bg/2"]
    - Cards: COLOR["card"]
    - Borders: COLOR["border"]
    - Text: COLOR["text"] (primary), COLOR["muted"] (secondary)
    - Status: COLOR["ok"], COLOR["warn"], COLOR["error"]
    
    Spacing:
    - Small gaps: SPACE["sm"] or SPACE["md"]
    - Major sections: SPACE["xl"] or SPACE["2xl"]
    - Card padding: SPACE["lg"]
    
    Radii:
    - Small components: RADIUS["sm"]
    - Cards/panels: RADIUS["lg"]
    - Large surfaces: RADIUS["xl"]
    
    Typography:
    - Section headers: FONT["h2"]
    - Body text: FONT["body"]
    - Code/logs: FONT["mono"]
    
    Example:
        card = ctk.CTkFrame(
            parent,
            fg_color=COLOR["card"],
            corner_radius=RADIUS["lg"]
        )
        card.pack(padx=SPACE["lg"], pady=SPACE["md"])
    """
    return True


# Density presets (multipliers for spacing)
DENSITY = {
    "Cozy": 1.25,       # More space, airier
    "Comfortable": 1.0,  # Default
    "Compact": 0.75     # Tighter, more content visible
}


def get_spacing(key: str, density: str = "Comfortable") -> int:
    """
    Get spacing value adjusted for density.
    
    Args:
        key: Spacing key from SPACE dict
        density: Density mode (Cozy, Comfortable, Compact)
    
    Returns:
        Adjusted spacing in pixels
    """
    base = SPACE.get(key, 0)
    multiplier = DENSITY.get(density, 1.0)
    return int(base * multiplier)


