"""
Diagnostics Analyzer - Parses logs for errors, tracebacks, and warnings
Maps issues to categories and severity levels
"""

import os
import sys
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
except ImportError:
    def log(msg, category="TROUBLE"):
        print(f"[{category}] {msg}")

class DiagnosticsAnalyzer:
    """Analyzes log files for errors, warnings, and issues"""
    
    def __init__(self):
        self.logs_dir = os.path.join(BASE_DIR, "Logs")
        self.rules_file = os.path.join(os.path.dirname(__file__), "troubleshooter_rules.json")
        self.rules = self._load_rules()
        
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
        """Get summary statistics of issues"""
        if not issues:
            return {
                "total": 0,
                "errors": 0,
                "warnings": 0,
                "auto_fixable": 0,
                "severity_score": 0
            }
        
        errors = sum(1 for i in issues if i.get("severity") == "ERROR")
        warnings = sum(1 for i in issues if i.get("severity") == "WARNING")
        auto_fixable = sum(1 for i in issues if i.get("auto_fixable", False))
        avg_severity = sum(i.get("severity_score", 0) for i in issues) / len(issues)
        
        return {
            "total": len(issues),
            "errors": errors,
            "warnings": warnings,
            "auto_fixable": auto_fixable,
            "avg_severity": avg_severity,
            "severity_score": avg_severity
        }




