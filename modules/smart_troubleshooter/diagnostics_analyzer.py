"""
Diagnostics Analyzer - Parses logs for errors, tracebacks, and warnings
Maps issues to categories and severity levels

TEST PLAN:
- Case 1: vector_store = "faiss" → no chroma nag
- Case 2: fastapi present, flask missing → API OK, no Flask nag
- Case 3: CLO listener not running → clo_bridge = not_reachable + recommendation shown
- Case 4: After running clo_bridge_listener.py in CLO → clo_bridge = reachable
"""

import os
import sys
import re
import socket
import importlib
import importlib.util as _spec
from importlib import metadata
import random
import time
import shutil
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

# Optional: psutil for RAM checks (graceful fallback if not available)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Safe I/O for GUI mode
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)
from core.io_safety import safe_reconfigure_streams
safe_reconfigure_streams()

try:
    from logger import log
except ImportError:
    def log(msg, category="TROUBLE"):
        print(f"[{category}] {msg}")

# Load unified settings for context-aware checks
try:
    from core.settings import load_settings
    SETTINGS = load_settings()
except ImportError:
    SETTINGS = None
    log("Warning: Could not load unified settings", "TROUBLE")

# Import CLO config
try:
    from modules.clo_companion.config import CLO_HOST, CLO_PORT
except ImportError:
    CLO_HOST = "127.0.0.1"
    CLO_PORT = 51235

