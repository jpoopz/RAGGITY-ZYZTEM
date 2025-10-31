"""
CLO Bridge Listener

TCP socket server that runs inside CLO 3D's Python environment.
Receives commands from external RAGGITY client and executes them using CLO's API.

USAGE:
1. Open CLO 3D
2. File > Script > Run Script... > Select this file
3. Server will start listening on 127.0.0.1:51235 (or configured port)
4. Send JSON commands from RAGGITY UI

SECURITY:
- Binds to localhost only (127.0.0.1)
- No external network exposure
- Command validation before execution
"""

import socket
import json
import os
import sys
import traceback
from datetime import datetime

# Configuration (can be overridden via environment)
HOST = os.getenv("CLO_HOST", "127.0.0.1")
PORT = int(os.getenv("CLO_PORT", "51235"))
BUFFER_SIZE = 4096

# Server state
running = True
request_count = 0


def log(message, level="INFO"):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")


def validate_path(path):
    """Validate and sanitize file path"""
    if not path:
        return False, "Path is empty"
    
    # Basic sanitization
    path = os.path.normpath(path)
    
    # Prevent directory traversal
    if ".." in path:
        return False, "Path contains invalid directory traversal"
    
    return True, path


def import_garment(path):
    """
    Import a garment file into CLO.
    
    Args:
        path: Absolute path to garment file (.zprj, .obj, .fbx, etc.)
    
    Returns:
        dict: Result with success status and message
    """
    try:
        valid, result = validate_path(path)
        if not valid:
            return {"success": False, "error": result}
        
        path = result
        
        if not os.path.exists(path):
            return {"success": False, "error": f"File not found: {path}"}
        
        # TODO: CLO: import garment via API
        # Example (actual API may differ):
        # import CLO_API
        # CLO_API.ImportFile(path)
        # or
        # CLO.ImportProject(path)
        
        log(f"TODO: Import garment from {path}", "WARN")
        
        return {
            "success": True,
            "message": f"Garment import requested: {path}",
            "note": "API stub - actual import not implemented"
        }
        
    except Exception as e:
        log(f"Import failed: {e}", "ERROR")
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


def export_garment(path, format="zprj"):
    """
    Export current garment to file.
    
    Args:
        path: Destination file path
        format: Export format (zprj, obj, fbx, gltf, etc.)
    
    Returns:
        dict: Result with success status
    """
    try:
        valid, result = validate_path(path)
        if not valid:
            return {"success": False, "error": result}
        
        path = result
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # TODO: CLO: export garment via API
        # Example:
        # import CLO_API
        # CLO_API.ExportFile(path, format)
        # or
        # CLO.SaveAs(path)
        # CLO.Export(path, exportType=format)
        
        log(f"TODO: Export garment to {path} as {format}", "WARN")
        
        return {
            "success": True,
            "message": f"Garment export requested: {path}",
            "format": format,
            "note": "API stub - actual export not implemented"
        }
        
    except Exception as e:
        log(f"Export failed: {e}", "ERROR")
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


def take_screenshot(path, width=1920, height=1080):
    """
    Capture screenshot of current 3D view.
    
    Args:
        path: Destination image file path (.png, .jpg)
        width: Image width in pixels
        height: Image height in pixels
    
    Returns:
        dict: Result with success status
    """
    try:
        valid, result = validate_path(path)
        if not valid:
            return {"success": False, "error": result}
        
        path = result
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # TODO: CLO: capture screenshot via API
        # Example:
        # import CLO_API
        # CLO_API.CaptureViewport(path, width, height)
        # or
        # CLO.TakeScreenshot(path, resolution=(width, height))
        
        log(f"TODO: Take screenshot {width}x{height} to {path}", "WARN")
        
        return {
            "success": True,
            "message": f"Screenshot requested: {path}",
            "width": width,
            "height": height,
            "note": "API stub - actual screenshot not implemented"
        }
        
    except Exception as e:
        log(f"Screenshot failed: {e}", "ERROR")
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


