"""
Garment Generator - File-based CLO asset creation
Generates CLO-ready garment files without requiring live CLO connection.

This module provides a safe, file-based workflow for creating garments that can be
imported into CLO 3D, replacing the fragile socket-based listener approach.

Usage:
    from modules.garment_generator import generate_garment, list_generated_garments
    
    result = generate_garment(name="Summer Dress", fabric="Cotton", style="casual")
    garments = list_generated_garments()
"""

import os
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from PIL import Image, ImageDraw, ImageFont

# Import LLM for prompt interpretation
try:
    from core.llm_connector import llm
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    print("Warning: LLM connector not available. AI prompt interpretation disabled.")

# TODO: Future integration with CLO CLI or SDK
# When CLO provides a command-line interface or Python SDK, integrate here
# Example: subprocess.run(["clo-cli", "generate", "--template", "dress", "--output", path])

# Base paths
BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates" / "garments"
EXPORTS_DIR = BASE_DIR / "exports" / "garments"
THUMBNAILS_DIR = EXPORTS_DIR / "thumbnails"

# Fabric presets
FABRIC_PRESETS = {
    "cotton": {"weight": 200, "stretch": 0.1, "color": "#F5F5DC"},
    "linen": {"weight": 180, "stretch": 0.05, "color": "#FAF0E6"},
    "silk": {"weight": 120, "stretch": 0.15, "color": "#FFF8DC"},
    "denim": {"weight": 350, "stretch": 0.2, "color": "#4682B4"},
    "leather": {"weight": 800, "stretch": 0.05, "color": "#8B4513"},
    "wool": {"weight": 300, "stretch": 0.1, "color": "#D2B48C"},
    "polyester": {"weight": 150, "stretch": 0.3, "color": "#E0E0E0"},
}

# Garment style templates
STYLE_TEMPLATES = {
    "tshirt": "tshirt_base.zprj",
    "shirt": "shirt_base.zprj",
    "dress": "dress_base.zprj",
    "pants": "pants_base.zprj",
    "jacket": "jacket_base.zprj",
}

# Garment type aliases
GARMENT_TYPES = {
    "casual": "tshirt",
    "formal": "shirt",
    "dress": "dress",
    "pants": "pants",
    "jacket": "jacket"
}


def ensure_directories():
    """Create required directories if they don't exist"""
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    THUMBNAILS_DIR.mkdir(parents=True, exist_ok=True)


