"""
Render Engine - Lightweight preview generator for garments
Generates placeholder preview images without requiring CLO 3D.

This module creates visual previews of garments for the UI, allowing users
to see their designs before exporting to CLO.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import random
from typing import Dict, Optional

# Preview settings
PREVIEW_DIR = Path("exports/previews")
PREVIEW_SIZE = (512, 512)
PREVIEW_BG_COLORS = {
    "cotton": "#F5F5DC",
    "linen": "#FAF0E6", 
    "silk": "#FFF8DC",
    "denim": "#4682B4",
    "leather": "#8B4513",
    "wool": "#D2B48C",
    "polyester": "#E0E0E0",
    "default": "#CCCCCC"
}

# Garment silhouettes (simple shapes for previews)
GARMENT_SHAPES = {
    "tshirt": [
        # Body
        [(150, 200), (350, 200), (350, 450), (150, 450)],
        # Sleeves
        [(100, 200), (150, 200), (150, 280), (100, 280)],
        [(350, 200), (400, 200), (400, 280), (350, 280)],
        # Neckline
        [(220, 180), (280, 180), (280, 210), (220, 210)]
    ],
    "pants": [
        # Left leg
        [(180, 200), (240, 200), (240, 480), (180, 480)],
        # Right leg
        [(260, 200), (320, 200), (320, 480), (260, 480)],
        # Waistband
        [(180, 180), (320, 180), (320, 200), (180, 200)]
    ],
    "jacket": [
        # Body
        [(140, 200), (360, 200), (360, 420), (140, 420)],
        # Sleeves
        [(80, 200), (140, 200), (140, 300), (80, 300)],
        [(360, 200), (420, 200), (420, 300), (360, 300)],
        # Collar
        [(200, 180), (300, 180), (300, 210), (200, 210)],
        # Buttons
        [(245, 240), (255, 240), (255, 250), (245, 250)],
        [(245, 280), (255, 280), (255, 290), (245, 290)],
        [(245, 320), (255, 320), (255, 330), (245, 330)]
    ],
    "dress": [
        # Bodice
        [(180, 200), (320, 200), (320, 320), (180, 320)],
        # Skirt
        [(140, 320), (360, 320), (360, 480), (140, 480)],
        # Straps
        [(200, 180), (210, 180), (210, 200), (200, 200)],
        [(290, 180), (300, 180), (300, 200), (290, 200)]
    ],
    "shirt": [
        # Body
        [(150, 220), (350, 220), (350, 450), (150, 450)],
        # Sleeves
        [(100, 220), (150, 220), (150, 320), (100, 320)],
        [(350, 220), (400, 220), (400, 320), (350, 320)],
        # Collar
        [(200, 200), (300, 200), (300, 230), (200, 230)],
        # Button placket
        [(245, 240), (255, 240), (255, 440), (245, 440)]
    ]
}


def ensure_preview_dir():
    """Create preview directory if it doesn't exist"""
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)


def hex_to_rgb(hex_color: str) -> tuple:
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def darken_color(rgb: tuple, factor: float = 0.7) -> tuple:
    """Darken an RGB color by a factor"""
    return tuple(int(c * factor) for c in rgb)


def render_preview(garment_meta: Dict, output_path: Optional[str] = None) -> str:
    """
    Generate a preview image for a garment.
    
    Args:
        garment_meta: Dictionary with garment metadata
            - name: Garment name
            - type: Garment type (tshirt, pants, jacket, dress, shirt)
            - fabric: Fabric type
            - color: Optional hex color
        output_path: Optional custom output path
    
    Returns:
        str: Path to generated preview image
    """
    ensure_preview_dir()
    
    # Extract metadata
    name = garment_meta.get("name", "Untitled")
    garment_type = garment_meta.get("type", "tshirt").lower()
    fabric = garment_meta.get("fabric", "cotton").lower()
    custom_color = garment_meta.get("color")
    
    # Determine background color
    if custom_color:
        bg_color = custom_color
    else:
        bg_color = PREVIEW_BG_COLORS.get(fabric, PREVIEW_BG_COLORS["default"])
    
    # Create image
    img = Image.new("RGB", PREVIEW_SIZE, color="#F0F0F0")
    draw = ImageDraw.Draw(img)
    
    # Draw background panel
    draw.rectangle([20, 20, PREVIEW_SIZE[0]-20, PREVIEW_SIZE[1]-20], 
                   fill="#FFFFFF", outline="#CCCCCC", width=2)
    
    # Load font
    try:
        title_font = ImageFont.truetype("arial.ttf", 24)
        label_font = ImageFont.truetype("arial.ttf", 16)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw title
    draw.text((40, 40), name, fill="#333333", font=title_font)
    
    # Draw fabric info
    fabric_text = f"Fabric: {fabric.title()}"
    draw.text((40, 75), fabric_text, fill="#666666", font=label_font)
    
    # Draw garment type
    type_text = f"Type: {garment_type.title()}"
    draw.text((40, 100), type_text, fill="#666666", font=label_font)
    
    # Draw garment silhouette
    shapes = GARMENT_SHAPES.get(garment_type, GARMENT_SHAPES["tshirt"])
    base_rgb = hex_to_rgb(bg_color)
    outline_rgb = darken_color(base_rgb, 0.5)
    
    for shape in shapes:
        draw.polygon(shape, fill=bg_color, outline=outline_rgb)
    
    # Add subtle shadow effect
    shadow_offset = 3
    for shape in shapes:
        shadow_shape = [(x + shadow_offset, y + shadow_offset) for x, y in shape]
        draw.polygon(shadow_shape, fill="#00000020")
    
    # Draw watermark
    watermark = "RAGGITY ZYZTEM"
    draw.text((PREVIEW_SIZE[0] - 150, PREVIEW_SIZE[1] - 30), 
              watermark, fill="#CCCCCC", font=small_font)
    
    # Determine output path
    if output_path is None:
        safe_name = "".join(c for c in name if c.isalnum() or c in "._- ")
        output_path = str(PREVIEW_DIR / f"{safe_name}.png")
    
    # Save image
    img.save(output_path)
    
    return output_path


def render_batch_previews(garments: list) -> Dict[str, str]:
    """
    Render previews for multiple garments.
    
    Args:
        garments: List of garment metadata dicts
    
    Returns:
        dict: Mapping of garment names to preview paths
    """
    previews = {}
    
    for garment in garments:
        try:
            name = garment.get("name", "Untitled")
            path = render_preview(garment)
            previews[name] = path
        except Exception as e:
            print(f"Warning: Could not render preview for {name}: {e}")
            continue
    
    return previews


def clear_preview_cache():
    """Delete all cached preview images"""
    if PREVIEW_DIR.exists():
        for file in PREVIEW_DIR.glob("*.png"):
            try:
                file.unlink()
            except Exception as e:
                print(f"Warning: Could not delete {file}: {e}")

