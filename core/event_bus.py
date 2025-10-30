"""
Inter-Module Event Bus - Simple in-process pub/sub system
Enables real-time communication between modules
"""

import threading
from collections import defaultdict
from datetime import datetime
import sys

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

try:
    from logger import log
except ImportError:
    def log(msg, category="EVENT_BUS"):
        print(f"[{category}] {msg}")

class EventBus:
    """Simple pub/sub event bus for inter-module communication"""
    
    def __init__(self, max_queue_size=100):
        self.subscribers = defaultdict(list)  # event_type -> [callbacks]
        self.event_history = []  # For debugging/logging
        self.max_history = max_queue_size
        self.lock = threading.Lock()
    
    def publish(self, event_type, sender, data=None):
        """
        Publish an event
        
        Args:
            event_type: Type of event (e.g., "document_indexed")
            sender: Module ID that published the event
            data: Optional event data dictionary
        """
        event = {
            "event_type": event_type,
            "sender": sender,
            "data": data or {},
            "timestamp": datetime.now().isoformat()
        }
        
        with self.lock:
            # Add to history
            self.event_history.append(event)
            if len(self.event_history) > self.max_history:
                self.event_history.pop(0)
            
            # Notify subscribers
            callbacks = self.subscribers.get(event_type, [])
            log(f"Event published: {event_type} by {sender} ({len(callbacks)} subscribers)", "EVENT_BUS")
        
        # Call callbacks outside lock to avoid deadlocks
        for callback in callbacks[:]:  # Copy list to avoid modification during iteration
            try:
                callback(event)
            except Exception as e:
                log(f"Error in event callback for {event_type}: {e}", "EVENT_BUS", level="ERROR")
        
            # Send to n8n for relevant events
            n8n_event_types = ["ERROR", "FIXED", "BACKUP", "RENDER_COMPLETE", "SYNC", 
                              "trouble.alert", "trouble.fixed", "TEST_SUITE_COMPLETE"]
            if event_type in n8n_event_types or any(et in event_type for et in n8n_event_types):
                self.send_to_n8n(event)
            
            # Also use dedicated n8n integration module if available
            try:
                from core.n8n_integration import get_n8n
                n8n = get_n8n()
                if n8n.config.get("enabled"):
                    n8n.send_event(event_type, sender, data)
            except:
                pass  # n8n integration not available or disabled
    
    def subscribe(self, event_type, callback):
        """
        Subscribe to an event type
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event is published
            
        Returns:
            Unsubscribe function
        """
        with self.lock:
            self.subscribers[event_type].append(callback)
        
        log(f"Subscribed to {event_type}", "EVENT_BUS")
        
        # Return unsubscribe function
        def unsubscribe():
            with self.lock:
                if callback in self.subscribers.get(event_type, []):
                    self.subscribers[event_type].remove(callback)
                    log(f"Unsubscribed from {event_type}", "EVENT_BUS")
        
        return unsubscribe
    
    def get_recent_events(self, count=50, event_type=None):
        """Get recent events (for debugging/logging)"""
        with self.lock:
            events = self.event_history[-count:]
            if event_type:
                events = [e for e in events if e['event_type'] == event_type]
            return events
    
    def send_to_n8n(self, event_data: dict):
        """
        Send event to n8n webhook
        
        Args:
            event_data: Event dictionary to send
        """
        try:
            import requests
            import json
            import os
            from pathlib import Path
            
            BASE_DIR = Path(__file__).parent.parent
            n8n_config_file = BASE_DIR / "config" / "n8n_config.json"
            
            if not n8n_config_file.exists():
                log("n8n config not found, skipping n8n integration", "EVENT_BUS", print_to_console=False)
                return
            
            with open(n8n_config_file, 'r', encoding='utf-8') as f:
                n8n_config = json.load(f)
            
            if not n8n_config.get("enable_alerts", False):
                return  # n8n alerts disabled
            
            n8n_url = n8n_config.get("url", "")
            webhook_url = f"{n8n_url}/webhook/julian-events"
            
            if not webhook_url or "http" not in webhook_url:
                return  # No valid URL configured
            
            # Send to n8n webhook
            try:
                response = requests.post(
                    webhook_url,
                    json=event_data,
                    timeout=5,
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    log(f"Event sent to n8n: {event_data.get('event_type', 'unknown')}", "EVENT_BUS", print_to_console=False)
                else:
                    log(f"n8n webhook returned {response.status_code}", "EVENT_BUS", print_to_console=False)
            
            except requests.exceptions.RequestException as e:
                # Fallback offline - just log, don't fail
                log(f"n8n webhook unreachable (offline mode): {e}", "EVENT_BUS", print_to_console=False)
        
        except Exception as e:
            # Don't fail if n8n integration has issues
            log(f"Error sending to n8n: {e}", "EVENT_BUS", print_to_console=False)
    
    def clear_history(self):
        """Clear event history"""
        with self.lock:
            self.event_history.clear()

# Global event bus instance
_event_bus_instance = None

def get_event_bus():
    """Get global event bus instance (singleton)"""
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = EventBus()
    return _event_bus_instance

def publish_event(event_type, sender, data=None):
    """Convenience function to publish an event"""
    get_event_bus().publish(event_type, sender, data)

def subscribe_to_event(event_type, callback):
    """Convenience function to subscribe to an event"""
    return get_event_bus().subscribe(event_type, callback)

