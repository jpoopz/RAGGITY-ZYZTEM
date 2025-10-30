"""
Smart Troubleshooter - Main Entry Point
Analyzes logs, detects issues, and provides automated fix recommendations
"""

import os
import sys
import re
from typing import Dict, List, Any
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from logger import get_logger

log = get_logger("troubleshooter")


class LogAnalyzer:
    """Analyzes log files for errors, stack traces, and issues"""
    
    def __init__(self, logs_dir: str = None):
        self.logs_dir = logs_dir or os.path.join(BASE_DIR, "Logs")
        
    def analyze_logs(self, hours: int = 24) -> Dict[str, Any]:
        """
        Analyze log files for the past N hours
        
        Returns:
            Dictionary with errors, warnings, stack traces, and patterns
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        errors = []
        warnings = []
        stack_traces = []
        missing_deps = []
        missing_files = []
        
        if not os.path.exists(self.logs_dir):
            log.warning(f"Logs directory not found: {self.logs_dir}")
            return self._empty_result()
        
        log.info(f"Analyzing logs from {self.logs_dir} (last {hours}h)")
        
        # Scan all .log files
        for log_file in Path(self.logs_dir).glob("*.log"):
            try:
                # Check file modification time
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_mtime < cutoff_time:
                    continue
                
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                log.info(f"Analyzing {log_file.name} ({len(content)} chars)")
                
                # Extract errors
                errors.extend(self._extract_errors(content, str(log_file)))
                
                # Extract warnings
                warnings.extend(self._extract_warnings(content, str(log_file)))
                
                # Extract stack traces
                stack_traces.extend(self._extract_stack_traces(content, str(log_file)))
                
                # Detect missing dependencies
                missing_deps.extend(self._detect_missing_deps(content, str(log_file)))
                
                # Detect missing files/folders
                missing_files.extend(self._detect_missing_files(content, str(log_file)))
                
            except Exception as e:
                log.error(f"Error analyzing {log_file}: {e}")
        
        # Aggregate and deduplicate
        result = {
            "errors": self._deduplicate(errors),
            "warnings": self._deduplicate(warnings),
            "stack_traces": self._deduplicate(stack_traces),
            "missing_dependencies": self._deduplicate(missing_deps),
            "missing_files": self._deduplicate(missing_files),
            "analyzed_files": len(list(Path(self.logs_dir).glob("*.log"))),
            "timestamp": datetime.now().isoformat()
        }
        
        log.info(f"Analysis complete: {len(result['errors'])} errors, {len(result['warnings'])} warnings")
        
        return result
    
    def _extract_errors(self, content: str, source: str) -> List[Dict]:
        """Extract ERROR level messages"""
        errors = []
        
        # Match [ERROR] or ERROR: patterns
        error_pattern = r'\[([^\]]*)\]\s*\[ERROR\]\s*(.+)|ERROR:\s*(.+)'
        
        for match in re.finditer(error_pattern, content, re.MULTILINE):
            timestamp = match.group(1) if match.group(1) else ""
            message = match.group(2) or match.group(3) or ""
            
            errors.append({
                "type": "error",
                "message": message.strip()[:200],  # Truncate long messages
                "source": os.path.basename(source),
                "timestamp": timestamp
            })
        
        return errors
    
    def _extract_warnings(self, content: str, source: str) -> List[Dict]:
        """Extract WARNING level messages"""
        warnings = []
        
        warning_pattern = r'\[([^\]]*)\]\s*\[WARNING\]\s*(.+)|WARNING:\s*(.+)|WARN:\s*(.+)'
        
        for match in re.finditer(warning_pattern, content, re.MULTILINE):
            timestamp = match.group(1) if match.group(1) else ""
            message = match.group(2) or match.group(3) or match.group(4) or ""
            
            warnings.append({
                "type": "warning",
                "message": message.strip()[:200],
                "source": os.path.basename(source),
                "timestamp": timestamp
            })
        
        return warnings
    
    def _extract_stack_traces(self, content: str, source: str) -> List[Dict]:
        """Extract Python stack traces"""
        stack_traces = []
        
        # Find "Traceback (most recent call last):" followed by lines
        traceback_pattern = r'Traceback \(most recent call last\):((?:\n  .*)+)'
        
        for match in re.finditer(traceback_pattern, content):
            full_trace = match.group(0)
            
            # Extract exception type and message
            exception_match = re.search(r'(\w+Error|Exception):\s*(.+)$', full_trace, re.MULTILINE)
            
            if exception_match:
                exc_type = exception_match.group(1)
                exc_msg = exception_match.group(2).strip()
                
                stack_traces.append({
                    "type": "stack_trace",
                    "exception_type": exc_type,
                    "message": exc_msg[:200],
                    "full_trace": full_trace[:500],  # Truncate
                    "source": os.path.basename(source)
                })
        
        return stack_traces
    
    def _detect_missing_deps(self, content: str, source: str) -> List[Dict]:
        """Detect missing Python dependencies"""
        missing = []
        
        # Common patterns for missing imports
        patterns = [
            r"ModuleNotFoundError: No module named '(\w+)'",
            r"ImportError: cannot import name '(\w+)'",
            r"ImportError: No module named (\w+)",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                module_name = match.group(1)
                
                missing.append({
                    "type": "missing_dependency",
                    "module": module_name,
                    "source": os.path.basename(source),
                    "fix": f"pip install {module_name}"
                })
        
        return missing
    
    def _detect_missing_files(self, content: str, source: str) -> List[Dict]:
        """Detect missing files or directories"""
        missing = []
        
        patterns = [
            r"FileNotFoundError:.*'([^']+)'",
            r"No such file or directory:\s*'?([^'\n]+)'?",
            r"\[Errno 2\].*'([^']+)'",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                path = match.group(1).strip()
                
                missing.append({
                    "type": "missing_file",
                    "path": path,
                    "source": os.path.basename(source),
                    "fix": f"Create file/directory: {path}"
                })
        
        return missing
    
    def _deduplicate(self, items: List[Dict]) -> List[Dict]:
        """Remove duplicate items based on message/module/path"""
        seen = set()
        unique = []
        
        for item in items:
            # Create key based on item type
            if item["type"] == "missing_dependency":
                key = item.get("module", "")
            elif item["type"] == "missing_file":
                key = item.get("path", "")
            else:
                key = item.get("message", "")[:100]
            
            if key and key not in seen:
                seen.add(key)
                unique.append(item)
        
        return unique
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty analysis result"""
        return {
            "errors": [],
            "warnings": [],
            "stack_traces": [],
            "missing_dependencies": [],
            "missing_files": [],
            "analyzed_files": 0,
            "timestamp": datetime.now().isoformat()
        }


