"""
CLO Script Factory

Generates self-contained Python scripts for direct execution in CLO 3D.
These scripts can be opened and run via CLO's Script menu.

Usage:
    from modules.clo_companion.script_factory import make_import_script
    
    make_import_script(
        garment_path="C:/Projects/shirt.zprj",
        out_script_path="C:/Scripts/import_shirt.py"
    )
    
    # Then in CLO: File > Script > Run Script... > Select import_shirt.py
"""

import os
import time
from typing import Optional

from .config import SCRIPT_HEADER, SCRIPT_ENCODING


def _write_script(script_path: str, content: str) -> bool:
    """
    Write script content to file with proper encoding.
    
    Args:
        script_path: Destination script file path
        content: Script content
    
    Returns:
        bool: True if successful
    """
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(script_path), exist_ok=True)
        
        # Write script
        with open(script_path, 'w', encoding=SCRIPT_ENCODING) as f:
            f.write(content)
        
        return True
    
    except Exception as e:
        print(f"Error writing script: {e}")
        return False


def make_import_script(garment_path: str, out_script_path: str, 
                      description: Optional[str] = None) -> bool:
    """
    Generate a CLO script to import a garment file.
    
    Args:
        garment_path: Path to garment file to import (.zprj, .obj, .fbx)
        out_script_path: Where to save the generated script
        description: Optional description for script header
    
    Returns:
        bool: True if script was generated successfully
    """
    # Normalize paths
    garment_path = os.path.normpath(garment_path)
    out_script_path = os.path.normpath(out_script_path)
    
    # Ensure .py extension
    if not out_script_path.endswith('.py'):
        out_script_path += '.py'
    
    # Build script header
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    mode = "Mode B: Direct Script Execution"
    
    header = SCRIPT_HEADER.format(timestamp=timestamp, mode=mode)
    
    if description:
        header += f"# Description: {description}\n"
    
    header += f"# Garment: {garment_path}\n\n"
    
    # Build script content
    script_content = header + f'''
"""
Import Garment Script

This script imports a garment file into CLO 3D.
Run this via: File > Script > Run Script... in CLO
"""

import os

# Configuration
GARMENT_PATH = r"{garment_path}"

def main():
    """Main execution function"""
    print("=" * 60)
    print("CLO Import Script - RAGGITY ZYZTEM 2.0")
    print("=" * 60)
    print(f"Importing: {{GARMENT_PATH}}")
    print("")
    
    # Validate file exists
    if not os.path.exists(GARMENT_PATH):
        print(f"ERROR: File not found: {{GARMENT_PATH}}")
        return False
    
    try:
        # TODO: CLO: Import garment via API
        # Replace this section with actual CLO API calls:
        # 
        # Example (syntax may vary):
        # import CLO_API
        # CLO_API.ImportFile(GARMENT_PATH)
        # 
        # or:
        # import CLO
        # CLO.ImportProject(GARMENT_PATH)
        
        print("TODO: Actual CLO import API call not implemented")
        print(f"Would import: {{GARMENT_PATH}}")
        print("")
        print("SUCCESS: Import requested (API stub)")
        return True
        
    except Exception as e:
        print(f"ERROR: Import failed: {{e}}")
        import traceback
        traceback.print_exc()
        return False

# Execute
if __name__ == "__main__":
    success = main()
    
    if success:
        print("")
        print("Script completed successfully")
    else:
        print("")
        print("Script completed with errors")
'''
    
    return _write_script(out_script_path, script_content)