def interpret_garment_prompt(prompt: str) -> Dict:
    """
    Use AI to interpret a natural language garment description.
    
    Args:
        prompt: User's natural language description (e.g., "a casual summer dress in light blue cotton")
    
    Returns:
        dict: {
            "success": bool,
            "name": str,
            "fabric": str,
            "style": str,
            "color": str or None,
            "notes": str or None,
            "error": str (if success=False)
        }
    """
    if not LLM_AVAILABLE:
        return {
            "success": False,
            "error": "LLM not available. Please ensure Ollama is running."
        }
    
    try:
        # Create a structured prompt for the LLM with enhanced pattern/detail extraction
        system_prompt = """You are an expert fashion design assistant. Parse detailed garment descriptions into structured data for CLO 3D garment generation.

Available fabric types: cotton, linen, silk, denim, leather, wool, polyester
Available styles: tshirt, shirt, dress, pants, jacket

Extract ALL of these fields from the user's description:
- name: A descriptive name capturing the essence (e.g., "Striped Summer T-Shirt")
- fabric: One of the available fabric types (default: cotton)
- style: One of the available styles
- base_color: Primary/base hex color code (e.g., "#000000" for black)
- secondary_color: Secondary color for patterns/accents (hex or null)
- accent_color: Accent/trim color (hex or null)
- pattern: Pattern type (stripe, polka_dot, floral, geometric, solid, plaid, checkered, animal_print, abstract, null)
- pattern_details: Detailed pattern description (e.g., "horizontal white stripes, 1cm width, 5cm spacing")
- texture: Surface texture (smooth, ribbed, textured, knit, woven, embossed, null)
- embellishments: Any special details (buttons, zippers, pockets, embroidery, sequins, studs, patches, null)
- fit: Garment fit (slim, regular, loose, oversized, fitted, null)
- length: Garment length (short, regular, long, cropped, midi, maxi, null)
- neckline: Neckline style for tops/dresses (crew, v-neck, scoop, boat, high, turtle, null)
- sleeves: Sleeve details (short, long, sleeveless, 3/4, capped, puff, null)
- design_notes: Comprehensive design specifications and construction details

Be VERY detailed in pattern_details and design_notes. Extract every design element mentioned.

Respond ONLY with valid JSON in this exact format:
{
  "name": "string",
  "fabric": "string",
  "style": "string",
  "base_color": "#HEXCODE",
  "secondary_color": "#HEXCODE or null",
  "accent_color": "#HEXCODE or null",
  "pattern": "pattern_type or null",
  "pattern_details": "detailed description or null",
  "texture": "texture_type or null",
  "embellishments": "comma-separated list or null",
  "fit": "fit_type or null",
  "length": "length_type or null",
  "neckline": "neckline_type or null",
  "sleeves": "sleeve_type or null",
  "design_notes": "comprehensive design specifications"
}

Example for "black t-shirt with white stripes":
{
  "name": "Striped Black T-Shirt",
  "fabric": "cotton",
  "style": "tshirt",
  "base_color": "#000000",
  "secondary_color": "#FFFFFF",
  "accent_color": null,
  "pattern": "stripe",
  "pattern_details": "horizontal white stripes, evenly spaced, modern casual style",
  "texture": "smooth",
  "embellishments": null,
  "fit": "regular",
  "length": "regular",
  "neckline": "crew",
  "sleeves": "short",
  "design_notes": "Classic striped t-shirt with black base and white horizontal stripes. Clean, modern aesthetic suitable for casual wear."
}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Parse this garment description: {prompt}"}
        ]
        
        # Get LLM response
        response = llm.chat(messages)
        
        # Try to extract JSON from response
        # Sometimes LLMs wrap JSON in markdown code blocks
        response = response.strip()
        if response.startswith("```"):
            # Extract JSON from code block
            lines = response.split("\n")
            json_lines = []
            in_code = False
            for line in lines:
                if line.startswith("```"):
                    in_code = not in_code
                    continue
                if in_code or (not line.startswith("```") and "{" in line or "}" in line or "\"" in line):
                    json_lines.append(line)
            response = "\n".join(json_lines)
        
        # Try to find JSON object if response has extra text
        if not response.startswith("{"):
            # Look for the first { and last }
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                response = response[start:end]
        
        # Parse JSON response
        try:
            parsed = json.loads(response)
        except json.JSONDecodeError as e:
            # Try to fix common JSON issues
            # Remove trailing commas
            response = response.replace(",}", "}").replace(",]", "]")
            # Try again
            try:
                parsed = json.loads(response)
            except json.JSONDecodeError:
                # Last resort: return partial data with defaults
                return {
                    "success": False,
                    "error": f"Failed to parse LLM response as valid JSON: {str(e)}",
                    "raw_response": response[:500]
                }
        
        # Helper function to clean null strings
        def clean_field(value):
            if value is None:
                return None
            value_str = str(value).strip()
            if value_str.lower() == "null" or "or null" in value_str.lower():
                if "#" in value_str:
                    return value_str.split("or")[0].strip()
                return None
            return value if value else None
        
        # Validate and normalize (with null safety)
        fabric = parsed.get("fabric") or "cotton"
        if fabric:
            fabric = str(fabric).lower()
        else:
            fabric = "cotton"
            
        style = parsed.get("style") or "tshirt"
        if style:
            style = str(style).lower()
        else:
            style = "tshirt"
        
        # Clean up all color fields
        base_color = clean_field(parsed.get("base_color"))
        secondary_color = clean_field(parsed.get("secondary_color"))
        accent_color = clean_field(parsed.get("accent_color"))
        
        # Validate hex format for colors
        def validate_color(color):
            if color and color.startswith("#") and len(color) in [4, 7]:
                return color
            return None
        
        base_color = validate_color(base_color)
        secondary_color = validate_color(secondary_color)
        accent_color = validate_color(accent_color)
        
        # Clean up text fields
        pattern = clean_field(parsed.get("pattern"))
        pattern_details = clean_field(parsed.get("pattern_details"))
        texture = clean_field(parsed.get("texture"))
        embellishments = clean_field(parsed.get("embellishments"))
        fit = clean_field(parsed.get("fit"))
        length = clean_field(parsed.get("length"))
        neckline = clean_field(parsed.get("neckline"))
        sleeves = clean_field(parsed.get("sleeves"))
        design_notes = clean_field(parsed.get("design_notes"))
        
        # Validate fabric
        if fabric not in FABRIC_PRESETS:
            fabric = "cotton"  # Default fallback
        
        # Validate style  
        if style not in STYLE_TEMPLATES:
            # Try to map common terms
            style_mapping = {
                "t-shirt": "tshirt",
                "top": "tshirt",
                "blouse": "shirt",
                "trousers": "pants",
                "jeans": "pants",
                "coat": "jacket"
            }
            style = style_mapping.get(style, "tshirt")
        
        return {
            "success": True,
            "name": parsed.get("name", "Custom Garment"),
            "fabric": fabric,
            "style": style,
            "base_color": base_color,
            "secondary_color": secondary_color,
            "accent_color": accent_color,
            "pattern": pattern,
            "pattern_details": pattern_details,
            "texture": texture,
            "embellishments": embellishments,
            "fit": fit,
            "length": length,
            "neckline": neckline,
            "sleeves": sleeves,
            "design_notes": design_notes,
            # Legacy color field for backwards compatibility
            "color": base_color,
            "notes": design_notes
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Failed to parse LLM response as JSON: {str(e)}",
            "raw_response": response if 'response' in locals() else None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"AI interpretation failed: {str(e)}"
        }


def create_placeholder_thumbnail(
    name: str, 
    fabric: str, 
    output_path: Path,
    base_color: Optional[str] = None,
    secondary_color: Optional[str] = None,
    pattern: Optional[str] = None,
    pattern_details: Optional[str] = None,
    style: str = "tshirt"
) -> bool:
    """
    Generate an enhanced thumbnail for a garment with pattern visualization.
    
    Args:
        name: Garment name
        fabric: Fabric type
        output_path: Where to save the thumbnail
        base_color: Base color hex code
        secondary_color: Secondary color for patterns
        pattern: Pattern type (stripe, polka_dot, etc.)
        pattern_details: Detailed pattern description
    
    Returns:
        bool: Success status
    """
    try:
        import random
        
        # Get colors
        base = base_color or FABRIC_PRESETS.get(fabric.lower(), {}).get("color", "#CCCCCC")
        secondary = secondary_color or "#FFFFFF"
        
        # Convert hex to RGB
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip('#')
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])
            try:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            except:
                return (200, 200, 200)
        
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(*rgb)
        
        def blend_color(color, amount=0.8):
            """Lighten or darken a color"""
            r, g, b = color
            return (int(r * amount), int(g * amount), int(b * amount))
        
        base_rgb = hex_to_rgb(base)
        secondary_rgb = hex_to_rgb(secondary) if secondary else (255, 255, 255)
        
        # Create high-res image
        img = Image.new('RGB', (500, 600), color=(250, 250, 250))
        draw = ImageDraw.Draw(img)
        
        # Define garment silhouettes based on style
        style = style.lower()
        
        if style == "tshirt":
            # T-shirt silhouette
            body = [(150, 180), (350, 180), (350, 420), (150, 420)]  # Body
            neck = [(220, 180), (280, 180), (270, 200), (230, 200)]  # Neckline
            left_sleeve = [(150, 180), (100, 220), (110, 260), (150, 240)]
            right_sleeve = [(350, 180), (400, 220), (390, 260), (350, 240)]
            garment_parts = [body, left_sleeve, right_sleeve]
            
        elif style == "shirt":
            # Button-up shirt
            body = [(160, 180), (340, 180), (340, 450), (160, 450)]
            collar = [(220, 170), (280, 170), (290, 190), (250, 200), (210, 190)]
            left_sleeve = [(160, 180), (120, 240), (130, 320), (160, 300)]
            right_sleeve = [(340, 180), (380, 240), (370, 320), (340, 300)]
            garment_parts = [body, collar, left_sleeve, right_sleeve]
            
        elif style == "dress":
            # Dress silhouette
            bodice = [(180, 180), (320, 180), (310, 320), (190, 320)]
            skirt = [(170, 320), (330, 320), (350, 520), (150, 520)]
            straps = [(180, 180), (190, 160), (200, 180)]  # Left strap
            straps2 = [(320, 180), (310, 160), (300, 180)]  # Right strap
            garment_parts = [bodice, skirt, straps, straps2]
            
        elif style == "pants":
            # Pants silhouette
            waist = [(160, 180), (340, 180), (340, 220), (160, 220)]
            left_leg = [(160, 220), (240, 220), (240, 520), (160, 520)]
            right_leg = [(260, 220), (340, 220), (340, 520), (260, 520)]
            garment_parts = [waist, left_leg, right_leg]
            
        elif style == "jacket":
            # Jacket silhouette
            body = [(170, 200), (330, 200), (340, 480), (160, 480)]
            collar = [(220, 190), (280, 190), (290, 210), (250, 220), (210, 210)]
            left_sleeve = [(170, 200), (130, 250), (140, 420), (170, 400)]
            right_sleeve = [(330, 200), (370, 250), (360, 420), (330, 400)]
            left_lapel = [(170, 200), (220, 250), (210, 350), (160, 300)]
            right_lapel = [(330, 200), (280, 250), (290, 350), (340, 300)]
            garment_parts = [body, collar, left_sleeve, right_sleeve]
        else:
            # Default rectangle
            garment_parts = [[(150, 180), (350, 180), (350, 480), (150, 480)]]
        
        # Create a temporary image for the pattern
        pattern_img = Image.new('RGBA', (500, 600), (0, 0, 0, 0))
        pattern_draw = ImageDraw.Draw(pattern_img)
        
        # Detect pattern type (fuzzy matching)
        pattern_type = None
        if pattern:
            pattern_lower = str(pattern).lower()
            if 'stripe' in pattern_lower or 'striped' in pattern_lower:
                if 'vertical' in pattern_lower:
                    pattern_type = 'vertical_stripe'
                else:
                    pattern_type = 'stripe'
            elif 'polka' in pattern_lower or 'dot' in pattern_lower:
                pattern_type = 'polka_dot'
            elif 'check' in pattern_lower or 'plaid' in pattern_lower:
                pattern_type = 'checkered'
            elif 'floral' in pattern_lower or 'flower' in pattern_lower:
                pattern_type = 'floral'
            elif 'geometric' in pattern_lower or 'diagonal' in pattern_lower:
                pattern_type = 'geometric'
            else:
                pattern_type = 'stripe'  # Default
        
        # Fill garment with base color and patterns
        for part in garment_parts:
            # Draw base garment part
            pattern_draw.polygon(part, fill=base_rgb + (255,))
            
            # Add pattern overlay if specified
            if pattern_type and secondary:
                # Get bounding box of the part
                xs = [p[0] for p in part]
                ys = [p[1] for p in part]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                
                if pattern_type == 'stripe':
                    # Horizontal stripes
                    stripe_height = 20
                    for y in range(min_y, max_y, stripe_height * 2):
                        pattern_draw.rectangle(
                            [min_x, y, max_x, y + stripe_height], 
                            fill=secondary_rgb + (255,)
                        )
                
                elif pattern_type == 'vertical_stripe':
                    # Vertical stripes
                    stripe_width = 15
                    for x in range(min_x, max_x, stripe_width * 2):
                        pattern_draw.rectangle(
                            [x, min_y, x + stripe_width, max_y], 
                            fill=secondary_rgb + (255,)
                        )
                
                elif pattern_type == 'polka_dot':
                    # Polka dots with proper seeding
                    random.seed(hash(name) % 1000)
                    dot_count = int((max_x - min_x) * (max_y - min_y) / 800)
                    for _ in range(dot_count):
                        x = random.randint(min_x + 10, max_x - 10)
                        y = random.randint(min_y + 10, max_y - 10)
                        radius = random.randint(4, 8)
                        pattern_draw.ellipse(
                            [x-radius, y-radius, x+radius, y+radius], 
                            fill=secondary_rgb + (255,)
                        )
                
                elif pattern_type == 'checkered':
                    # Checkered pattern
                    square_size = 30
                    for y in range(min_y, max_y, square_size):
                        for x in range(min_x, max_x, square_size):
                            if ((x - min_x) // square_size + (y - min_y) // square_size) % 2:
                                pattern_draw.rectangle(
                                    [x, y, x + square_size, y + square_size], 
                                    fill=secondary_rgb + (255,)
                                )
                
                elif pattern_type == 'floral':
                    # Simple floral pattern (small circles in clusters)
                    random.seed(hash(name) % 1000)
                    flower_count = int((max_x - min_x) * (max_y - min_y) / 1500)
                    for _ in range(flower_count):
                        cx = random.randint(min_x + 20, max_x - 20)
                        cy = random.randint(min_y + 20, max_y - 20)
                        # Center
                        pattern_draw.ellipse([cx-3, cy-3, cx+3, cy+3], fill=secondary_rgb + (255,))
                        # Petals
                        for angle in [0, 60, 120, 180, 240, 300]:
                            import math
                            px = cx + int(8 * math.cos(math.radians(angle)))
                            py = cy + int(8 * math.sin(math.radians(angle)))
                            pattern_draw.ellipse([px-4, py-4, px+4, py+4], fill=secondary_rgb + (200,))
                
                elif pattern_type == 'geometric':
                    # Diagonal lines
                    for i in range(-200, 500, 25):
                        pattern_draw.line(
                            [(min_x + i, min_y), (min_x + i + (max_y - min_y), max_y)], 
                            fill=secondary_rgb + (255,), 
                            width=2
                        )
            
            # Add subtle shading for depth
            shadow_color = blend_color(base_rgb, 0.7)
            pattern_draw.polygon(part, outline=shadow_color + (255,), width=2)
        
        # Paste pattern onto base image
        img.paste(pattern_img, (0, 0), pattern_img)
        draw = ImageDraw.Draw(img)
        
        # Try to use nice fonts
        try:
            font_large = ImageFont.truetype("arial.ttf", 24)
            font_medium = ImageFont.truetype("arial.ttf", 16)
            font_small = ImageFont.truetype("arial.ttf", 12)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw info panel with rounded corners
        info_bg = Image.new('RGBA', (500, 140), (0, 0, 0, 220))
        img.paste(info_bg, (0, 0), info_bg)
        
        # Draw garment info
        draw.text((20, 15), name[:35], fill="#FFFFFF", font=font_large)
        draw.text((20, 50), f"Fabric: {fabric.title()}", fill="#DDDDDD", font=font_medium)
        if pattern:
            clean_pattern = pattern.replace('_', ' ').title()
            draw.text((20, 75), f"Pattern: {clean_pattern}", fill="#DDDDDD", font=font_medium)
        draw.text((20, 100), f"Style: {style.title()}", fill="#AAAAAA", font=font_small)
        draw.text((20, 115), "CLO 3D Ready ✓", fill="#88FF88", font=font_small)
        
        # Add color swatches
        swatch_y = 20
        swatch_x = 400
        # Base color
        draw.rectangle([swatch_x, swatch_y, swatch_x + 30, swatch_y + 30], fill=base_rgb, outline=(255, 255, 255), width=2)
        # Secondary color if present
        if secondary_color:
            draw.rectangle([swatch_x + 35, swatch_y, swatch_x + 65, swatch_y + 30], fill=secondary_rgb, outline=(255, 255, 255), width=2)
        
        # Save at good quality
        img = img.resize((400, 480), Image.Resampling.LANCZOS)
        img.save(output_path, quality=95)
        return True
        
    except Exception as e:
        print(f"Warning: Could not create thumbnail: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_garment(
    name: str,
    fabric: str = "cotton",
    style: str = "casual",
    color: Optional[str] = None,
    notes: Optional[str] = None,
    # Enhanced design parameters
    base_color: Optional[str] = None,
    secondary_color: Optional[str] = None,
    accent_color: Optional[str] = None,
    pattern: Optional[str] = None,
    pattern_details: Optional[str] = None,
    texture: Optional[str] = None,
    embellishments: Optional[str] = None,
    fit: Optional[str] = None,
    length: Optional[str] = None,
    neckline: Optional[str] = None,
    sleeves: Optional[str] = None,
    design_notes: Optional[str] = None
) -> Dict:
    """
    Generate a CLO-ready garment file from a template.
    
    This function:
    1. Copies a base template from templates/garments/
    2. Injects metadata (name, fabric, color, etc.)
    3. Saves to exports/garments/
    4. Generates a thumbnail preview
    5. Returns metadata for UI display
    
    Args:
        name: Garment name (e.g., "Summer Dress")
        fabric: Fabric type (cotton, linen, silk, denim, leather, wool, polyester)
        style: Style template (casual, formal, dress, pants, jacket)
        color: Optional hex color override
        notes: Optional user notes
    
    Returns:
        dict: {
            "success": bool,
            "garment_id": str,
            "name": str,
            "fabric": str,
            "style": str,
            "export_path": str,
            "thumbnail_path": str,
            "timestamp": str,
            "metadata": dict
        }
    """
    try:
        ensure_directories()
        
        # Normalize inputs
        fabric = fabric.lower()
        style = style.lower()
        
        # Validate fabric
        if fabric not in FABRIC_PRESETS:
            return {
                "success": False,
                "error": f"Unknown fabric: {fabric}",
                "available_fabrics": list(FABRIC_PRESETS.keys())
            }
        
        # Validate style
        if style not in STYLE_TEMPLATES:
            return {
                "success": False,
                "error": f"Unknown style: {style}",
                "available_styles": list(STYLE_TEMPLATES.keys())
            }
        
        # Generate unique ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        garment_id = f"{name.replace(' ', '_')}_{timestamp}"
        safe_name = "".join(c for c in garment_id if c.isalnum() or c in "._-")
        
        # Template path
        template_name = STYLE_TEMPLATES[style]
        template_path = TEMPLATES_DIR / template_name
        
        # If template doesn't exist, create a placeholder
        if not template_path.exists():
            # Create a minimal .zprj placeholder (JSON format)
            placeholder_data = {
                "version": "7.0",
                "project_name": name,
                "garments": [{
                    "name": name,
                    "fabric": fabric,
                    "style": style,
                    "created": timestamp,
                    "note": "Generated by RAGGITY ZYZTEM - Import into CLO to edit"
                }],
                "metadata": {
                    "generator": "RAGGITY ZYZTEM 2.0",
                    "template": template_name,
                    "fabric_preset": FABRIC_PRESETS[fabric]
                }
            }
            
            # Save placeholder template
            template_path.parent.mkdir(parents=True, exist_ok=True)
            with open(template_path, 'w', encoding='utf-8') as f:
                json.dump(placeholder_data, f, indent=2)
        
        # Export paths
        export_filename = f"{safe_name}.zprj"
        export_path = EXPORTS_DIR / export_filename
        thumbnail_path = THUMBNAILS_DIR / f"{safe_name}.png"
        metadata_path = EXPORTS_DIR / f"{safe_name}.json"
        
        # Copy template to export location
        shutil.copy2(template_path, export_path)
        
        # Update the exported file with custom metadata
        try:
            with open(export_path, 'r', encoding='utf-8') as f:
                garment_data = json.load(f)
            
            # Use base_color if provided, otherwise fall back to color
            primary_color = base_color or color or FABRIC_PRESETS[fabric]["color"]
            
            # Inject custom metadata
            garment_data["project_name"] = name
            if "garments" in garment_data and len(garment_data["garments"]) > 0:
                garment_obj = garment_data["garments"][0]
                garment_obj["name"] = name
                garment_obj["fabric"] = fabric
                garment_obj["style"] = style
                garment_obj["color"] = primary_color
                garment_obj["base_color"] = base_color or primary_color
                
                # Add enhanced design fields
                if secondary_color:
                    garment_obj["secondary_color"] = secondary_color
                if accent_color:
                    garment_obj["accent_color"] = accent_color
                if pattern:
                    garment_obj["pattern"] = {
                        "type": pattern,
                        "details": pattern_details or f"{pattern} pattern",
                        "colors": [c for c in [base_color, secondary_color, accent_color] if c]
                    }
                if texture:
                    garment_obj["texture"] = texture
                if embellishments:
                    garment_obj["embellishments"] = embellishments.split(",") if isinstance(embellishments, str) else embellishments
                if fit:
                    garment_obj["fit"] = fit
                if length:
                    garment_obj["length"] = length
                if neckline:
                    garment_obj["neckline"] = neckline
                if sleeves:
                    garment_obj["sleeves"] = sleeves
                
                # Add comprehensive notes
                garment_obj["notes"] = notes or design_notes or ""
                garment_obj["design_specifications"] = {
                    "pattern_details": pattern_details,
                    "texture": texture,
                    "embellishments": embellishments,
                    "fit": fit,
                    "length": length,
                    "neckline": neckline,
                    "sleeves": sleeves,
                    "full_description": design_notes or notes
                }
            
            garment_data["metadata"] = {
                "generator": "RAGGITY ZYZTEM 2.0",
                "generated_at": timestamp,
                "fabric_preset": FABRIC_PRESETS[fabric],
                "colors": {
                    "base": base_color or color,
                    "secondary": secondary_color,
                    "accent": accent_color
                },
                "pattern": {
                    "type": pattern,
                    "details": pattern_details
                },
                "design_details": {
                    "texture": texture,
                    "embellishments": embellishments,
                    "fit": fit,
                    "length": length,
                    "neckline": neckline,
                    "sleeves": sleeves
                },
                "user_notes": design_notes or notes
            }
            
            # Save updated file
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(garment_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not update garment metadata: {e}")
        
        # Generate thumbnail with pattern visualization and garment silhouette
        thumbnail_created = create_placeholder_thumbnail(
            name, 
            fabric, 
            thumbnail_path,
            base_color=base_color or color,
            secondary_color=secondary_color,
            pattern=pattern,
            pattern_details=pattern_details,
            style=style
        )
        
        # Save metadata separately for quick listing
        metadata = {
            "garment_id": garment_id,
            "name": name,
            "fabric": fabric,
            "style": style,
            "color": color or FABRIC_PRESETS[fabric]["color"],
            "notes": notes,
            "timestamp": timestamp,
            "export_path": str(export_path),
            "thumbnail_path": str(thumbnail_path) if thumbnail_created else None,
            "file_size": export_path.stat().st_size if export_path.exists() else 0
        }
        
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            "success": True,
            "garment_id": garment_id,
            "name": name,
            "fabric": fabric,
            "style": style,
            "export_path": str(export_path),
            "thumbnail_path": str(thumbnail_path) if thumbnail_created else None,
            "timestamp": timestamp,
            "metadata": metadata
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "name": name
        }


def list_generated_garments() -> List[Dict]:
    """
    List all generated garments with their metadata.
    
    Returns:
        list: List of garment metadata dicts, sorted by timestamp (newest first)
    """
    try:
        ensure_directories()
        
        garments = []
        
        # Find all metadata files
        for metadata_file in EXPORTS_DIR.glob("*.json"):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    
                # Verify the .zprj file still exists
                export_path = Path(metadata.get("export_path", ""))
                if export_path.exists():
                    garments.append(metadata)
                    
            except Exception as e:
                print(f"Warning: Could not read metadata from {metadata_file}: {e}")
                continue
        
        # Sort by timestamp (newest first)
        garments.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return garments
        
    except Exception as e:
        print(f"Error listing garments: {e}")
        return []


def delete_garment(garment_id: str) -> Dict:
    """
    Delete a generated garment and its associated files.
    
    Args:
        garment_id: The garment ID to delete
    
    Returns:
        dict: {"success": bool, "message": str}
    """
    try:
        ensure_directories()
        
        # Find files matching this garment_id
        deleted_files = []
        
        for pattern in [f"*{garment_id}*.zprj", f"*{garment_id}*.json", f"*{garment_id}*.png"]:
            for file in EXPORTS_DIR.rglob(pattern):
                try:
                    file.unlink()
                    deleted_files.append(str(file))
                except Exception as e:
                    print(f"Warning: Could not delete {file}: {e}")
        
        if deleted_files:
            return {
                "success": True,
                "message": f"Deleted {len(deleted_files)} file(s)",
                "deleted_files": deleted_files
            }
        else:
            return {
                "success": False,
                "error": f"No files found for garment_id: {garment_id}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_fabric_presets() -> Dict:
    """Return available fabric presets"""
    return FABRIC_PRESETS.copy()


def get_style_templates() -> Dict:
    """Return available style templates"""
    return STYLE_TEMPLATES.copy()


# Initialize directories on import
ensure_directories()

