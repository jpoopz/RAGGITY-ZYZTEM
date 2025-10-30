"""
Garment Editor - Edits OBJ files based on structured edit commands
Uses trimesh for mesh manipulation
"""

import os
import sys
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
except ImportError:
    def log(msg, category="CLO"):
        print(f"[{category}] {msg}")

# Try importing trimesh (required for mesh editing)
try:
    import trimesh
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False
    trimesh = None
    log("trimesh not available - garment editing will be limited", "CLO", level="WARNING")

class GarmentEditor:
    """Edits garment OBJ files based on structured commands"""
    
    def __init__(self, output_dir: Optional[str] = None):
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "outputs")
        
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        log("GarmentEditor initialized", "CLO")
    
    def load_obj(self, file_path: str) -> Optional[object]:
        """Load OBJ file using trimesh"""
        if not TRIMESH_AVAILABLE:
            log("Cannot load OBJ: trimesh not available", "CLO", level="ERROR")
            return None
        
        try:
            if os.path.exists(file_path):
                mesh = trimesh.load(file_path, file_type='obj')
                log(f"Loaded OBJ: {os.path.basename(file_path)} ({len(mesh.vertices)} vertices)", "CLO")
                return mesh
            else:
                log(f"OBJ file not found: {file_path}", "CLO", level="ERROR")
                return None
        except Exception as e:
            log(f"Error loading OBJ: {e}", "CLO", level="ERROR")
            return None
    
    def apply_transformations(self, mesh, edit_commands: List[Dict]) -> bool:
        """
        Apply transformations to mesh based on edit commands
        
        Args:
            mesh: trimesh mesh object
            edit_commands: List of command dicts with action/value
        
        Returns:
            True if successful
        """
        if not TRIMESH_AVAILABLE or mesh is None:
            return False
        
        try:
            for cmd in edit_commands:
                action = cmd.get("action", "")
                value = cmd.get("value", "")
                unit = cmd.get("unit", "cm")
                
                if action == "adjust_sleeve_length":
                    self._adjust_sleeve_length(mesh, value, unit)
                elif action == "adjust_hem_length":
                    self._adjust_hem_length(mesh, value, unit)
                elif action == "adjust_width":
                    self._adjust_width(mesh, value, unit)
                elif action == "adjust_length":
                    self._adjust_length(mesh, value, unit)
                elif action == "change_color":
                    # Color change doesn't modify mesh, just MTL
                    log(f"Color change detected: {value} (will update MTL separately)", "CLO")
                elif action == "change_material":
                    # Material change updates MTL
                    log(f"Material change detected: {value} (will update MTL separately)", "CLO")
                elif action == "adjust_fit":
                    # Generic fit adjustment
                    self._adjust_fit(mesh, value)
                else:
                    log(f"Unknown action: {action}", "CLO", level="WARNING")
            
            log(f"Applied {len(edit_commands)} transformations", "CLO")
            return True
            
        except Exception as e:
            log(f"Error applying transformations: {e}", "CLO", level="ERROR")
            return False
    
    def _adjust_sleeve_length(self, mesh, value: str, unit: str):
        """Adjust sleeve length by scaling Y-axis for sleeve vertices"""
        try:
            # Parse value (e.g., "+2.5", "-1.0")
            numeric_value = float(value)
            
            # Find sleeve vertices (rough heuristic: vertices with high Y and X near edges)
            # This is simplified - real implementation would need vertex grouping
            vertices = mesh.vertices.copy()
            
            # Scale sleeve region (vertices on sides, upper portion)
            # Assume sleeves are in regions with |X| > 0.4 and Y > 0.5
            for i, vertex in enumerate(vertices):
                if abs(vertex[0]) > 0.4 and vertex[1] > 0.5:  # Sleeve region heuristic
                    # Extend/contract along Y axis
                    scale_factor = 1.0 + (numeric_value / 10.0)  # Normalize
                    vertices[i][1] *= scale_factor
            
            mesh.vertices = vertices
            log(f"Adjusted sleeve length by {numeric_value}{unit}", "CLO")
            
        except Exception as e:
            log(f"Error adjusting sleeve length: {e}", "CLO", level="ERROR")
    
    def _adjust_hem_length(self, mesh, value: str, unit: str):
        """Adjust hem length by scaling Y-axis for bottom vertices"""
        try:
            numeric_value = float(value)
            vertices = mesh.vertices.copy()
            
            # Bottom region: low Y values
            for i, vertex in enumerate(vertices):
                if vertex[1] < 0.5:  # Lower portion
                    scale_factor = 1.0 + (numeric_value / 10.0)
                    vertices[i][1] *= scale_factor
            
            mesh.vertices = vertices
            log(f"Adjusted hem length by {numeric_value}{unit}", "CLO")
            
        except Exception as e:
            log(f"Error adjusting hem length: {e}", "CLO", level="ERROR")
    
    def _adjust_width(self, mesh, value: str, unit: str):
        """Adjust width by scaling X-axis"""
        try:
            numeric_value = float(value)
            scale_factor = 1.0 + (numeric_value / 100.0)  # Percentage-based
            
            mesh.apply_scale([scale_factor, 1.0, 1.0])
            log(f"Adjusted width by {numeric_value}{unit}", "CLO")
            
        except Exception as e:
            log(f"Error adjusting width: {e}", "CLO", level="ERROR")
    
    def _adjust_length(self, mesh, value: str, unit: str):
        """Adjust length by scaling Y-axis"""
        try:
            numeric_value = float(value)
            scale_factor = 1.0 + (numeric_value / 100.0)
            
            mesh.apply_scale([1.0, scale_factor, 1.0])
            log(f"Adjusted length by {numeric_value}{unit}", "CLO")
            
        except Exception as e:
            log(f"Error adjusting length: {e}", "CLO", level="ERROR")
    
    def _adjust_fit(self, mesh, value: str):
        """Generic fit adjustment (oversized/fitted)"""
        value_lower = value.lower()
        
        if "oversized" in value_lower or "larger" in value_lower or "bigger" in value_lower:
            mesh.apply_scale(1.1)  # 10% larger
            log("Applied oversized fit adjustment", "CLO")
        elif "fitted" in value_lower or "tighter" in value_lower or "smaller" in value_lower:
            mesh.apply_scale(0.9)  # 10% smaller
            log("Applied fitted/tight fit adjustment", "CLO")
    
    def save_new_version(self, mesh, base_path: str, version: int, 
                        original_metadata: Optional[Dict] = None) -> Dict[str, str]:
        """
        Save new version of garment
        
        Args:
            mesh: Modified trimesh mesh
            base_path: Original OBJ file path
            version: Version number (2, 3, etc.)
            original_metadata: Original metadata dict
        
        Returns:
            Dict with paths to new files
        """
        try:
            # Generate new filename
            base_name = os.path.splitext(os.path.basename(base_path))[0]
            # Remove existing version suffix if present
            base_name = re.sub(r'_v\d+$', '', base_name)
            
            new_filename = f"{base_name}_v{version}"
            new_obj_path = os.path.join(self.output_dir, f"{new_filename}.obj")
            new_mtl_path = os.path.join(self.output_dir, f"{new_filename}.mtl")
            new_metadata_path = os.path.join(self.output_dir, f"{new_filename}_metadata.json")
            preview_dir = os.path.join(self.output_dir, "previews")
            os.makedirs(preview_dir, exist_ok=True)
            new_preview_path = os.path.join(preview_dir, f"{new_filename}_preview.png")
            
            # Save OBJ
            if TRIMESH_AVAILABLE:
                mesh.export(new_obj_path, file_type='obj')
                log(f"Saved new version: {new_filename}.obj", "CLO")
            
            # Copy and update MTL if exists
            original_mtl_path = base_path.replace(".obj", ".mtl")
            if os.path.exists(original_mtl_path):
                # For now, just copy (color/material changes would update here)
                shutil.copy2(original_mtl_path, new_mtl_path)
                log(f"Copied MTL: {new_filename}.mtl", "CLO")
            
            # Update metadata
            metadata = original_metadata.copy() if original_metadata else {}
            metadata["version"] = version
            metadata["base_file"] = os.path.basename(base_path)
            metadata["edit_timestamp"] = __import__("datetime").datetime.now().isoformat()
            
            with open(new_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Generate preview
            try:
                from modules.clo_companion.garment_gen import GarmentGenerator
                generator = GarmentGenerator(self.output_dir)
                generator.generate_preview(new_obj_path, new_preview_path)
            except:
                pass  # Preview optional
            
            return {
                "obj_file": new_obj_path,
                "mtl_file": new_mtl_path,
                "metadata_file": new_metadata_path,
                "preview_file": new_preview_path if os.path.exists(new_preview_path) else None,
                "base_name": new_filename
            }
            
        except Exception as e:
            log(f"Error saving new version: {e}", "CLO", level="ERROR")
            return {}
    
    def apply_edit(self, model_path: str, feedback_text: str, 
                   edit_commands: List[Dict], version: int = 2) -> Optional[Dict[str, str]]:
        """
        Main function: Load, edit, save new version
        
        Args:
            model_path: Path to original OBJ
            feedback_text: Original user feedback
            edit_commands: Parsed edit commands
            version: Version number for new file
        
        Returns:
            Dict with paths to new files, or None if failed
        """
        try:
            # Load mesh
            mesh = self.load_obj(model_path)
            if mesh is None:
                log("Failed to load mesh for editing", "CLO", level="ERROR")
                return None
            
            # Apply transformations
            success = self.apply_transformations(mesh, edit_commands)
            if not success:
                log("Failed to apply transformations", "CLO", level="ERROR")
                return None
            
            # Load original metadata if exists
            metadata_path = model_path.replace(".obj", "_metadata.json")
            original_metadata = None
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    original_metadata = json.load(f)
            
            # Save new version
            result = self.save_new_version(mesh, model_path, version, original_metadata)
            
            if result:
                log(f"Successfully created version {version}: {result.get('base_name', 'unknown')}", "CLO")
                return result
            else:
                return None
                
        except Exception as e:
            log(f"Error in apply_edit: {e}", "CLO", level="ERROR")
            return None

# Fix regex import
import re