class IssueRecommender:
    """Generates recommendations for detected issues"""
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate fix recommendations based on analysis
        
        Returns:
            List of recommendations with type, description, and action
        """
        recommendations = []
        
        # Missing dependencies
        for dep in analysis.get("missing_dependencies", []):
            recommendations.append({
                "type": "install_dependency",
                "priority": "high",
                "description": f"Install missing Python package: {dep['module']}",
                "action": f"pip install {dep['module']}",
                "automated": True
            })
        
        # Missing files/directories
        for file_info in analysis.get("missing_files", []):
            path = file_info["path"]
            
            # Determine if it's likely a directory or file
            is_dir = "/" in path or "\\" in path
            
            if is_dir:
                recommendations.append({
                    "type": "create_directory",
                    "priority": "medium",
                    "description": f"Create missing directory: {path}",
                    "action": f"mkdir -p {path}",
                    "automated": True
                })
            else:
                recommendations.append({
                    "type": "create_file",
                    "priority": "medium",
                    "description": f"Create missing file: {path}",
                    "action": f"touch {path}",
                    "automated": False
                })
        
        # Frequent exceptions - recommend try/except
        exception_counts = Counter()
        for trace in analysis.get("stack_traces", []):
            exc_type = trace.get("exception_type", "")
            if exc_type:
                exception_counts[exc_type] += 1
        
        for exc_type, count in exception_counts.most_common(3):
            if count >= 2:  # Appears multiple times
                recommendations.append({
                    "type": "add_error_handling",
                    "priority": "medium",
                    "description": f"Add error handling for frequent {exc_type} ({count} occurrences)",
                    "action": f"Wrap code in try/except for {exc_type}",
                    "automated": False
                })
        
        # Check for common error patterns
        error_messages = [e.get("message", "") for e in analysis.get("errors", [])]
        
        # Connection errors
        if any("connection" in msg.lower() or "timeout" in msg.lower() for msg in error_messages):
            recommendations.append({
                "type": "connection_issue",
                "priority": "high",
                "description": "Connection errors detected - check network/service availability",
                "action": "Verify Ollama/services are running and accessible",
                "automated": False
            })
        
        # Permission errors
        if any("permission denied" in msg.lower() for msg in error_messages):
            recommendations.append({
                "type": "permission_issue",
                "priority": "high",
                "description": "Permission denied errors detected",
                "action": "Check file/directory permissions",
                "automated": False
            })
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: priority_order.get(x["priority"], 3))
        
        return recommendations


def troubleshoot(hours: int = 24) -> Dict[str, Any]:
    """
    Main troubleshooting function - analyzes logs and generates recommendations
    
    Args:
        hours: Number of hours to look back in logs (default: 24)
    
    Returns:
        Dictionary with:
            - issues: List of detected issues
            - recommendations: List of fix recommendations
            - summary: Summary statistics
            - timestamp: When analysis was performed
    """
    log.info(f"Starting troubleshoot analysis (last {hours}h)")
    
    # Analyze logs
    analyzer = LogAnalyzer()
    analysis = analyzer.analyze_logs(hours=hours)
    
    # Generate recommendations
    recommender = IssueRecommender()
    recommendations = recommender.generate_recommendations(analysis)
    
    # Combine all issues
    issues = []
    issues.extend(analysis.get("errors", []))
    issues.extend(analysis.get("warnings", []))
    issues.extend(analysis.get("stack_traces", []))
    issues.extend(analysis.get("missing_dependencies", []))
    issues.extend(analysis.get("missing_files", []))
    
    # Create summary
    summary = {
        "total_issues": len(issues),
        "errors": len(analysis.get("errors", [])),
        "warnings": len(analysis.get("warnings", [])),
        "stack_traces": len(analysis.get("stack_traces", [])),
        "missing_dependencies": len(analysis.get("missing_dependencies", [])),
        "missing_files": len(analysis.get("missing_files", [])),
        "recommendations": len(recommendations),
        "analyzed_files": analysis.get("analyzed_files", 0)
    }
    
    log.info(f"Troubleshoot complete: {summary['total_issues']} issues, {len(recommendations)} recommendations")
    
    return {
        "issues": issues,
        "recommendations": recommendations,
        "summary": summary,
        "timestamp": datetime.now().isoformat(),
        "analysis_window_hours": hours
    }

