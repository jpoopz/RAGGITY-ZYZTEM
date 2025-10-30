"""
Troubleshooter Core - Main scheduler loop; subscribes to event bus and monitors Logs/
"""

import os
import sys
import threading
import time
from datetime import datetime
from typing import List, Dict

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
    from core.event_bus import get_event_bus, publish_event
except ImportError:
    def log(msg, category="TROUBLE"):
        print(f"[{category}] {msg}")
    def publish_event(event_type, sender, data=None):
        pass

from modules.smart_troubleshooter.diagnostics_analyzer import DiagnosticsAnalyzer
from modules.smart_troubleshooter.fix_recommender import FixRecommender
from modules.smart_troubleshooter.auto_fixer import AutoFixer
from modules.smart_troubleshooter.prompt_generator import PromptGenerator

class TroubleshooterCore:
    """Main troubleshooter scheduler and coordinator"""
    
    def __init__(self):
        self.analyzer = DiagnosticsAnalyzer()
        self.recommender = FixRecommender()
        self.fixer = AutoFixer()
        self.generator = PromptGenerator()
        
        self.running = False
        self.monitor_thread = None
        self.check_interval = 60  # Check every 60 seconds
        self.issues_history = []
        
        self.log_file = os.path.join(BASE_DIR, "Logs", "troubleshooter.log")
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
        # Subscribe to event bus
        try:
            event_bus = get_event_bus()
            event_bus.subscribe("error.detected", self._on_error_event)
            # Subscribe to LLM fallback events
            event_bus.subscribe("llm_fallback_active", self._handle_llm_fallback)
            log("Subscribed to LLM fallback events", "TROUBLE")
        except:
            pass
        
        log("TroubleshooterCore initialized", "TROUBLE")
        
        # Check LLM status on startup
        self._check_llm_status()
    
    def start_monitoring(self):
        """Start background monitoring thread"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        log("Troubleshooter monitoring started", "TROUBLE")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        log("Troubleshooter monitoring stopped", "TROUBLE")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Analyze recent logs
                issues = self.analyzer.analyze_logs(hours=1)  # Last hour
                
                if issues:
                    # Filter new issues
                    new_issues = [
                        i for i in issues
                        if i not in self.issues_history
                    ]
                    
                    if new_issues:
                        self._handle_issues(new_issues)
                        self.issues_history.extend(new_issues)
                
                # Sleep before next check
                time.sleep(self.check_interval)
            
            except Exception as e:
                log(f"Error in monitor loop: {e}", "TROUBLE", level="ERROR")
                time.sleep(self.check_interval)
    
    def _handle_issues(self, issues: List[Dict]):
        """Handle detected issues"""
        for issue in issues:
            try:
                self._log_issue(issue)
                
                # Recommend fix
                fix = self.recommender.recommend_fix(issue)
                
                # Auto-fix if safe
                if fix.get("safe", False) and fix.get("fix_type") in ["pip_install", "clear_cache"]:
                    success, message = self.fixer.apply_fix(issue, fix)
                    if success:
                        log(f"Auto-fixed issue: {issue.get('type')} - {message}", "TROUBLE")
                        publish_event("trouble.fixed", "troubleshooter", {
                            "issue": issue,
                            "fix": fix,
                            "message": message
                        })
                    else:
                        log(f"Auto-fix failed: {message}", "TROUBLE", level="WARNING")
                else:
                    # Publish alert
                    publish_event("trouble.alert", "troubleshooter", {
                        "issue": issue,
                        "fix": fix
                    })
            
            except Exception as e:
                log(f"Error handling issue: {e}", "TROUBLE", level="ERROR")
    
    def _on_error_event(self, event):
        """Handle error event from event bus"""
        try:
            error_data = event.get("data", {})
            # Trigger immediate analysis
            issues = self.analyzer.analyze_logs(hours=1)
            if issues:
                self._handle_issues(issues[:5])  # Handle top 5
        except:
            pass
    
    def _handle_llm_fallback(self, event):
        """Handle LLM fallback events"""
        try:
            data = event.get("data", {})
            is_active = data.get("active", False)
            
            if is_active:
                log("LLM fallback detected - monitoring local recovery", "TROUBLE")
                self.publish_issue({
                    "type": "LLMFallback",
                    "message": "LLM router fallback to cloud active",
                    "severity": "WARNING",
                    "category": "performance"
                })
            else:
                log("LLM fallback resolved - local Ollama restored", "TROUBLE")
                self.publish_fix({
                    "type": "LLMFallback",
                    "message": "Local LLM service restored",
                    "severity": "INFO"
                })
        except Exception as e:
            log(f"Error handling LLM fallback event: {e}", "TROUBLE", level="WARNING")
    
    def _check_llm_status(self):
        """Check current LLM status"""
        try:
            from core.llm_router import get_llm_router
            router = get_llm_router()
            status = router.get_status()
            
            if status["status"] == "offline":
                self.publish_issue({
                    "type": "LLMOffline",
                    "message": "No LLM service available",
                    "severity": "ERROR",
                    "category": "service_unavailable"
                })
            elif status["fallback_active"]:
                self.publish_issue({
                    "type": "LLMFallback",
                    "message": "LLM router using cloud fallback",
                    "severity": "WARNING",
                    "category": "performance"
                })
        except:
            pass
    
    def publish_issue(self, issue: Dict):
        """Publish issue to event bus"""
        try:
            publish_event("trouble.alert", "troubleshooter", {"issue": issue})
        except:
            pass
    
    def publish_fix(self, fix: Dict):
        """Publish fix notification"""
        try:
            publish_event("trouble.fixed", "troubleshooter", {"fix": fix})
        except:
            pass
    
    def _log_issue(self, issue: Dict):
        """Log issue to troubleshooter log"""
        try:
            timestamp = datetime.now().isoformat()
            log_entry = f"[{timestamp}] [{issue.get('severity', 'UNKNOWN')}] {issue.get('type', 'Unknown')} - {issue.get('message', '')[:100]}\n"
            
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except:
            pass
    
    def run_manual_scan(self) -> Dict:
        """Run a manual diagnostic scan"""
        try:
            issues = self.analyzer.analyze_logs(hours=24)
            summary = self.analyzer.get_issue_summary(issues)
            
            self._log_issue({
                "type": "ManualScan",
                "severity": "INFO",
                "message": f"Manual scan completed: {summary['total']} issues found"
            })
            
            return {
                "success": True,
                "issues": issues[:50],  # Limit to 50
                "summary": summary
            }
        except Exception as e:
            log(f"Error in manual scan: {e}", "TROUBLE", level="ERROR")
            return {
                "success": False,
                "error": str(e),
                "issues": [],
                "summary": {}
            }
    
    def generate_cursor_prompt_for_issue(self, issue_id: int) -> Optional[str]:
        """Generate Cursor prompt for a specific issue"""
        if issue_id < len(self.issues_history):
            issue = self.issues_history[issue_id]
            fix = self.recommender.recommend_fix(issue)
            return self.generator.generate_cursor_prompt(issue, fix)
        return None

# Global instance
_troubleshooter_instance = None

def get_troubleshooter() -> TroubleshooterCore:
    """Get global troubleshooter instance"""
    global _troubleshooter_instance
    if _troubleshooter_instance is None:
        _troubleshooter_instance = TroubleshooterCore()
    return _troubleshooter_instance