def run_simulation(steps=100, duration=None):
    """
    Run physics simulation.
    
    Args:
        steps: Number of simulation steps (if duration not specified)
        duration: Simulation duration in seconds (overrides steps)
    
    Returns:
        dict: Result with success status
    """
    try:
        # TODO: CLO: run simulation via API
        # Example:
        # import CLO_API
        # if duration:
        #     CLO_API.RunSimulation(duration=duration)
        # else:
        #     CLO_API.RunSimulation(steps=steps)
        # or
        # CLO.Simulate(frames=steps)
        # CLO.SimulateTime(seconds=duration)
        
        if duration:
            log(f"TODO: Run simulation for {duration} seconds", "WARN")
            return {
                "success": True,
                "message": f"Simulation requested: {duration}s",
                "duration": duration,
                "note": "API stub - actual simulation not implemented"
            }
        else:
            log(f"TODO: Run simulation for {steps} steps", "WARN")
            return {
                "success": True,
                "message": f"Simulation requested: {steps} steps",
                "steps": steps,
                "note": "API stub - actual simulation not implemented"
            }
        
    except Exception as e:
        log(f"Simulation failed: {e}", "ERROR")
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


def get_garment_info():
    """
    Get information about current garment/project.
    
    Returns:
        dict: Garment metadata
    """
    try:
        # TODO: CLO: get garment info via API
        # Example:
        # import CLO_API
        # info = {
        #     "project_name": CLO_API.GetProjectName(),
        #     "garment_count": CLO_API.GetGarmentCount(),
        #     "pattern_count": CLO_API.GetPatternCount(),
        #     "fabric_count": CLO_API.GetFabricCount(),
        #     "avatar_name": CLO_API.GetAvatarName(),
        #     "is_modified": CLO_API.IsModified()
        # }
        
        log("TODO: Get garment info", "WARN")
        
        return {
            "success": True,
            "info": {
                "project_name": "Unknown",
                "garment_count": 0,
                "pattern_count": 0,
                "note": "API stub - actual info retrieval not implemented"
            }
        }
        
    except Exception as e:
        log(f"Get info failed: {e}", "ERROR")
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


def reset_garment():
    """
    Reset simulation and return garment to initial state.
    
    Returns:
        dict: Result with success status
    """
    try:
        # TODO: CLO: reset simulation via API
        # Example:
        # import CLO_API
        # CLO_API.ResetSimulation()
        # or
        # CLO.ResetToBindPose()
        
        log("TODO: Reset garment", "WARN")
        
        return {
            "success": True,
            "message": "Garment reset requested",
            "note": "API stub - actual reset not implemented"
        }
        
    except Exception as e:
        log(f"Reset failed: {e}", "ERROR")
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}


# Command dispatch table
COMMANDS = {
    "import_garment": import_garment,
    "export_garment": export_garment,
    "take_screenshot": take_screenshot,
    "run_simulation": run_simulation,
    "get_garment_info": get_garment_info,
    "reset_garment": reset_garment,
}


