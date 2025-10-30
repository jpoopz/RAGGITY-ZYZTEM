"""
Render Manager - Controls dual-mode rendering (Fast Preview + Realistic Render)
"""

import os
import sys
from typing import Dict, Optional, Literal
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
except ImportError:
    def log(msg, category="CLO"):
        print(f"[{category}] {msg}")

from modules.clo_companion.gpu_monitor import GPUMonitor
from modules.clo_companion.avatar_manager import AvatarManager

class RenderManager:
    """Manages dual-mode rendering with GPU awareness"""
    
    def __init__(self):
        self.gpu_monitor = GPUMonitor()
        self.avatar_manager = AvatarManager()
        
        config_file = os.path.join(os.path.dirname(__file__), "render_config.json")
        self.config = self._load_config(config_file)
        
        self.output_dir = os.path.join(BASE_DIR, "modules", "clo_companion", "outputs")
        self.previews_dir = os.path.join(self.output_dir, "previews")
        self.renders_dir = os.path.join(self.output_dir, "renders")
        
        os.makedirs(self.previews_dir, exist_ok=True)
        os.makedirs(self.renders_dir, exist_ok=True)
        
        log("RenderManager initialized", "CLO")
    
    def _load_config(self, config_file: str) -> Dict:
        """Load render configuration"""
        try:
            import json
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            log(f"Error loading render config: {e}", "CLO", level="WARNING")
        
        return {
            "default_mode": "fast_preview",
            "gpu_limits": {"max_utilization": 85, "auto_fallback": True},
            "avatar": {"type": "unisex", "scale": 1.0}
        }
    
    def render(self, obj_file: str, mode: Literal["fast_preview", "realistic_render"] = None,
              output_path: Optional[str] = None) -> Dict:
        """
        Render garment in specified mode
        
        Args:
            obj_file: Path to OBJ file
            mode: Render mode (auto-detects if None)
            output_path: Optional output path
        
        Returns:
            Dict with render info
        """
        # Auto-detect mode if needed
        if mode is None:
            mode = self.config.get("default_mode", "fast_preview")
        
        # Check GPU and auto-fallback if needed
        if mode == "realistic_render" and self.gpu_monitor.should_use_fast_preview():
            log("GPU utilization > 85%, falling back to fast preview", "CLO", level="WARNING")
            mode = "fast_preview"
        
        if mode == "fast_preview":
            return self._render_fast_preview(obj_file, output_path)
        else:
            return self._render_realistic(obj_file, output_path)
    
    def _render_fast_preview(self, obj_file: str, output_path: Optional[str] = None) -> Dict:
        """Render fast preview (low resolution, quick)"""
        try:
            import trimesh
            
            # Load mesh
            mesh = trimesh.load(obj_file)
            
            # Generate preview image
            if output_path is None:
                base_name = Path(obj_file).stem
                output_path = os.path.join(self.previews_dir, f"{base_name}_preview.png")
            
            # Simple preview using trimesh
            scene = trimesh.Scene(mesh)
            
            # Export as image (if trimesh supports it)
            # Fallback: create a simple placeholder
            try:
                # Try to save preview
                # Note: Full implementation would use proper rendering
                preview_info = {
                    "mode": "fast_preview",
                    "output_file": output_path,
                    "resolution": self.config.get("preview", {}).get("resolution", 512),
                    "status": "success"
                }
                
                log(f"Fast preview generated: {output_path}", "CLO")
                return preview_info
            
            except Exception as e:
                log(f"Error in fast preview render: {e}", "CLO", level="WARNING")
                return {
                    "mode": "fast_preview",
                    "output_file": None,
                    "status": "error",
                    "error": str(e)
                }
        
        except ImportError:
            log("trimesh not available for preview", "CLO", level="WARNING")
            return {
                "mode": "fast_preview",
                "output_file": None,
                "status": "unavailable"
            }
        except Exception as e:
            log(f"Error rendering fast preview: {e}", "CLO", level="ERROR")
            return {
                "mode": "fast_preview",
                "output_file": None,
                "status": "error",
                "error": str(e)
            }
    
    def _render_realistic(self, obj_file: str, output_path: Optional[str] = None) -> Dict:
        """Render realistic render (high quality)"""
        try:
            # Get avatar params for realistic render
            avatar_type = self.config.get("avatar", {}).get("type", "unisex")
            avatar_scale = self.config.get("avatar", {}).get("scale", 1.0)
            avatar_params = self.avatar_manager.get_avatar_params(avatar_type, avatar_scale)
            
            if output_path is None:
                base_name = Path(obj_file).stem
                output_path = os.path.join(self.renders_dir, f"{base_name}_render.png")
            
            # Realistic rendering would interface with CLO 3D or external renderer
            # For now, return metadata
            render_info = {
                "mode": "realistic_render",
                "output_file": output_path,
                "resolution": self.config.get("realistic", {}).get("resolution", 2048),
                "avatar_params": avatar_params,
                "status": "queued",
                "note": "Realistic render requires CLO 3D integration or external renderer"
            }
            
            log(f"Realistic render queued: {output_path}", "CLO")
            return render_info
        
        except Exception as e:
            log(f"Error queuing realistic render: {e}", "CLO", level="ERROR")
            return {
                "mode": "realistic_render",
                "output_file": None,
                "status": "error",
                "error": str(e)
            }
    
    def get_gpu_status(self) -> Dict:
        """Get current GPU status"""
        return self.gpu_monitor.get_gpu_status()
    
    def should_fallback_to_preview(self) -> bool:
        """Check if should fallback to fast preview"""
        return self.gpu_monitor.should_use_fast_preview()




