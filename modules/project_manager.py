"""
Project Manager - Handles garment projects and CLO integration
Manages iteration tracking, exports, and CLO 3D integration.
"""

import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.json"
EXPORTS_DIR = BASE_DIR / "exports" / "garments"
PROJECTS_DIR = BASE_DIR / "exports" / "projects"


def ensure_directories():
    """Create required directories"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


def get_settings() -> Dict:
    """
    Load settings from config/settings.json
    
    Returns:
        dict: Settings dictionary with defaults
    """
    ensure_directories()
    
    defaults = {
        "clo_executable": "C:\\Program Files\\CLO\\CLO.exe",
        "export_dir": str(EXPORTS_DIR),
        "template_dir": str(BASE_DIR / "templates"),
        "auto_open_clo": False,
        "default_fabric": "cotton",
        "default_style": "casual"
    }
    
    if not SETTINGS_FILE.exists():
        save_settings(defaults)
        return defaults
    
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # Merge with defaults (in case new settings were added)
        for key, value in defaults.items():
            if key not in settings:
                settings[key] = value
        
        return settings
        
    except Exception as e:
        print(f"Warning: Could not load settings: {e}")
        return defaults


def save_settings(settings: Dict) -> bool:
    """
    Save settings to config/settings.json
    
    Args:
        settings: Settings dictionary
    
    Returns:
        bool: Success status
    """
    try:
        ensure_directories()
        
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2)
        
        return True
        
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False


def update_setting(key: str, value) -> bool:
    """
    Update a single setting
    
    Args:
        key: Setting key
        value: New value
    
    Returns:
        bool: Success status
    """
    settings = get_settings()
    settings[key] = value
    return save_settings(settings)


def open_in_clo(file_path: str) -> Dict:
    """
    Open a garment file in CLO 3D.
    
    Args:
        file_path: Path to .zprj file
    
    Returns:
        dict: {"success": bool, "message": str}
    """
    try:
        settings = get_settings()
        clo_path = settings.get("clo_executable", "C:\\Program Files\\CLO\\CLO.exe")
        
        # Check if CLO executable exists
        if not Path(clo_path).exists():
            return {
                "success": False,
                "error": f"CLO executable not found at: {clo_path}",
                "hint": "Update CLO path in Settings"
            }
        
        # Check if garment file exists
        if not Path(file_path).exists():
            return {
                "success": False,
                "error": f"Garment file not found: {file_path}"
            }
        
        # Launch CLO with the file
        subprocess.Popen([clo_path, file_path], shell=True)
        
        return {
            "success": True,
            "message": f"Opened {Path(file_path).name} in CLO 3D"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def create_project(name: str, description: str = "") -> Dict:
    """
    Create a new garment project.
    
    Args:
        name: Project name
        description: Optional project description
    
    Returns:
        dict: Project metadata
    """
    try:
        ensure_directories()
        
        # Generate project ID
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_id = f"{name.replace(' ', '_')}_{timestamp}"
        safe_id = "".join(c for c in project_id if c.isalnum() or c in "._-")
        
        # Create project directory
        project_dir = PROJECTS_DIR / safe_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Create project metadata
        metadata = {
            "project_id": safe_id,
            "name": name,
            "description": description,
            "created_at": timestamp,
            "iterations": [],
            "current_iteration": 0,
            "tags": []
        }
        
        # Save metadata
        metadata_file = project_dir / "project.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            "success": True,
            "project_id": safe_id,
            "project_dir": str(project_dir),
            "metadata": metadata
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def add_iteration(project_id: str, garment_path: str, notes: str = "") -> Dict:
    """
    Add a garment iteration to a project.
    
    Args:
        project_id: Project ID
        garment_path: Path to garment file
        notes: Optional iteration notes
    
    Returns:
        dict: Updated project metadata
    """
    try:
        project_dir = PROJECTS_DIR / project_id
        metadata_file = project_dir / "project.json"
        
        if not metadata_file.exists():
            return {
                "success": False,
                "error": f"Project not found: {project_id}"
            }
        
        # Load project metadata
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        
        # Create iteration
        iteration_num = len(metadata["iterations"]) + 1
        iteration = {
            "iteration": iteration_num,
            "garment_path": garment_path,
            "notes": notes,
            "timestamp": datetime.now().isoformat()
        }
        
        # Copy garment to project directory
        garment_name = Path(garment_path).name
        project_garment = project_dir / f"iteration_{iteration_num}_{garment_name}"
        shutil.copy2(garment_path, project_garment)
        iteration["project_path"] = str(project_garment)
        
        # Update metadata
        metadata["iterations"].append(iteration)
        metadata["current_iteration"] = iteration_num
        
        # Save metadata
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            "success": True,
            "iteration": iteration_num,
            "metadata": metadata
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def list_projects() -> List[Dict]:
    """
    List all garment projects.
    
    Returns:
        list: List of project metadata dicts
    """
    try:
        ensure_directories()
        
        projects = []
        
        for project_dir in PROJECTS_DIR.iterdir():
            if not project_dir.is_dir():
                continue
            
            metadata_file = project_dir / "project.json"
            if not metadata_file.exists():
                continue
            
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                projects.append(metadata)
            except Exception as e:
                print(f"Warning: Could not load project {project_dir.name}: {e}")
                continue
        
        # Sort by creation date (newest first)
        projects.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        return projects
        
    except Exception as e:
        print(f"Error listing projects: {e}")
        return []


def export_project(project_id: str, export_format: str = "zip") -> Dict:
    """
    Export a project as a package.
    
    Args:
        project_id: Project ID
        export_format: Export format (zip, folder)
    
    Returns:
        dict: Export result with path
    """
    try:
        project_dir = PROJECTS_DIR / project_id
        
        if not project_dir.exists():
            return {
                "success": False,
                "error": f"Project not found: {project_id}"
            }
        
        if export_format == "zip":
            # Create zip archive
            archive_path = EXPORTS_DIR / f"{project_id}.zip"
            shutil.make_archive(
                str(archive_path.with_suffix('')),
                'zip',
                project_dir
            )
            
            return {
                "success": True,
                "export_path": str(archive_path),
                "format": "zip"
            }
        
        else:
            # Copy to exports folder
            export_path = EXPORTS_DIR / project_id
            if export_path.exists():
                shutil.rmtree(export_path)
            shutil.copytree(project_dir, export_path)
            
            return {
                "success": True,
                "export_path": str(export_path),
                "format": "folder"
            }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Initialize on import
ensure_directories()