def make_screenshot_script(png_path: str, width: int, height: int, 
                          out_script_path: str, 
                          description: Optional[str] = None) -> bool:
    """
    Generate a CLO script to take a screenshot.
    
    Args:
        png_path: Where to save the screenshot
        width: Screenshot width in pixels
        height: Screenshot height in pixels
        out_script_path: Where to save the generated script
        description: Optional description for script header
    
    Returns:
        bool: True if script was generated successfully
    """
    # Normalize paths
    png_path = os.path.normpath(png_path)
    out_script_path = os.path.normpath(out_script_path)
    
    # Ensure .py extension for script
    if not out_script_path.endswith('.py'):
        out_script_path += '.py'
    
    # Ensure .png extension for image
    if not png_path.lower().endswith('.png'):
        png_path += '.png'
    
    # Build script header
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    mode = "Mode B: Direct Script Execution"
    
    header = SCRIPT_HEADER.format(timestamp=timestamp, mode=mode)
    
    if description:
        header += f"# Description: {description}\n"
    
    header += f"# Output: {png_path}\n"
    header += f"# Resolution: {width}x{height}\n\n"
    
    # Build script content
    script_content = header + f'''
"""
Screenshot Script

This script captures a screenshot of the CLO 3D viewport.
Run this via: File > Script > Run Script... in CLO
"""

import os

# Configuration
OUTPUT_PATH = r"{png_path}"
WIDTH = {width}
HEIGHT = {height}

def main():
    """Main execution function"""
    print("=" * 60)
    print("CLO Screenshot Script - RAGGITY ZYZTEM 2.0")
    print("=" * 60)
    print(f"Output: {{OUTPUT_PATH}}")
    print(f"Resolution: {{WIDTH}}x{{HEIGHT}}")
    print("")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(OUTPUT_PATH)
    if output_dir and not os.path.exists(output_dir):
        print(f"Creating directory: {{output_dir}}")
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        # TODO: CLO: Capture screenshot via API
        # Replace this section with actual CLO API calls:
        #
        # Example (syntax may vary):
        # import CLO_API
        # CLO_API.CaptureViewport(OUTPUT_PATH, WIDTH, HEIGHT)
        #
        # or:
        # import CLO
        # CLO.TakeScreenshot(OUTPUT_PATH, resolution=(WIDTH, HEIGHT))
        #
        # or:
        # import CLO
        # CLO.SetViewportSize(WIDTH, HEIGHT)
        # CLO.CaptureImage(OUTPUT_PATH)
        
        print("TODO: Actual CLO screenshot API call not implemented")
        print(f"Would save screenshot to: {{OUTPUT_PATH}}")
        print(f"Resolution: {{WIDTH}}x{{HEIGHT}}")
        print("")
        print("SUCCESS: Screenshot requested (API stub)")
        return True
        
    except Exception as e:
        print(f"ERROR: Screenshot failed: {{e}}")
        import traceback
        traceback.print_exc()
        return False

# Execute
if __name__ == "__main__":
    success = main()
    
    if success:
        print("")
        print("Script completed successfully")
        print(f"Check: {{OUTPUT_PATH}}")
    else:
        print("")
        print("Script completed with errors")
'''
    
    return _write_script(out_script_path, script_content)


