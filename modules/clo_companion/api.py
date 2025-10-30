"""
CLO Companion Module - Flask API Server (STUB)
"""

import sys
import os

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from flask import Flask, request, jsonify
from flask_cors import CORS
import time
from datetime import datetime

# Add paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from logger import log
except ImportError:
    def log(msg, category="CLO"):
        print(f"[{category}] {msg}")

from core.config_manager import get_module_config, get_suite_config
from core.auth_helper import require_auth_token

app = Flask(__name__)

suite_config = get_suite_config()
if suite_config.get("security", {}).get("cors_enabled", False):
    CORS(app)

module_config = get_module_config("clo_companion")

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "module_id": "clo_companion",
        "version": "1.0.0",
        "uptime_seconds": 0,
        "clo3d_connected": False,
        "last_command_time": None,
        "enabled": module_config.get("enabled", False)
    })

@app.route('/apply_change', methods=['POST'])
@require_auth_token
def apply_change():
    """Apply design change (with DressCode integration)"""
    try:
        data = request.json or {}
        command = data.get('command', '')
        dry_run = data.get('dry_run', False)
        
        # Check if garment generation requested
        if any(word in command.lower() for word in ['generate', 'create', 'make', 'pattern']):
            from modules.clo_companion.garment_gen import GarmentGenerator
            
            generator = GarmentGenerator()
            result = generator.generate_from_prompt(command)
            
            if result.get('success'):
                # Store in memory
                try:
                    from core.memory_manager import get_memory_manager
                    memory = get_memory_manager()
                    memory.remember(
                        "julian",
                        f"clo_generation_{int(time.time())}",
                        {
                            "prompt": command,
                            "obj_file": result.get("obj_file"),
                            "timestamp": datetime.now().isoformat()
                        },
                        category="clo_projects",
                        confidence=1.0
                    )
                except:
                    pass
                
                # Publish render event
                try:
                    from core.event_bus import publish_event
                    publish_event(
                        "render.complete",
                        "clo_companion",
                        {
                            "obj_file": result.get("obj_file"),
                            "prompt": command
                        }
                    )
                except:
                    pass
                
                return jsonify({
                    "status": "success",
                    "action": "garment_generated",
                    "result": result
                })
        
        # Regular design change (stub for now)
        return jsonify({
            "status": "stub",
            "message": "Design change commands not yet fully implemented",
            "command": command,
            "dry_run": dry_run
        }), 503
        
    except Exception as e:
        log(f"Error in apply_change: {e}", "CLO", level="ERROR")
        return jsonify({"error": str(e)}), 500

@app.route('/undo', methods=['POST'])
@require_auth_token
def undo():
    """Undo last change (STUB)"""
    return jsonify({
        "status": "stub",
        "message": "CLO Companion is not yet implemented."
    }), 503

@app.route('/redo', methods=['POST'])
@require_auth_token
def redo():
    """Redo last undone change (STUB)"""
    return jsonify({
        "status": "stub",
        "message": "CLO Companion is not yet implemented."
    }), 503

@app.route('/render', methods=['POST'])
@require_auth_token
def render():
    """Render preview"""
    try:
        data = request.json or {}
        obj_file = data.get('obj_file', '')
        garment_path = data.get('garment', '')
        
        if not obj_file and garment_path:
            # Find latest generated garment
            import glob
            generated_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "modules", "clo_companion", "data", "generated"
            )
            if os.path.exists(generated_dir):
                obj_files = glob.glob(os.path.join(generated_dir, "**", "*.obj"), recursive=True)
                if obj_files:
                    obj_file = max(obj_files, key=os.path.getmtime)
        
        if obj_file and os.path.exists(obj_file):
            from modules.clo_companion.garment_gen import GarmentGenerator
            generator = GarmentGenerator()
            preview_file = generator.preview_garment(obj_file)
            
            return jsonify({
                "status": "success",
                "preview_file": preview_file,
                "obj_file": obj_file
            })
        else:
            return jsonify({
                "status": "error",
                "message": "No garment file provided or found"
            }), 400
        
    except Exception as e:
        log(f"Error in render: {e}", "CLO", level="ERROR")
        return jsonify({"error": str(e)}), 500

@app.route('/export', methods=['POST'])
@require_auth_token
def export():
    """Export design to CLO3D"""
    try:
        data = request.json or {}
        obj_file = data.get('obj_file', '')
        clo_project_dir = data.get('clo_project_dir', '')
        
        if not obj_file:
            return jsonify({
                "status": "error",
                "message": "obj_file required"
            }), 400
        
        if not os.path.exists(obj_file):
            return jsonify({
                "status": "error",
                "message": f"OBJ file not found: {obj_file}"
            }), 404
        
        from modules.clo_companion.garment_gen import GarmentGenerator
        generator = GarmentGenerator()
        
        if clo_project_dir:
            exported_path = generator.export_to_clo3d(obj_file, clo_project_dir)
            return jsonify({
                "status": "success",
                "exported_path": exported_path,
                "message": "Exported to CLO3D project"
            })
        else:
            # Return OBJ file path
            return jsonify({
                "status": "success",
                "obj_file": obj_file,
                "message": "CLO project directory not specified, returning OBJ path"
            })
        
    except Exception as e:
        log(f"Error in export: {e}", "CLO", level="ERROR")
        return jsonify({"error": str(e)}), 500

@app.route('/summarize_design', methods=['POST'])
@require_auth_token
def summarize_design():
    """Summarize design (STUB)"""
    return jsonify({
        "status": "stub",
        "message": "CLO Companion is not yet implemented."
    }), 503

if __name__ == '__main__':
    # Use clo_api.py instead (FastAPI server)
    # This file is legacy; new server is clo_api.py
    port = module_config.get('api', {}).get('port', 5001)
    host = suite_config.get("security", {}).get("bind_localhost_only", True)
    host_addr = "127.0.0.1" if host else "0.0.0.0"
    
    log(f"Starting CLO Companion API on {host_addr}:{port}", "CLO")
    app.run(host=host_addr, port=port, debug=False)

