"""
Overlap Resolver - Detects and stops duplicate Julian Assistant Suite instances
Ensures clean startup by terminating conflicting processes
"""

import os
import sys
import time
import socket
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "Logs")
os.makedirs(LOG_DIR, exist_ok=True)

try:
    import psutil
except ImportError:
    psutil = None
    print("WARNING: psutil not installed. Install with: pip install psutil")

try:
    from logger import log
except ImportError:
    def log(msg, category="OVERLAP", level="INFO", print_to_console=True):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{category}] {msg}\n"
        log_file = os.path.join(LOG_DIR, "overlap_check.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        if print_to_console:
            print(f"[{category}] {msg}")


# Target processes to monitor
TARGET_SCRIPTS = [
    "RAG_Control_Panel.py",
    "rag_api.py",
    "clo_api.py",
    "cloud_bridge.py",
    "background_services.py",
]

TARGET_PROCESSES = [
    "ollama",
]

# Module port mappings
MODULE_PORTS = {
    "rag_api": 5000,
    "clo_api": 5001,
    "cloud_bridge": 5002,
}


def check_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    """Check if a port is in use"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            result = s.connect_ex((host, port))
            return result == 0
    except:
        return False


def get_port_process(port: int) -> Optional[int]:
    """Get the PID of the process using a port (Windows)"""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        for line in result.stdout.split('\n'):
            if f":{port} " in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    try:
                        return int(pid)
                    except:
                        pass
    except:
        pass
    return None


def find_duplicate_processes() -> Dict[str, List[Tuple]]:
    """
    Find duplicate processes for target scripts
    
    Returns:
        Dictionary mapping target name to list of (process, pid, start_time) tuples
    """
    if not psutil:
        log("psutil not available - cannot detect duplicates", "OVERLAP", level="WARNING")
        return {}
    
    active = {}
    
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time', 'exe']):
            try:
                cmdline = proc.info.get('cmdline', []) or []
                cmd_str = " ".join(str(c) for c in cmdline).lower()
                
                # Check for target scripts
                for target in TARGET_SCRIPTS:
                    target_lower = target.lower()
                    # Check if target script is in command line
                    if target_lower in cmd_str and "python" in cmd_str:
                        if target not in active:
                            active[target] = []
                        active[target].append((
                            proc,
                            proc.info['pid'],
                            proc.info['create_time']
                        ))
                
                # Check for target process names
                proc_name = (proc.info.get('name') or '').lower()
                exe = (proc.info.get('exe') or '').lower()
                
                for target in TARGET_PROCESSES:
                    if target in proc_name or target in exe or target in cmd_str:
                        if target not in active:
                            active[target] = []
                        active[target].append((
                            proc,
                            proc.info['pid'],
                            proc.info['create_time']
                        ))
            
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                log(f"Error checking process {proc}: {e}", "OVERLAP", level="WARNING")
                continue
    
    except Exception as e:
        log(f"Error iterating processes: {e}", "OVERLAP", level="ERROR")
        return {}
    
    return active


def terminate_process_safely(proc, timeout: int = 3) -> bool:
    """
    Safely terminate a process
    
    Args:
        proc: psutil.Process or PID
        timeout: Seconds to wait for graceful termination
    
    Returns:
        True if terminated successfully
    """
    try:
        if isinstance(proc, int):
            proc = psutil.Process(proc)
        
        pid = proc.pid
        
        try:
            # Try graceful termination
            proc.terminate()
            proc.wait(timeout=timeout)
            log(f"Terminated process {pid} gracefully", "OVERLAP")
            return True
        except psutil.TimeoutExpired:
            # Force kill if graceful termination failed
            try:
                proc.kill()
                proc.wait(timeout=1)
                log(f"Force killed process {pid}", "OVERLAP")
                return True
            except:
                log(f"Failed to kill process {pid}", "OVERLAP", level="WARNING")
                return False
        except psutil.NoSuchProcess:
            log(f"Process {pid} already terminated", "OVERLAP")
            return True
    
    except Exception as e:
        log(f"Error terminating process: {e}", "OVERLAP", level="ERROR")
        return False


def check_port_conflicts() -> Dict[str, int]:
    """
    Check for port conflicts
    
    Returns:
        Dictionary mapping port to PID of conflicting process
    """
    conflicts = {}
    
    for module, port in MODULE_PORTS.items():
        if check_port_in_use(port):
            pid = get_port_process(port)
            if pid:
                conflicts[port] = pid
                log(f"Port {port} ({module}) in use by PID {pid}", "OVERLAP")
    
    return conflicts


def resolve_overlaps(skip_control_panel: bool = False) -> Dict:
    """
    Resolve overlapping instances
    
    Args:
        skip_control_panel: If True, don't terminate Control Panel instances
    
    Returns:
        Dictionary with resolution results
    """
    log("=== Starting Overlap Resolution ===", "OVERLAP")
    log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "OVERLAP")
    
    results = {
        "found": {},
        "terminated": [],
        "kept": [],
        "port_conflicts": {},
        "errors": []
    }
    
    if not psutil:
        log("psutil not available - skipping process detection", "OVERLAP", level="WARNING")
        results["errors"].append("psutil not installed")
        return results
    
    # Find duplicates
    active = find_duplicate_processes()
    results["found"] = {k: len(v) for k, v in active.items()}
    
    # Resolve duplicates
    for target, procs in active.items():
        if len(procs) == 0:
            continue
        
        # Skip Control Panel if requested (we want to keep it running for graceful restart)
        if skip_control_panel and "RAG_Control_Panel" in target:
            log(f"Skipping {target} termination (graceful restart)", "OVERLAP")
            continue
        
        if len(procs) > 1:
            # Sort by start time (keep most recent)
            procs_sorted = sorted(procs, key=lambda x: x[2])
            keep = procs_sorted[-1]  # Most recent
            
            log(f"Found {len(procs)} instances of {target}, keeping most recent (PID {keep[1]})", "OVERLAP")
            
            # Terminate older instances
            for proc, pid, _ in procs_sorted[:-1]:
                log(f"Terminating duplicate {target} (PID {pid})", "OVERLAP")
                if terminate_process_safely(proc):
                    results["terminated"].append({
                        "target": target,
                        "pid": pid
                    })
                else:
                    results["errors"].append(f"Failed to terminate {target} (PID {pid})")
            
            results["kept"].append({
                "target": target,
                "pid": keep[1]
            })
        else:
            # Only one instance - keep it
            proc, pid, _ = procs[0]
            results["kept"].append({
                "target": target,
                "pid": pid
            })
            log(f"Single instance of {target} running (PID {pid})", "OVERLAP")
    
    # Check port conflicts
    port_conflicts = check_port_conflicts()
    results["port_conflicts"] = port_conflicts
    
    # Resolve port conflicts (terminate processes using ports)
    for port, pid in port_conflicts.items():
        # Don't terminate if it's one of our kept processes
        is_kept = any(p["pid"] == pid for p in results["kept"])
        
        if not is_kept:
            log(f"Terminating process {pid} blocking port {port}", "OVERLAP")
            if terminate_process_safely(pid):
                results["terminated"].append({
                    "target": f"port_{port}",
                    "pid": pid
                })
    
    log("=== Overlap Resolution Complete ===", "OVERLAP")
    
    return results


def verify_system_ready() -> Tuple[bool, List[str]]:
    """
    Verify system is ready for launch
    
    Returns:
        Tuple of (is_ready, list_of_warnings)
    """
    warnings = []
    
    if not psutil:
        warnings.append("psutil not available - cannot verify processes")
        return False, warnings
    
    # Check for duplicates
    active = find_duplicate_processes()
    
    for target, procs in active.items():
        if len(procs) > 1:
            warnings.append(f"Multiple instances of {target} detected ({len(procs)} instances)")
    
    # Check port availability
    for module, port in MODULE_PORTS.items():
        if check_port_in_use(port):
            pid = get_port_process(port)
            warnings.append(f"Port {port} ({module}) already in use by PID {pid}")
    
    is_ready = len(warnings) == 0
    
    if is_ready:
        log("✅ System ready - no overlapping instances", "OVERLAP")
    else:
        log(f"⚠️ System has {len(warnings)} warnings: {warnings}", "OVERLAP", level="WARNING")
    
    return is_ready, warnings


if __name__ == "__main__":
    # Run overlap resolution
    print("🔍 Checking for overlapping instances...")
    
    results = resolve_overlaps()
    
    print(f"\n📊 Results:")
    print(f"   Found: {len(results['found'])} target types")
    print(f"   Terminated: {len(results['terminated'])} processes")
    print(f"   Kept: {len(results['kept'])} processes")
    print(f"   Port conflicts: {len(results['port_conflicts'])}")
    
    if results['errors']:
        print(f"   Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"      - {error}")
    
    is_ready, warnings = verify_system_ready()
    
    if is_ready:
        print("\n✅ No overlapping instances — safe to launch Control Panel.")
    else:
        print(f"\n⚠️ System has {len(warnings)} warnings:")
        for warning in warnings:
            print(f"   - {warning}")

