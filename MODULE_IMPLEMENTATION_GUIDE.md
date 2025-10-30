# Module Implementation Guide - Julian Assistant Suite

**Purpose:** Guide for implementing individual modules within the suite

---

## 📋 **Module Requirements Checklist**

Every module **MUST** implement:

### ✅ **Required Files**

1. **`module_info.json`** - Module metadata (see schema below)
2. **`__init__.py`** - Python package marker
3. **Health endpoint** - `GET /health` in API server
4. **Config loader** - Reads from `config/{module_id}_config.json`

### ✅ **Required Behaviors**

1. **Graceful shutdown** - Handles SIGTERM/SIGINT
2. **Port binding** - Uses port from `module_info.json` or registry
3. **Config validation** - Validates config on startup
4. **Error logging** - Uses unified logger with `[MODULE_ID]` category
5. **Health reporting** - Responds to `/health` with status

---

## 📐 **module_info.json Schema**

```json
{
  "module_id": "unique_module_identifier",
  "name": "Display Name",
  "version": "1.0.0",
  "description": "What this module does",
  "author": "Julian Poopat",
  "status": "active",
  
  "ports": {
    "api": 5000,
    "websocket": null
  },
  
  "dependencies": {
    "python_packages": ["flask", "requests"],
    "external": ["ollama"],
    "other_modules": []
  },
  
  "entry_points": {
    "api": "modules/{module_id}/api.py",
    "cli": null
  },
  
  "gui": {
    "tab_name": "Short Name",
    "icon": "icon_name",
    "priority": 1,
    "widget_class": null
  },
  
  "permissions": {
    "file_system_access": [],
    "network_access": false,
    "require_api_keys": []
  },
  
  "features": []
}
```

---

## 🏗️ **Module Structure Template**

```
modules/my_module/
├── __init__.py
├── module_info.json
├── api.py              # Flask server entry point
├── config_loader.py    # Reads module config
├── health.py           # Health check implementation
├── utils.py            # Module-specific utilities
└── README.md           # Module documentation
```

---

## 💻 **Module API Template**

```python
# modules/my_module/api.py
from flask import Flask, jsonify, request
from core.logger import log
from core.config_manager import get_module_config
import sys

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

app = Flask(__name__)
config = get_module_config("my_module")

@app.route('/health', methods=['GET'])
def health():
    """Required health endpoint"""
    return jsonify({
        "status": "healthy",
        "module_id": "my_module",
        "version": "1.0.0",
        "uptime_seconds": get_uptime(),
        "checks": {
            "process": True,
            "port": True,
            "dependencies": check_dependencies()
        }
    })

@app.route('/api/my_endpoint', methods=['POST'])
def my_endpoint():
    """Module-specific endpoints"""
    log("Processing request", "MY_MODULE")
    # Implementation
    return jsonify({"result": "success"})

if __name__ == '__main__':
    port = config.get('api', {}).get('port', 5000)
    log(f"Starting {config['module_id']} on port {port}", "MY_MODULE")
    app.run(host='127.0.0.1', port=port, debug=False)
```

---

## 🔗 **Inter-Module Communication Examples**

### **Publishing Events**

```python
from core.inter_module_bus import publish_event

# Module publishes event
publish_event(
    event_type="my_event",
    sender="my_module",
    data={"key": "value"}
)
```

### **Subscribing to Events**

```python
from core.inter_module_bus import subscribe_to_event

def on_document_indexed(event_data):
    # Handle event
    log(f"Received event: {event_data}", "MY_MODULE")

# Subscribe
subscribe_to_event("document_indexed", on_document_indexed)
```

### **Direct HTTP Calls**

```python
import requests
from core.config_manager import get_module_port

# Call another module
port = get_module_port("academic_rag")
response = requests.post(
    f"http://127.0.0.1:{port}/api/endpoint",
    json={"data": "value"}
)
```

---

## 📝 **Module Config Template**

```json
{
  "module_id": "my_module",
  "version": "1.0.0",
  
  "api": {
    "host": "127.0.0.1",
    "port": 5000,
    "cors_enabled": true
  },
  
  "settings": {
    "my_setting": "value",
    "another_setting": 123
  }
}
```

---

## ✅ **Testing Your Module**

1. **Standalone Test:** Run module API directly
2. **Health Check:** `curl http://127.0.0.1:PORT/health`
3. **Integration Test:** Start from suite, verify appears in GUI
4. **Inter-Module Test:** Publish/subscribe to events

---

**Status:** Ready for module development




