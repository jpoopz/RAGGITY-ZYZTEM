"""
Fix Recommender - Uses regex and embedding similarity to suggest fixes
"""

import os
import sys
import re
from typing import Dict, List, Optional

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
except ImportError:
    def log(msg, category="TROUBLE"):
        print(f"[{category}] {msg}")

class FixRecommender:
    """Recommends fixes for detected issues"""
    
    def __init__(self):
        self.rules_file = os.path.join(os.path.dirname(__file__), "troubleshooter_rules.json")
        self.rules = self._load_rules()
        
        log("FixRecommender initialized", "TROUBLE")
    
    def _load_rules(self) -> Dict:
        """Load troubleshooting rules"""
        try:
            import json
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            log(f"Error loading rules: {e}", "TROUBLE", level="ERROR")
            return {}
    
    def recommend_fix(self, issue: Dict) -> Dict:
        """
        Recommend fix for an issue
        
        Returns:
            Dict with fix_type, description, command, confidence
        """
        issue_type = issue.get("type", "")
        category = issue.get("category", "")
        auto_fix_type = issue.get("auto_fix_type")
        
        # Check rules first
        if auto_fix_type:
            return self._get_rule_fix(issue, auto_fix_type)
        
        # Generic recommendations by category
        if category == "missing_dependency":
            return {
                "fix_type": "pip_install",
                "description": "Install missing dependency",
                "command": None,  # Will be generated
                "confidence": 0.8,
                "safe": True
            }
        
        elif category == "service_down":
            return {
                "fix_type": "restart_service",
                "description": "Restart service",
                "command": None,
                "confidence": 0.7,
                "safe": True
            }
        
        elif category == "database_error":
            return {
                "fix_type": "clear_cache",
                "description": "Clear database cache",
                "command": None,
                "confidence": 0.6,
                "safe": False  # Requires backup
            }
        
        elif category == "missing_file":
            return {
                "fix_type": "create_file",
                "description": "Create missing file",
                "command": None,
                "confidence": 0.5,
                "safe": True
            }
        
        elif category == "permission_error":
            return {
                "fix_type": "fix_permissions",
                "description": "Fix file permissions",
                "command": None,
                "confidence": 0.7,
                "safe": False
            }
        
        else:
            return {
                "fix_type": "manual_review",
                "description": "Requires manual review",
                "command": None,
                "confidence": 0.3,
                "safe": False
            }
    
    def _get_rule_fix(self, issue: Dict, fix_type: str) -> Dict:
        """Get fix from rule"""
        fix_command = issue.get("fix_command")
        matched_groups = issue.get("matched_groups", [])
        
        if fix_command and matched_groups:
            # Replace placeholders
            command = fix_command
            for i, group in enumerate(matched_groups):
                command = command.replace(f"{{module}}", group).replace(f"{{group_{i}}}", group)
            return {
                "fix_type": fix_type,
                "description": f"Auto-fix: {fix_type}",
                "command": command,
                "confidence": 0.9,
                "safe": True
            }
        
        return {
            "fix_type": fix_type,
            "description": f"Auto-fix: {fix_type}",
            "command": None,
            "confidence": 0.7,
            "safe": True
        }