def make_export_script(export_path: str, export_format: str, 
                      out_script_path: str,
                      description: Optional[str] = None) -> bool:
    """
    Generate a CLO script to export the current garment.
    
    Args:
        export_path: Where to save the exported file
        export_format: Export format (zprj, obj, fbx, gltf)
        out_script_path: Where to save the generated script
        description: Optional description for script header
    
    Returns:
        bool: True if script was generated successfully
    """
    # Normalize paths
    export_path = os.path.normpath(export_path)
    out_script_path = os.path.normpath(out_script_path)
    
    # Ensure .py extension for script
    if not out_script_path.endswith('.py'):
        out_script_path += '.py'
    
    # Build script header
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    mode = "Mode B: Direct Script Execution"
    
    header = SCRIPT_HEADER.format(timestamp=timestamp, mode=mode)
    
    if description:
        header += f"# Description: {description}\n"
    
    header += f"# Export: {export_path}\n"
    header += f"# Format: {export_format}\n\n"
    
    # Build script content
    script_content = header + f'''
"""
Export Garment Script

This script exports the current garment from CLO 3D.
Run this via: File > Script > Run Script... in CLO
"""

import os

# Configuration
EXPORT_PATH = r"{export_path}"
EXPORT_FORMAT = "{export_format}"

def main():
    """Main execution function"""
    print("=" * 60)
    print("CLO Export Script - RAGGITY ZYZTEM 2.0")
    print("=" * 60)
    print(f"Export to: {{EXPORT_PATH}}")
    print(f"Format: {{EXPORT_FORMAT}}")
    print("")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(EXPORT_PATH)
    if output_dir and not os.path.exists(output_dir):
        print(f"Creating directory: {{output_dir}}")
        os.makedirs(output_dir, exist_ok=True)
    
    try:
        # TODO: CLO: Export garment via API
        # Replace this section with actual CLO API calls:
        #
        # Example (syntax may vary):
        # import CLO_API
        # CLO_API.ExportFile(EXPORT_PATH, EXPORT_FORMAT)
        #
        # or:
        # import CLO
        # CLO.SaveAs(EXPORT_PATH)
        # CLO.Export(EXPORT_PATH, exportType=EXPORT_FORMAT)
        
        print("TODO: Actual CLO export API call not implemented")
        print(f"Would export to: {{EXPORT_PATH}}")
        print(f"Format: {{EXPORT_FORMAT}}")
        print("")
        print("SUCCESS: Export requested (API stub)")
        return True
        
    except Exception as e:
        print(f"ERROR: Export failed: {{e}}")
        import traceback
        traceback.print_exc()
        return False

# Execute
if __name__ == "__main__":
    success = main()
    
    if success:
        print("")
        print("Script completed successfully")
        print(f"Check: {{EXPORT_PATH}}")
    else:
        print("")
        print("Script completed with errors")
'''
    
    return _write_script(out_script_path, script_content)


def make_simulation_script(steps: int, out_script_path: str,
                          description: Optional[str] = None) -> bool:
    """
    Generate a CLO script to run physics simulation.
    
    Args:
        steps: Number of simulation steps
        out_script_path: Where to save the generated script
        description: Optional description for script header
    
    Returns:
        bool: True if script was generated successfully
    """
    # Normalize path
    out_script_path = os.path.normpath(out_script_path)
    
    # Ensure .py extension
    if not out_script_path.endswith('.py'):
        out_script_path += '.py'
    
    # Build script header
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    mode = "Mode B: Direct Script Execution"
    
    header = SCRIPT_HEADER.format(timestamp=timestamp, mode=mode)
    
    if description:
        header += f"# Description: {description}\n"
    
    header += f"# Simulation Steps: {steps}\n\n"
    
    # Build script content
    script_content = header + f'''
"""
Simulation Script

This script runs physics simulation in CLO 3D.
Run this via: File > Script > Run Script... in CLO
"""

# Configuration
SIMULATION_STEPS = {steps}

def main():
    """Main execution function"""
    print("=" * 60)
    print("CLO Simulation Script - RAGGITY ZYZTEM 2.0")
    print("=" * 60)
    print(f"Simulation steps: {{SIMULATION_STEPS}}")
    print("")
    
    try:
        # TODO: CLO: Run simulation via API
        # Replace this section with actual CLO API calls:
        #
        # Example (syntax may vary):
        # import CLO_API
        # CLO_API.RunSimulation(steps=SIMULATION_STEPS)
        #
        # or:
        # import CLO
        # CLO.Simulate(frames=SIMULATION_STEPS)
        
        print("TODO: Actual CLO simulation API call not implemented")
        print(f"Would run simulation for {{SIMULATION_STEPS}} steps")
        print("")
        print("SUCCESS: Simulation requested (API stub)")
        return True
        
    except Exception as e:
        print(f"ERROR: Simulation failed: {{e}}")
        import traceback
        traceback.print_exc()
        return False

# Execute
if __name__ == "__main__":
    success = main()
    
    if success:
        print("")
        print("Script completed successfully")
    else:
        print("")
        print("Script completed with errors")
'''
    
    return _write_script(out_script_path, script_content)

