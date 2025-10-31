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


def create_placeholder_thumbnail(name: str, fabric: str, output_path: Path) -> bool:
    """
    Generate a placeholder thumbnail for a garment.
    
    Args:
        name: Garment name
        fabric: Fabric type
        output_path: Where to save the thumbnail
    
    Returns:
        bool: Success status
    """
    try:
        # Create a simple placeholder image
        img = Image.new('RGB', (400, 500), color=FABRIC_PRESETS.get(fabric.lower(), {}).get("color", "#CCCCCC"))
        draw = ImageDraw.Draw(img)
        
        # Try to use a nice font, fallback to default
        try:
            font_large = ImageFont.truetype("arial.ttf", 32)
            font_small = ImageFont.truetype("arial.ttf", 20)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw garment name
        draw.text((20, 20), name, fill="#333333", font=font_large)
        draw.text((20, 60), f"Fabric: {fabric.title()}", fill="#666666", font=font_small)
        draw.text((20, 90), "Ready for CLO Import", fill="#999999", font=font_small)
        
        # Draw a simple garment silhouette (rectangle as placeholder)
        draw.rectangle([100, 150, 300, 450], outline="#333333", width=3)
        
        # Save
        img.save(output_path)
        return True
        
    except Exception as e:
        print(f"Warning: Could not create thumbnail: {e}")
        return False


def generate_garment(
    name: str,
    fabric: str = "cotton",
    style: str = "casual",
    color: Optional[str] = None,
    notes: Optional[str] = None
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
            
            # Inject custom metadata
            garment_data["project_name"] = name
            if "garments" in garment_data and len(garment_data["garments"]) > 0:
                garment_data["garments"][0]["name"] = name
                garment_data["garments"][0]["fabric"] = fabric
                garment_data["garments"][0]["style"] = style
                if color:
                    garment_data["garments"][0]["color"] = color
                if notes:
                    garment_data["garments"][0]["notes"] = notes
            
            garment_data["metadata"] = {
                "generator": "RAGGITY ZYZTEM 2.0",
                "generated_at": timestamp,
                "fabric_preset": FABRIC_PRESETS[fabric],
                "custom_color": color,
                "user_notes": notes
            }
            
            # Save updated file
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(garment_data, f, indent=2)
                
        except Exception as e:
            print(f"Warning: Could not update garment metadata: {e}")
        
        # Generate thumbnail
        thumbnail_created = create_placeholder_thumbnail(name, fabric, thumbnail_path)
        
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