def handle_command(data):
    """
    Parse and execute command from client.
    
    Args:
        data: JSON string with command and parameters
    
    Returns:
        dict: Response to send back to client
    """
    global request_count
    request_count += 1
    
    try:
        # Parse JSON
        request = json.loads(data)
        
        # Handle handshake format: {"ping": "clo"}
        if "ping" in request and request.get("ping") == "clo":
            return {"success": True, "pong": "clo", "service": "CLO Bridge Listener", "version": "2.0"}
        
        cmd = request.get("cmd")
        
        if not cmd:
            return {"success": False, "error": "Missing 'cmd' field"}
        
        log(f"Received command: {cmd} (request #{request_count})")
        
        # Special commands
        if cmd == "ping":
            # Support both old format and new handshake format
            return {"success": True, "message": "pong", "pong": "clo", "uptime_requests": request_count}
        
        if cmd == "shutdown":
            global running
            running = False
            return {"success": True, "message": "Server shutting down"}
        
        if cmd == "list_commands":
            return {
                "success": True,
                "commands": list(COMMANDS.keys()) + ["ping", "shutdown", "list_commands"]
            }
        
        # Dispatch to handler
        handler = COMMANDS.get(cmd)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown command: {cmd}",
                "available_commands": list(COMMANDS.keys())
            }
        
        # Extract parameters (everything except 'cmd')
        params = {k: v for k, v in request.items() if k != "cmd"}
        
        # Execute command
        result = handler(**params)
        return result
        
    except json.JSONDecodeError as e:
        log(f"Invalid JSON: {e}", "ERROR")
        return {"success": False, "error": f"Invalid JSON: {str(e)}"}
    
    except TypeError as e:
        log(f"Invalid parameters: {e}", "ERROR")
        return {"success": False, "error": f"Invalid parameters: {str(e)}"}
    
    except Exception as e:
        log(f"Command execution failed: {e}", "ERROR")
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def start_server():
    """Start TCP socket server and listen for commands"""
    global running
    
    # Create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        # Bind and listen
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        server_socket.settimeout(1.0)  # Allow periodic checks of 'running' flag
        
        log(f"CLO Bridge Listener started on {HOST}:{PORT}", "INFO")
        log(f"Waiting for connections... (Press Ctrl+C to stop)", "INFO")
        log(f"Available commands: {', '.join(COMMANDS.keys())}", "INFO")
        
        while running:
            try:
                # Accept connection
                client_socket, address = server_socket.accept()
                log(f"Connection from {address}", "INFO")
                
                try:
                    # Receive data
                    raw = client_socket.recv(BUFFER_SIZE)
                    data = raw.decode('utf-8')
                    
                    if not data:
                        log("Empty request received", "WARN")
                        continue
                    
                    log(f"Request: {data[:200]}...", "DEBUG")

                    # Immediate pong for handshake probes
                    if b'"ping":"clo"' in raw:
                        try:
                            client_socket.sendall(b'{"pong":"clo"}\n')
                        except Exception:
                            pass
                        # Continue loop; do not process further for this request
                        continue
                    
                    # Handle command
                    response = handle_command(data)
                    
                    # Send response
                    response_json = json.dumps(response, indent=2)
                    client_socket.sendall(response_json.encode('utf-8'))
                    
                    log(f"Response sent: {response.get('success', 'unknown')}", "INFO")
                    
                except Exception as e:
                    log(f"Error handling client: {e}", "ERROR")
                    error_response = {
                        "success": False,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                    try:
                        client_socket.sendall(json.dumps(error_response).encode('utf-8'))
                    except:
                        pass
                
                finally:
                    client_socket.close()
            
            except socket.timeout:
                # Timeout allows checking 'running' flag periodically
                continue
            
            except KeyboardInterrupt:
                log("Keyboard interrupt received", "INFO")
                running = False
                break
        
        log("Server stopped", "INFO")
    
    except OSError as e:
        log(f"Failed to bind to {HOST}:{PORT}: {e}", "ERROR")
        log(f"Is the port already in use?", "ERROR")
        return False
    
    except Exception as e:
        log(f"Server error: {e}", "ERROR")
        log(traceback.format_exc(), "ERROR")
        return False
    
    finally:
        server_socket.close()
        log("Socket closed", "INFO")
    
    return True


# Entry point
if __name__ == "__main__":
    log("=" * 60, "INFO")
    log("CLO Bridge Listener - RAGGITY ZYZTEM 2.0", "INFO")
    log("=" * 60, "INFO")
    log(f"Python version: {sys.version}", "INFO")
    log(f"Host: {HOST}, Port: {PORT}", "INFO")
    log("", "INFO")
    
    success = start_server()
    
    if success:
        log("Server exited cleanly", "INFO")
    else:
        log("Server exited with errors", "ERROR")


