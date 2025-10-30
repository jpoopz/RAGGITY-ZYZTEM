"""
Garment Generator - Procedural mesh generation from text prompts
Generates .obj + .mtl files with metadata for CLO3D import
"""

import os
import sys
import json
import random
import hashlib
from datetime import datetime
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

# Optional GPU support
try:
    import torch
    GPU_AVAILABLE = torch.cuda.is_available()
except ImportError:
    GPU_AVAILABLE = False
    torch = None

class GarmentGenerator:
    """Generates procedural garment meshes from text prompts"""
    
    def __init__(self, output_dir: Optional[str] = None):
        if output_dir is None:
            output_dir = os.path.join(os.path.dirname(__file__), "outputs")
        
        self.output_dir = output_dir
        self.preview_dir = os.path.join(output_dir, "previews")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.preview_dir, exist_ok=True)
        
        # Initialize render manager for dual-mode rendering
        try:
            from modules.clo_companion.render_manager import RenderManager
            self.render_manager = RenderManager()
        except Exception as e:
            log(f"Render manager not available: {e}", "CLO", level="WARNING")
            self.render_manager = None
        
        # Garment templates (procedural bases)
        self.templates = {
            "shirt": self._generate_shirt_template,
            "t-shirt": self._generate_tshirt_template,
            "pants": self._generate_pants_template,
            "coat": self._generate_coat_template,
            "jacket": self._generate_jacket_template,
            "trench": self._generate_trench_template,
            "dress": self._generate_dress_template,
            "skirt": self._generate_skirt_template
        }
        
        # Material library
        self.materials = {
            "cotton": {"kd": (0.9, 0.9, 0.9), "roughness": 0.7, "name": "Cotton"},
            "denim": {"kd": (0.2, 0.3, 0.6), "roughness": 0.8, "name": "Denim"},
            "leather": {"kd": (0.3, 0.2, 0.1), "roughness": 0.3, "name": "Leather"},
            "silk": {"kd": (0.95, 0.95, 0.95), "roughness": 0.1, "name": "Silk"},
            "wool": {"kd": (0.6, 0.6, 0.6), "roughness": 0.9, "name": "Wool"},
            "beige": {"kd": (0.9, 0.85, 0.75), "roughness": 0.6, "name": "Beige"},
            "white": {"kd": (1.0, 1.0, 1.0), "roughness": 0.7, "name": "White"},
            "black": {"kd": (0.1, 0.1, 0.1), "roughness": 0.5, "name": "Black"}
        }
        
        log("GarmentGenerator initialized", "CLO")
    
    def parse_prompt(self, prompt: str) -> Dict:
        """Parse text prompt to extract garment type, material, and attributes"""
        prompt_lower = prompt.lower()
        
        # Detect garment type
        garment_type = "shirt"  # Default
        for key in self.templates.keys():
            if key in prompt_lower:
                garment_type = key
                break
        
        # Detect material
        material_key = "cotton"  # Default
        for mat_key in self.materials.keys():
            if mat_key in prompt_lower:
                material_key = mat_key
                break
        
        # Detect attributes
        attributes = []
        if "oversized" in prompt_lower or "large" in prompt_lower:
            attributes.append("oversized")
        if "fitted" in prompt_lower or "tight" in prompt_lower:
            attributes.append("fitted")
        if "long" in prompt_lower:
            attributes.append("long")
        if "short" in prompt_lower:
            attributes.append("short")
        if "sleeveless" in prompt_lower or "tank" in prompt_lower:
            attributes.append("sleeveless")
        if "rolled" in prompt_lower or "cuffed" in prompt_lower:
            attributes.append("rolled_sleeves")
        if "belt" in prompt_lower:
            attributes.append("belted")
        if "hood" in prompt_lower:
            attributes.append("hooded")
        
        return {
            "garment_type": garment_type,
            "material": material_key,
            "attributes": attributes,
            "original_prompt": prompt
        }
    
    def generate_garment(self, prompt: str, seed: Optional[int] = None) -> Dict[str, str]:
        """
        Generate garment from text prompt
        
        Returns:
            Dict with keys: obj_file, mtl_file, metadata_file, preview_file
        """
        if seed is None:
            seed = random.randint(1000, 9999)
        
        random.seed(seed)
        
        # Parse prompt
        parsed = self.parse_prompt(prompt)
        garment_type = parsed["garment_type"]
        material_key = parsed["material"]
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = f"garment_{timestamp}_{garment_type}_{seed:04d}"
        
        obj_file = os.path.join(self.output_dir, f"{base_name}.obj")
        mtl_file = os.path.join(self.output_dir, f"{base_name}.mtl")
        metadata_file = os.path.join(self.output_dir, f"{base_name}_metadata.json")
        
        # Preview will be generated via render_manager after OBJ creation
        preview_file = None
        
        # Get template generator
        if garment_type not in self.templates:
            garment_type = "shirt"
        
        template_func = self.templates[garment_type]
        
        # Generate mesh
        vertices, faces, normals = template_func(parsed["attributes"], seed)
        
        # Write OBJ file
        self._write_obj(obj_file, vertices, faces, normals, base_name, mtl_file)
        
        # Write MTL file
        material = self.materials[material_key]
        self._write_mtl(mtl_file, base_name, material)
        
        # Write metadata
        metadata = {
            "prompt": prompt,
            "parsed": parsed,
            "seed": seed,
            "timestamp": datetime.now().isoformat(),
            "files": {
                "obj": os.path.basename(obj_file),
                "mtl": os.path.basename(mtl_file),
                "preview": os.path.basename(preview_file) if os.path.exists(preview_file) else None
            },
            "garment_type": garment_type,
            "material": material_key,
            "vertex_count": len(vertices),
            "face_count": len(faces)
        }
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        log(f"Generated garment: {base_name}.obj ({len(vertices)} vertices, {len(faces)} faces)", "CLO")
        
        return {
            "obj_file": obj_file,
            "mtl_file": mtl_file,
            "metadata_file": metadata_file,
            "preview_file": preview_file,
            "base_name": base_name,
            "metadata": metadata
        }
    
    def _write_obj(self, obj_file: str, vertices: List[Tuple], faces: List[Tuple], 
                   normals: List[Tuple], mtl_name: str, mtl_file: str):
        """Write OBJ file with vertices, faces, normals, and material reference"""
        with open(obj_file, 'w', encoding='utf-8') as f:
            f.write(f"# Garment generated by Julian Assistant Suite\n")
            f.write(f"mtllib {os.path.basename(mtl_file)}\n\n")
            
            # Write vertices
            for v in vertices:
                f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
            
            # Write normals
            f.write("\n")
            for n in normals:
                f.write(f"vn {n[0]:.6f} {n[1]:.6f} {n[2]:.6f}\n")
            
            # Write faces (1-indexed in OBJ)
            f.write("\n")
            f.write(f"usemtl {mtl_name}\n")
            for face in faces:
                # OBJ format: f v1//vn1 v2//vn2 v3//vn3
                if len(face) >= 3:
                    face_str = " ".join([f"{face[i]+1}//{face[i]+1}" for i in range(min(3, len(face)))])
                    f.write(f"f {face_str}\n")
    
    def _write_mtl(self, mtl_file: str, material_name: str, material: Dict):
        """Write MTL material file"""
        kd = material["kd"]
        roughness = material["roughness"]
        
        with open(mtl_file, 'w', encoding='utf-8') as f:
            f.write(f"newmtl {material_name}\n")
            f.write(f"Kd {kd[0]:.3f} {kd[1]:.3f} {kd[2]:.3f}\n")
            f.write(f"Ns {int((1.0 - roughness) * 1000)}\n")  # Specular exponent
            f.write(f"d 1.0\n")  # Opacity
            f.write(f"illum 2\n")  # Illumination model
    
    def _generate_shirt_template(self, attributes: List[str], seed: int) -> Tuple[List, List, List]:
        """Generate basic shirt mesh"""
        vertices = []
        faces = []
        normals = []
        
        # Body parameters
        width = 1.0 if "oversized" in attributes else 0.8
        length = 1.5 if "long" in attributes else 1.0
        sleeve_length = 0.7 if "rolled_sleeves" in attributes else 1.0
        
        # Simplified shirt mesh (box-like base shape)
        # Front torso
        vertices.extend([
            (-width/2, 0, 0), (width/2, 0, 0),
            (-width/2, length, 0), (width/2, length, 0)
        ])
        
        # Back torso
        vertices.extend([
            (-width/2, 0, -0.2), (width/2, 0, -0.2),
            (-width/2, length, -0.2), (width/2, length, -0.2)
        ])
        
        # Sleeves (if not sleeveless)
        if "sleeveless" not in attributes:
            vertices.extend([
                (-width/2 - 0.3, 0.5, 0), (-width/2 - 0.1, 0.5, 0),
                (-width/2 - 0.3, 0.5 + sleeve_length, 0), (-width/2 - 0.1, 0.5 + sleeve_length, 0),
                (width/2 + 0.1, 0.5, 0), (width/2 + 0.3, 0.5, 0),
                (width/2 + 0.1, 0.5 + sleeve_length, 0), (width/2 + 0.3, 0.5 + sleeve_length, 0)
            ])
        
        # Generate faces (simplified triangulation)
        if len(vertices) >= 4:
            # Front face
            faces.append((0, 1, 2))
            faces.append((1, 3, 2))
        
        # Generate normals (simple outward normals)
        for i in range(len(vertices)):
            # Simplified normal calculation
            normals.append((0, 0, 1))
        
        return vertices, faces, normals
    
    def _generate_tshirt_template(self, attributes: List[str], seed: int) -> Tuple[List, List, List]:
        """Generate T-shirt mesh (simpler than shirt)"""
        return self._generate_shirt_template(attributes, seed)
    
    def _generate_pants_template(self, attributes: List[str], seed: int) -> Tuple[List, List, List]:
        """Generate pants mesh"""
        vertices = []
        faces = []
        normals = []
        
        width = 0.6 if "oversized" in attributes else 0.5
        length = 1.2 if "long" in attributes else 0.8
        
        # Waist
        vertices.extend([
            (-width/2, 0, 0), (width/2, 0, 0),
            (-width/2, 0, -0.3), (width/2, 0, -0.3)
        ])
        
        # Legs
        vertices.extend([
            (-width/3, length, 0), (width/3, length, 0),
            (-width/3, length, -0.2), (width/3, length, -0.2)
        ])
        
        if len(vertices) >= 4:
            faces.append((0, 1, 2))
            faces.append((1, 3, 2))
        
        for i in range(len(vertices)):
            normals.append((0, 0, 1))
        
        return vertices, faces, normals
    
    def _generate_coat_template(self, attributes: List[str], seed: int) -> Tuple[List, List, List]:
        """Generate coat mesh"""
        vertices = []
        faces = []
        normals = []
        
        width = 1.2 if "oversized" in attributes else 1.0
        length = 2.0 if "long" in attributes else 1.5
        
        # Body
        vertices.extend([
            (-width/2, 0, 0), (width/2, 0, 0),
            (-width/2, length, 0), (width/2, length, 0)
        ])
        
        # Collar (if applicable)
        if len(vertices) >= 4:
            faces.append((0, 1, 2))
            faces.append((1, 3, 2))
        
        for i in range(len(vertices)):
            normals.append((0, 0, 1))
        
        return vertices, faces, normals
    
    def _generate_jacket_template(self, attributes: List[str], seed: int) -> Tuple[List, List, List]:
        """Generate jacket mesh"""
        return self._generate_coat_template(attributes, seed)
    
    def _generate_trench_template(self, attributes: List[str], seed: int) -> Tuple[List, List, List]:
        """Generate trench coat mesh"""
        vertices = []
        faces = []
        normals = []
        
        width = 1.3 if "oversized" in attributes else 1.1
        length = 2.5 if "long" in attributes else 2.0
        
        # Body
        vertices.extend([
            (-width/2, 0, 0), (width/2, 0, 0),
            (-width/2, length, 0), (width/2, length, 0)
        ])
        
        # Belt (if belted)
        if "belted" in attributes:
            vertices.extend([
                (-width/2, 1.0, 0.1), (width/2, 1.0, 0.1)
            ])
        
        if len(vertices) >= 4:
            faces.append((0, 1, 2))
            faces.append((1, 3, 2))
        
        for i in range(len(vertices)):
            normals.append((0, 0, 1))
        
        return vertices, faces, normals
    
    def _generate_dress_template(self, attributes: List[str], seed: int) -> Tuple[List, List, List]:
        """Generate dress mesh"""
        vertices = []
        faces = []
        normals = []
        
        width = 0.8 if "oversized" in attributes else 0.7
        length = 2.0 if "long" in attributes else 1.5
        
        vertices.extend([
            (-width/2, 0, 0), (width/2, 0, 0),
            (-width/2, length, 0), (width/2, length, 0)
        ])
        
        if len(vertices) >= 4:
            faces.append((0, 1, 2))
            faces.append((1, 3, 2))
        
        for i in range(len(vertices)):
            normals.append((0, 0, 1))
        
        return vertices, faces, normals
    
    def _generate_skirt_template(self, attributes: List[str], seed: int) -> Tuple[List, List, List]:
        """Generate skirt mesh"""
        vertices = []
        faces = []
        normals = []
        
        width_top = 0.6
        width_bottom = 1.0 if "oversized" in attributes else 0.8
        length = 0.8 if "short" in attributes else 1.2
        
        vertices.extend([
            (-width_top/2, 0, 0), (width_top/2, 0, 0),
            (-width_bottom/2, length, 0), (width_bottom/2, length, 0)
        ])
        
        if len(vertices) >= 4:
            faces.append((0, 1, 2))
            faces.append((1, 3, 2))
        
        for i in range(len(vertices)):
            normals.append((0, 0, 1))
        
        return vertices, faces, normals
    
    def generate_preview(self, obj_file: str, output_preview: str) -> bool:
        """Generate preview image from OBJ file"""
        try:
            # Try trimesh first (lighter)
            try:
                import trimesh
                mesh = trimesh.load(obj_file, file_type='obj')
                
                # Render scene
                scene = trimesh.Scene(mesh)
                data = scene.save_image(resolution=(512, 512))
                
                if data:
                    with open(output_preview, 'wb') as f:
                        f.write(data)
                    log(f"Preview generated: {os.path.basename(output_preview)}", "CLO")
                    return True
            except ImportError:
                pass
            
            # Fallback to Open3D
            try:
                import open3d as o3d
                mesh = o3d.io.read_triangle_mesh(obj_file)
                
                if len(mesh.vertices) == 0:
                    return False
                
                # Create visualizer
                vis = o3d.visualization.Visualizer()
                vis.create_window(visible=False, width=512, height=512)
                vis.add_geometry(mesh)
                vis.capture_screen_image(output_preview)
                vis.destroy_window()
                
                log(f"Preview generated: {os.path.basename(output_preview)}", "CLO")
                return True
            except ImportError:
                log("Preview generation requires trimesh or open3d", "CLO", level="WARNING")
                return False
        except Exception as e:
            log(f"Preview generation failed: {e}", "CLO", level="ERROR")
            return False
    
    def list_outputs(self) -> List[Dict]:
        """List all generated garments"""
        outputs = []
        
        for file in os.listdir(self.output_dir):
            if file.endswith("_metadata.json"):
                metadata_path = os.path.join(self.output_dir, file)
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    # Check for preview
                    preview_name = metadata.get("files", {}).get("preview")
                    preview_path = None
                    if preview_name:
                        preview_path = os.path.join(self.preview_dir, preview_name)
                        if not os.path.exists(preview_path):
                            preview_path = None
                    
                    outputs.append({
                        "base_name": metadata.get("garment_type", "unknown"),
                        "prompt": metadata.get("prompt", ""),
                        "timestamp": metadata.get("timestamp", ""),
                        "obj_file": metadata.get("files", {}).get("obj", ""),
                        "preview_file": preview_name if preview_path else None,
                        "metadata": metadata
                    })
                except:
                    pass
        
        # Sort by timestamp (newest first)
        outputs.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return outputs
    
    def export_to_clo3d(self, obj_file: str, clo_project_dir: str) -> Optional[str]:
        """Export generated garment to CLO3D project folder"""
        try:
            if not os.path.exists(clo_project_dir):
                log(f"CLO3D project directory not found: {clo_project_dir}", "CLO", level="WARNING")
                return None
            
            imports_dir = os.path.join(clo_project_dir, "imports")
            os.makedirs(imports_dir, exist_ok=True)
            
            # Copy OBJ and MTL files
            import shutil
            base_name = os.path.basename(obj_file)
            clo_obj_path = os.path.join(imports_dir, base_name)
            shutil.copy2(obj_file, clo_obj_path)
            
            # Copy MTL if exists
            mtl_file = obj_file.replace(".obj", ".mtl")
            if os.path.exists(mtl_file):
                clo_mtl_path = os.path.join(imports_dir, os.path.basename(mtl_file))
                shutil.copy2(mtl_file, clo_mtl_path)
            
            log(f"Exported to CLO3D: {clo_obj_path}", "CLO")
            return clo_obj_path
        except Exception as e:
            log(f"Error exporting to CLO3D: {e}", "CLO", level="ERROR")
            return None
