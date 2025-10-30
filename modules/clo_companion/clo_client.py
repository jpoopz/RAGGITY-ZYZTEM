"""
CLO Client

External client for connecting to CLO Bridge Listener.
Used by RAGGITY to send commands to CLO 3D software.

Usage:
    from modules.clo_companion.clo_client import CLOClient
    
    client = CLOClient()
    client.connect()
    
    result = client.import_garment("C:/Projects/shirt.zprj")
    if result["ok"]:
        print("Garment imported successfully")
"""

import socket
import json
import time
from typing import Dict, Any, Optional

from .config import CLO_HOST, CLO_PORT, CLO_TIMEOUT, MAX_RETRIES, RETRY_DELAY


class CLOClientError(Exception):
    """Base exception for CLO client errors"""
    pass


class CLOConnectionError(CLOClientError):
    """Raised when connection to CLO bridge fails"""
    pass


class CLOCommandError(CLOClientError):
    """Raised when command execution fails"""
    pass


class CLOClient:
    """
    Client for communicating with CLO Bridge Listener.
    
    Connects to the TCP listener running inside CLO's Python environment
    and sends JSON commands.
    """
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None, 
                 timeout: Optional[int] = None):
        """
        Initialize CLO client.
        
        Args:
            host: CLO listener host (default: from config)
            port: CLO listener port (default: from config)
            timeout: Connection timeout in seconds (default: from config)
        """
        self.host = host or CLO_HOST
        self.port = port or CLO_PORT
        self.timeout = timeout or CLO_TIMEOUT
        self.connected = False
        self._socket = None
    
    def connect(self, retries: Optional[int] = None) -> Dict[str, Any]:
        """
        Test connection to CLO bridge listener with exponential backoff.
        
        Args:
            retries: Number of connection retries (default: from config)
        
        Returns:
            dict: {ok: bool, data: dict, error: str, help: str (on error)}
        """
        max_retries = retries if retries is not None else MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                # Send ping command
                result = self.send({"cmd": "ping"})
                
                if result["ok"]:
                    self.connected = True
                    return {
                        "ok": True,
                        "data": {
                            "host": self.host,
                            "port": self.port,
                            "message": "Connected to CLO bridge",
                            "ping_response": result.get("data", {}),
                            "attempts": attempt + 1
                        },
                        "error": None
                    }
                else:
                    error = result.get("error", "Unknown error")
                    
                    # Check if it's a connection refused error
                    if "Connection refused" in error or "refused" in error.lower():
                        if attempt < max_retries - 1:
                            # Exponential backoff: 1s, 2s, 4s
                            delay = RETRY_DELAY * (2 ** attempt)
                            time.sleep(delay)
                            continue
                        
                        return {
                            "ok": False,
                            "data": None,
                            "error": f"Cannot connect to CLO bridge on {self.host}:{self.port}",
                            "help": self._get_connection_help()
                        }
                    
                    if attempt < max_retries - 1:
                        delay = RETRY_DELAY * (2 ** attempt)
                        time.sleep(delay)
                        continue
                    
                    return {
                        "ok": False,
                        "data": None,
                        "error": f"Connection test failed: {error}",
                        "help": self._get_connection_help()
                    }
            
            except ConnectionRefusedError:
                if attempt < max_retries - 1:
                    delay = RETRY_DELAY * (2 ** attempt)
                    time.sleep(delay)
                    continue
                
                self.connected = False
                return {
                    "ok": False,
                    "data": None,
                    "error": f"Connection refused on {self.host}:{self.port}",
                    "help": self._get_connection_help()
                }
            
            except socket.timeout:
                if attempt < max_retries - 1:
                    delay = RETRY_DELAY * (2 ** attempt)
                    time.sleep(delay)
                    continue
                
                self.connected = False
                return {
                    "ok": False,
                    "data": None,
                    "error": f"Connection timeout after {self.timeout}s (tried {max_retries} times)",
                    "help": "CLO may be slow to respond. Try increasing CLO_TIMEOUT."
                }
            
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = RETRY_DELAY * (2 ** attempt)
                    time.sleep(delay)
                    continue
                
                self.connected = False
                return {
                    "ok": False,
                    "data": None,
                    "error": f"Connection failed: {str(e)}",
                    "help": self._get_connection_help()
                }
        
        return {
            "ok": False,
            "data": None,
            "error": "Max retries exceeded",
            "help": self._get_connection_help()
        }
    
    def _get_connection_help(self) -> str:
        """
        Get helpful error message for connection failures.
        
        Returns:
            str: Multi-line help message
        """
        return f"""
Troubleshooting Steps:

1. Is CLO 3D running?
   - Launch CLO 3D application

2. Is the bridge listener started in CLO?
   - In CLO: File > Script > Run Script...
   - Select: modules/clo_companion/clo_bridge_listener.py
   - Look for message: "CLO Bridge listening on {self.host}:{self.port}"

3. Check firewall settings
   - Ensure localhost connections are allowed
   - Port {self.port} should not be blocked

4. Verify port is not in use
   - Try changing CLO_PORT environment variable
   - Check if another application is using port {self.port}

5. Check CLO's Python console for errors
   - Look for error messages in the script output window
"""
    
    def send(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send command to CLO bridge listener.
        
        Args:
            command: Command dictionary with 'cmd' field and parameters
        
        Returns:
            dict: {ok: bool, data: dict, error: str}
        """
        sock = None
        
        try:
            # Validate command
            if not isinstance(command, dict):
                return {
                    "ok": False,
                    "data": None,
                    "error": "Command must be a dictionary"
                }
            
            if "cmd" not in command:
                return {
                    "ok": False,
                    "data": None,
                    "error": "Command must contain 'cmd' field"
                }
            
            # Create socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            # Connect
            sock.connect((self.host, self.port))
            
            # Serialize and send command as newline-delimited JSON
            command_json = json.dumps(command) + "\n"
            sock.sendall(command_json.encode('utf-8'))
            
            # Receive response until newline (NDJSON protocol)
            response_data = b""
            while b"\n" not in response_data:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response_data += chunk

            if not response_data:
                return {
                    "ok": False,
                    "data": None,
                    "error": "No response from CLO bridge"
                }
            
            # Split at first newline and parse JSON
            line = response_data.split(b"\n", 1)[0]
            try:
                response = json.loads(line.decode('utf-8'))
            except json.JSONDecodeError as e:
                return {
                    "ok": False,
                    "data": None,
                    "error": f"Invalid JSON response: {str(e)}"
                }
            
            # Convert bridge response format to client format
            if response.get("success"):
                return {
                    "ok": True,
                    "data": response,
                    "error": None
                }
            else:
                return {
                    "ok": False,
                    "data": response,
                    "error": response.get("error", "Command failed")
                }
        
        except socket.timeout:
            return {
                "ok": False,
                "data": None,
                "error": f"Connection timeout after {self.timeout}s"
            }
        
        except ConnectionRefusedError:
            return {
                "ok": False,
                "data": None,
                "error": f"Connection refused. Is CLO bridge listener running on {self.host}:{self.port}?"
            }
        
        except socket.error as e:
            return {
                "ok": False,
                "data": None,
                "error": f"Socket error: {str(e)}"
            }
        
        except Exception as e:
            return {
                "ok": False,
                "data": None,
                "error": f"Unexpected error: {str(e)}"
            }
        
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass
    
    def ping(self) -> Dict[str, Any]:
        """
        Send ping to check if bridge is alive.
        
        Returns:
            dict: {ok: bool, data: dict, error: str}
        """
        return self.send({"cmd": "ping"})
    
    def list_commands(self) -> Dict[str, Any]:
        """
        Get list of available commands from bridge.
        
        Returns:
            dict: {ok: bool, data: dict with 'commands' list, error: str}
        """
        return self.send({"cmd": "list_commands"})
    
    def import_garment(self, path: str) -> Dict[str, Any]:
        """
        Import a garment file into CLO.
        
        Args:
            path: Absolute path to garment file (.zprj, .obj, .fbx, etc.)
        
        Returns:
            dict: {ok: bool, data: dict, error: str}
        """
        if not path:
            return {
                "ok": False,
                "data": None,
                "error": "Path is required"
            }
        
        return self.send({
            "cmd": "import_garment",
            "path": path
        })
    
    def export_garment(self, path: str, format: str = "zprj") -> Dict[str, Any]:
        """
        Export current garment to file.
        
        Args:
            path: Destination file path
            format: Export format (zprj, obj, fbx, gltf, etc.)
        
        Returns:
            dict: {ok: bool, data: dict, error: str}
        """
        if not path:
            return {
                "ok": False,
                "data": None,
                "error": "Path is required"
            }
        
        return self.send({
            "cmd": "export_garment",
            "path": path,
            "format": format
        })
    
    def take_screenshot(self, path: str, width: int = 1280, height: int = 720) -> Dict[str, Any]:
        """
        Capture screenshot of CLO 3D viewport.
        
        Args:
            path: Destination image file path (.png, .jpg)
            width: Image width in pixels (default: 1280)
            height: Image height in pixels (default: 720)
        
        Returns:
            dict: {ok: bool, data: dict, error: str}
        """
        if not path:
            return {
                "ok": False,
                "data": None,
                "error": "Path is required"
            }
        
        if width <= 0 or height <= 0:
            return {
                "ok": False,
                "data": None,
                "error": "Width and height must be positive integers"
            }
        
        return self.send({
            "cmd": "take_screenshot",
            "path": path,
            "width": width,
            "height": height
        })
    
    def run_simulation(self, steps: int = 50, duration: Optional[float] = None) -> Dict[str, Any]:
        """
        Run physics simulation in CLO.
        
        Args:
            steps: Number of simulation steps (default: 50)
            duration: Simulation duration in seconds (overrides steps if provided)
        
        Returns:
            dict: {ok: bool, data: dict, error: str}
        """
        if steps <= 0 and duration is None:
            return {
                "ok": False,
                "data": None,
                "error": "Steps must be positive or duration must be provided"
            }
        
        cmd = {
            "cmd": "run_simulation",
            "steps": steps
        }
        
        if duration is not None:
            if duration <= 0:
                return {
                    "ok": False,
                    "data": None,
                    "error": "Duration must be positive"
                }
            cmd["duration"] = duration
        
        return self.send(cmd)
    
    def get_garment_info(self) -> Dict[str, Any]:
        """
        Get information about current garment/project in CLO.
        
        Returns:
            dict: {ok: bool, data: dict with garment info, error: str}
        """
        return self.send({"cmd": "get_garment_info"})
    
    def reset_garment(self) -> Dict[str, Any]:
        """
        Reset simulation and return garment to initial state.
        
        Returns:
            dict: {ok: bool, data: dict, error: str}
        """
        return self.send({"cmd": "reset_garment"})
    
    def shutdown(self) -> Dict[str, Any]:
        """
        Shutdown the CLO bridge listener.
        
        Use with caution - this will stop the listener service.
        
        Returns:
            dict: {ok: bool, data: dict, error: str}
        """
        result = self.send({"cmd": "shutdown"})
        if result["ok"]:
            self.connected = False
        return result
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.connected = False
        return False
    
    def __repr__(self):
        """String representation"""
        status = "connected" if self.connected else "disconnected"
        return f"<CLOClient {self.host}:{self.port} ({status})>"


# Convenience function for quick one-off commands
def send_command(command: Dict[str, Any], host: Optional[str] = None, 
                port: Optional[int] = None, timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Send a single command to CLO bridge without persistent connection.
    
    Args:
        command: Command dictionary
        host: CLO listener host (optional)
        port: CLO listener port (optional)
        timeout: Connection timeout (optional)
    
    Returns:
        dict: {ok: bool, data: dict, error: str}
    """
    client = CLOClient(host=host, port=port, timeout=timeout)
    return client.send(command)


if __name__ == "__main__":
    # Simple smoke test CLI for manual debugging
    import argparse

    parser = argparse.ArgumentParser(description="CLOClient smoke test")
    parser.add_argument("--host", default=CLO_HOST, help="CLO bridge host")
    parser.add_argument("--port", type=int, default=CLO_PORT, help="CLO bridge port")
    parser.add_argument("--timeout", type=int, default=CLO_TIMEOUT, help="Timeout seconds")
    parser.add_argument("--cmd", default="ping", help="Command name (default: ping)")
    args, unknown = parser.parse_known_args()

    client = CLOClient(host=args.host, port=args.port, timeout=args.timeout)
    print(f"Connecting to {args.host}:{args.port} ...")
    res = client.connect()
    print("connect:", res)
    if not res.get("ok"):
        raise SystemExit(1)

    # Build command
    cmd = {"cmd": args.cmd}
    # Allow extra key=value pairs
    for kv in unknown:
        if "=" in kv:
            k, v = kv.split("=", 1)
            # try to parse numbers/bools
            if v.isdigit():
                v = int(v)
            elif v.lower() in ("true", "false"):
                v = v.lower() == "true"
            cmd[k.lstrip("-")] = v

    print("sending:", cmd)
    out = client.send(cmd)
    print("response:", out)