class DiagnosticsAnalyzer:
    """Analyzes log files for errors, warnings, and issues"""
    
    def __init__(self):
        self.logs_dir = os.path.join(BASE_DIR, "Logs")
        self.rules_file = os.path.join(os.path.dirname(__file__), "troubleshooter_rules.json")
        self.rules = self._load_rules()
        
        # State tracking for telemetry breadcrumbs
        self._last_clo_state = None
        self._last_api_state = None
        
        log("DiagnosticsAnalyzer initialized", "TROUBLE")
    
    def _load_rules(self) -> Dict:
        """Load troubleshooting rules from JSON"""
        try:
            import json
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"error_patterns": {}, "warning_patterns": {}, "info_patterns": {}}
        except Exception as e:
            log(f"Error loading rules: {e}", "TROUBLE", level="ERROR")
            return {"error_patterns": {}, "warning_patterns": {}, "info_patterns": {}}
    
    def analyze_logs(self, hours: int = 24) -> List[Dict]:
        """
        Analyze recent log files for issues
        
        Args:
            hours: Time window to analyze (default: 24 hours)
        
        Returns:
            List of detected issues with metadata
        """
        issues = []
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Scan all log files in Logs/
        if not os.path.exists(self.logs_dir):
            return issues
        
        for log_file in Path(self.logs_dir).glob("*.log"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_time:
                    continue  # Skip old files
                
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                # Analyze each line
                for line_num, line in enumerate(lines, 1):
                    issue = self._analyze_line(line, str(log_file), line_num)
                    if issue:
                        issues.append(issue)
            
            except Exception as e:
                log(f"Error analyzing {log_file}: {e}", "TROUBLE", level="WARNING")
        
        # Sort by severity and timestamp
        issues.sort(key=lambda x: (x.get("severity_score", 0), x.get("timestamp", "")), reverse=True)
        
        return issues
    
    def _analyze_line(self, line: str, file_path: str, line_num: int) -> Optional[Dict]:
        """Analyze a single log line for issues"""
        
        # Check for ERROR level
        if "[ERROR]" in line or "ERROR:" in line:
            return self._parse_error(line, file_path, line_num, "ERROR")
        
        # Check for traceback
        if "Traceback (most recent call last)" in line or "  File " in line:
            return self._parse_traceback(line, file_path, line_num)
        
        # Check for WARNING
        if "[WARNING]" in line or "WARN:" in line:
            return self._parse_warning(line, file_path, line_num)
        
        # Check error patterns from rules
        for error_type, rule in self.rules.get("error_patterns", {}).items():
            pattern = rule.get("pattern", "")
            if pattern:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    return self._build_issue_dict(
                        line, file_path, line_num,
                        error_type, "ERROR", rule, match
                    )
        
        # Check warning patterns
        for warning_type, rule in self.rules.get("warning_patterns", {}).items():
            pattern = rule.get("pattern", "")
            if pattern:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    return self._build_issue_dict(
                        line, file_path, line_num,
                        warning_type, "WARNING", rule, match
                    )
        
        return None
    
    def _parse_error(self, line: str, file_path: str, line_num: int, level: str) -> Dict:
        """Parse an ERROR line"""
        timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
        timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().isoformat()
        
        return {
            "type": "Error",
            "severity": level,
            "severity_score": 3,
            "message": line.strip(),
            "file": os.path.basename(file_path),
            "line": line_num,
            "timestamp": timestamp,
            "category": "error",
            "auto_fixable": False
        }
    
    def _parse_traceback(self, line: str, file_path: str, line_num: int) -> Dict:
        """Parse a traceback line"""
        return {
            "type": "Traceback",
            "severity": "ERROR",
            "severity_score": 4,
            "message": line.strip(),
            "file": os.path.basename(file_path),
            "line": line_num,
            "timestamp": datetime.now().isoformat(),
            "category": "traceback",
            "auto_fixable": False
        }
    
    def _parse_warning(self, line: str, file_path: str, line_num: int) -> Dict:
        """Parse a WARNING line"""
        timestamp_match = re.search(r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]', line)
        timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().isoformat()
        
        return {
            "type": "Warning",
            "severity": "WARNING",
            "severity_score": 2,
            "message": line.strip(),
            "file": os.path.basename(file_path),
            "line": line_num,
            "timestamp": timestamp,
            "category": "warning",
            "auto_fixable": False
        }
    
    def _build_issue_dict(self, line: str, file_path: str, line_num: int,
                         issue_type: str, severity: str, rule: Dict, match) -> Dict:
        """Build issue dictionary from pattern match"""
        severity_map = {"ERROR": 3, "WARNING": 2, "INFO": 1}
        severity_score = severity_map.get(severity, 1)
        
        # Extract capture groups
        groups = match.groups()
        rule_data = rule.copy()
        
        # Replace placeholders in cursor_prompt
        cursor_prompt = rule_data.get("cursor_prompt", "")
        if cursor_prompt and groups:
            for i, group in enumerate(groups):
                cursor_prompt = cursor_prompt.replace(f"{{group_{i}}}", group)
            # Common patterns
            if "{module}" in cursor_prompt and groups:
                cursor_prompt = cursor_prompt.replace("{module}", groups[0])
            if "{file}" in cursor_prompt and len(groups) > 0:
                cursor_prompt = cursor_prompt.replace("{file}", groups[0])
            if "{port}" in cursor_prompt and len(groups) > 0:
                cursor_prompt = cursor_prompt.replace("{port}", groups[0])
        
        return {
            "type": issue_type,
            "severity": severity,
            "severity_score": severity_score,
            "message": line.strip(),
            "file": os.path.basename(file_path),
            "line": line_num,
            "timestamp": datetime.now().isoformat(),
            "category": rule_data.get("category", "unknown"),
            "auto_fixable": rule_data.get("auto_fix") is not None,
            "auto_fix_type": rule_data.get("auto_fix"),
            "fix_command": rule_data.get("fix_command"),
            "cursor_prompt": cursor_prompt,
            "matched_groups": list(groups)
        }
    
    def get_issue_summary(self, issues: List[Dict]) -> Dict:
        """Get summary statistics of issues with context-aware dependency checks"""
        if not issues:
            summary = {
                "total": 0,
                "errors": 0,
                "warnings": 0,
                "auto_fixable": 0,
                "severity_score": 0,
                "missing_deps": [],
                "recommendations": []
            }
        else:
            errors = sum(1 for i in issues if i.get("severity") == "ERROR")
            warnings = sum(1 for i in issues if i.get("severity") == "WARNING")
            auto_fixable = sum(1 for i in issues if i.get("auto_fixable", False))
            avg_severity = sum(i.get("severity_score", 0) for i in issues) / len(issues)
            
            summary = {
                "total": len(issues),
                "errors": errors,
                "warnings": warnings,
                "auto_fixable": auto_fixable,
                "avg_severity": avg_severity,
                "severity_score": avg_severity,
                "missing_deps": [],
                "recommendations": []
            }
        
        # Context-aware dependency checks
        missing_deps, recommendations = self._check_dependencies()
        summary["missing_deps"] = missing_deps
        summary["recommendations"] = recommendations
        
        # CLO Bridge check
        clo_status, clo_recommendation = self._check_clo_bridge()
        summary["clo_bridge"] = clo_status
        if clo_recommendation:
            summary["recommendations"].append(clo_recommendation)
        
        # System resource checks
        system_hints = self._check_system_resources()
        if system_hints:
            summary["system_hints"] = system_hints
            summary["recommendations"].extend(system_hints)
        
        # Log diagnostics context
        if SETTINGS:
            log(f"Diagnostics context: vector_store={SETTINGS.vector_store}, Python={sys.version_info.major}.{sys.version_info.minor}", "TROUBLE")
        
        return summary
    
    def pkg_ok(self, name: str, min_ver: str | None = None) -> Tuple[bool, str]:
        """
        Robust package check with version and import validation.
        
        Args:
            name: Package name
            min_ver: Optional minimum version requirement
            
        Returns:
            (success: bool, detail: str)
            detail can be: version string, "not_installed", "outdated:X < Y", "import_error:ExceptionType"
        """
        if _spec.find_spec(name) is None:
            return (False, "not_installed")
        
        try:
            ver = metadata.version(name)
        except Exception:
            ver = "unknown"
        
        if min_ver:
            try:
                from packaging.version import Version
                if Version(ver) < Version(min_ver):
                    return (False, f"outdated:{ver} < {min_ver}")
            except Exception:
                pass
        
        # Optional import smoke test (avoids slow side-effects)
        try:
            importlib.import_module(name)
        except Exception as e:
            return (False, f"import_error:{e.__class__.__name__}")
        
        return (True, ver)
    
    def _has_package(self, pkg: str) -> bool:
        """Check if a package is installed (simple check for backward compat)"""
        ok, _ = self.pkg_ok(pkg)
        return ok
    
    def _check_dependencies(self) -> Tuple[List[str], List[str]]:
        """
        Context-aware dependency check with version validation
        Returns: (missing_deps, recommendations)
        """
        missing = []
        recommendations = []
        
        # Vector store check (context-aware)
        if SETTINGS and SETTINGS.vector_store == "chroma":
            ok, detail = self.pkg_ok("chromadb", min_ver="0.4.0")
            if not ok:
                missing.append("chromadb")
                if detail == "not_installed":
                    recommendations.append("Install ChromaDB: pip install chromadb")
                elif detail.startswith("outdated:"):
                    recommendations.append(f"Upgrade ChromaDB: pip install --upgrade chromadb ({detail})")
                elif detail.startswith("import_error:"):
                    recommendations.append(f"ChromaDB import broken ({detail}): reinstall with pip install --force-reinstall chromadb")
        # Don't nag about chromadb if using FAISS
        
        # API backend check (Flask OR FastAPI, not both required)
        flask_ok, flask_detail = self.pkg_ok("flask", min_ver="3.0.0")
        fastapi_ok, fastapi_detail = self.pkg_ok("fastapi")
        
        if not (flask_ok or fastapi_ok):
            # Neither is present - recommend Flask (our primary API)
            missing.append("flask")
            recommendations.append("Install Flask: pip install flask flask-cors")
        elif not flask_ok and fastapi_ok:
            # FastAPI present but Flask missing - check if Flask API is used
            flask_api_path = os.path.join(BASE_DIR, "modules", "academic_rag", "api.py")
            if os.path.exists(flask_api_path):
                try:
                    with open(flask_api_path, 'r', encoding='utf-8') as f:
                        content = f.read(500)  # Check first 500 chars
                        if "from flask import" in content:
                            if flask_detail == "not_installed":
                                recommendations.append("Flask API detected but Flask not installed: pip install flask flask-cors")
                            elif flask_detail.startswith("outdated:"):
                                recommendations.append(f"Flask API needs upgrade: pip install --upgrade flask ({flask_detail})")
                            elif flask_detail.startswith("import_error:"):
                                recommendations.append(f"Flask import broken ({flask_detail}): pip install --force-reinstall flask")
                except Exception:
                    pass
        
        # Essential packages with version checks
        essential = {
            "requests": ("2.31.0", "Install requests: pip install requests>=2.31.0"),
            "pyyaml": ("6.0.0", "Install PyYAML: pip install pyyaml>=6.0.0"),
            "numpy": ("1.24.0", "Install NumPy: pip install numpy>=1.24.0")
        }
        
        for pkg, (min_ver, hint) in essential.items():
            ok, detail = self.pkg_ok(pkg, min_ver=min_ver)
            if not ok:
                missing.append(pkg)
                if detail == "not_installed":
                    recommendations.append(hint)
                elif detail.startswith("outdated:"):
                    recommendations.append(f"Upgrade {pkg}: pip install --upgrade {pkg} ({detail})")
                elif detail.startswith("import_error:"):
                    recommendations.append(f"{pkg} broken ({detail}): pip install --force-reinstall {pkg}")
        
        return missing, recommendations
    
    def _tcp_reachable(self, host: str, port: int, attempts: int = 3, 
                       base_delay: float = 0.25, timeout: float = 0.8) -> Tuple[bool, Optional[str]]:
        """
        Smart TCP reachability check with backoff and IPv4/IPv6 fallbacks.
        
        Features:
        - Exponential backoff with jitter for transient failures
        - IPv6/localhost fallbacks for loopback addresses
        - Reports which host succeeded for debugging
        
        Args:
            host: Target host
            port: Target port
            attempts: Number of retry attempts per host
            base_delay: Base delay for exponential backoff (seconds)
            timeout: Socket connection timeout (seconds)
            
        Returns:
            (success: bool, connected_host: str or None)
        """
        # Build candidate list for loopback addresses
        candidates = [host]
        if host in ("127.0.0.1", "localhost", "::1"):
            candidates = ["127.0.0.1", "localhost", "::1"]
        
        for candidate_host in candidates:
            for attempt in range(attempts):
                try:
                    with socket.create_connection((candidate_host, port), timeout=timeout):
                        # Success - report which host worked
                        if candidate_host != host:
                            log(f"TCP probe: {host}:{port} reachable via {candidate_host}", "TROUBLE")
                        return True, candidate_host
                except OSError as e:
                    # Specific error handling
                    if attempt < attempts - 1:  # Not last attempt
                        # Exponential backoff with jitter
                        delay = base_delay * (2 ** attempt) + random.random() * 0.1
                        time.sleep(delay)
                    else:
                        # Log specific connection errors
                        if isinstance(e, ConnectionResetError):
                            log(f"TCP probe failed: Connection reset (possible firewall/AV) - {candidate_host}:{port}", "TROUBLE")
                        elif isinstance(e, ConnectionRefusedError):
                            log(f"TCP probe failed: Connection refused - {candidate_host}:{port}", "TROUBLE")
                except Exception as e:
                    # Unexpected errors
                    log(f"TCP probe unexpected error: {e.__class__.__name__} - {candidate_host}:{port}", "TROUBLE")
        
        return False, None
    
    def _tcp_handshake_check(self, host: str, port: int, expected_service: str = "clo",
                            timeout: float = 1.0) -> Tuple[bool, str]:
        """
        Verify service identity with handshake (optional enhanced check).
        
        Args:
            host: Target host
            port: Target port
            expected_service: Expected service identifier
            timeout: Socket timeout
            
        Returns:
            (verified: bool, message: str)
        """
        try:
            import json
            with socket.create_connection((host, port), timeout=timeout) as sock:
                sock.settimeout(timeout)
                # Send ping
                ping = json.dumps({"ping": expected_service}) + "\n"
                sock.sendall(ping.encode('utf-8'))
                
                # Read response
                response = sock.recv(1024).decode('utf-8').strip()
                data = json.loads(response)
                
                if data.get("pong") == expected_service:
                    return True, f"Verified {expected_service} service"
                else:
                    return False, f"Wrong service on port (expected {expected_service}, got {data})"
        except json.JSONDecodeError:
            return False, "Wrong service on port (invalid protocol)"
        except socket.timeout:
            return False, "Service timeout (possible incompatible protocol)"
        except Exception as e:
            return False, f"Handshake failed: {e.__class__.__name__}"
    
    def _check_clo_bridge(self) -> Tuple[str, Optional[str]]:
        """
        Check CLO Bridge listener reachability with smart fallbacks
        Returns: (status, recommendation)
        """
        reachable, connected_host = self._tcp_reachable(CLO_HOST, CLO_PORT)
        
        if reachable:
            # Optional: Verify it's actually CLO service (not just open port)
            verified, msg = self._tcp_handshake_check(connected_host or CLO_HOST, CLO_PORT, "clo")
            if verified:
                log(f"CLO Bridge verified at {connected_host or CLO_HOST}:{CLO_PORT}", "TROUBLE")
                new_state = "reachable"
                # Telemetry breadcrumb: state change
                if self._last_clo_state and self._last_clo_state != new_state:
                    log(f"[EVENT] clo_state_change: {self._last_clo_state}→{new_state}", "TROUBLE")
                self._last_clo_state = new_state
                return "reachable", None
            else:
                log(f"CLO Bridge port open but service unverified: {msg}", "TROUBLE")
                new_state = "uncertain"
                # Telemetry breadcrumb
                if self._last_clo_state and self._last_clo_state != new_state:
                    log(f"[EVENT] clo_state_change: {self._last_clo_state}→{new_state} ({msg})", "TROUBLE")
                self._last_clo_state = new_state
                recommendation = (
                    f"Port {CLO_PORT} is open but may not be CLO Bridge ({msg}). "
                    f"Restart CLO listener: modules\\clo_companion\\clo_bridge_listener.py"
                )
                return "uncertain", recommendation
        else:
            log(f"CLO Bridge not reachable at {CLO_HOST}:{CLO_PORT}", "TROUBLE")
            new_state = "not_reachable"
            # Telemetry breadcrumb
            if self._last_clo_state and self._last_clo_state != new_state:
                log(f"[EVENT] clo_state_change: {self._last_clo_state}→{new_state}", "TROUBLE")
            self._last_clo_state = new_state
            recommendation = (
                f"Start CLO listener: In CLO → Script → Run Script… "
                f"select modules\\clo_companion\\clo_bridge_listener.py"
            )
            return "not_reachable", recommendation
    
    def _check_system_resources(self) -> List[str]:
        """
        Check system resources (disk, RAM, Python version)
        Returns: List of hints/warnings
        """
        hints = []
        
        # Disk space check
        try:
            vector_dir = os.path.join(BASE_DIR, "vector_store")
            if os.path.exists(vector_dir):
                free_gb = shutil.disk_usage(vector_dir).free / (1024**3)
                if free_gb < 2:
                    hints.append(f"⚠️ Low disk space at vector_store: {free_gb:.1f} GB free (recommend 2+ GB)")
        except Exception:
            pass
        
        # RAM check (if psutil available)
        if PSUTIL_AVAILABLE:
            try:
                ram_gb = psutil.virtual_memory().available / (1024**3)
                if ram_gb < 2:
                    hints.append(f"⚠️ Low free RAM: {ram_gb:.1f} GB (recommend 2+ GB for indexing)")
            except Exception:
                pass
        
        # Python version check
        py_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        if py_version not in ("3.11", "3.12"):
            if py_version in ("3.10", "3.14"):
                hints.append(f"⚠️ Python {py_version} detected — recommended 3.11/3.12 for best stability")
            elif py_version < "3.10":
                hints.append(f"⚠️ Python {py_version} is too old — upgrade to 3.11+ required")
        
        return hints




