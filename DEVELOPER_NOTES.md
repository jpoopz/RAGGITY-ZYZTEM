# Developer Notes - Module Extension Guide

**Version:** 3.0.0  
**For:** Developers extending Julian Assistant Suite

---

## 🏗️ **Adding a New Module**

### Step 1: Create Module Structure

```
modules/my_new_module/
├── __init__.py
├── module_info.json
├── api.py (or other entry point)
└── README.md
```

### Step 2: Define `module_info.json`

```json
{
  "module_id": "my_new_module",
  "name": "My New Module",
  "version": "1.0.0",
  "ports": {
    "api": 5004
  },
  "gui": {
    "tab_name": "My Module",
    "priority": 7
  }
}
```

### Step 3: Register Module

On suite startup, module is auto-discovered and registered:
- Scans `modules/` directory
- Reads `module_info.json`
- Validates and allocates port
- Adds to GUI automatically

**No core code changes needed!**

---

## 💾 **Using Memory System**

### Store Facts

```python
from core.memory_manager import get_memory_manager

memory = get_memory_manager()
memory.remember("julian", "module_preference", "prefers_feature_x", category="module_config")
```

### Recall Facts

```python
preference = memory.recall("julian", "module_preference", default="default_value")
```

### Get Context Bundle

```python
facts = memory.context_bundle("julian", limit=10, category="module_config")
```

---

## 🌐 **Using Context Graph**

### Build Context

```python
from core.context_graph import get_context_graph

graph = get_context_graph(user="julian")
context = graph.build_context(query="my query", include_rag=True)

# Context includes:
# - memory facts
# - RAG documents
# - system metrics
# - voice commands
# - CLO projects
```

### Add to Your Module

In your module's API endpoint:

```python
from core.context_graph import get_context_graph

@app.route('/my_endpoint', methods=['POST'])
def my_endpoint():
    query = request.json.get('query')
    
    # Get context
    graph = get_context_graph()
    context = graph.build_context(query=query)
    
    # Use context in your logic
    user_prefs = context['memory']['preferences']
    system_status = context['system']['metrics']
    
    # Your processing...
```

---

## 📡 **Event Bus Integration**

### Publish Events

```python
from core.event_bus import publish_event

publish_event(
    "my_module.event_type",
    "my_module",
    {
        "data": "value",
        "timestamp": "2025-10-29T18:00:00"
    }
)
```

### Subscribe to Events

```python
from core.event_bus import subscribe_to_event

def on_event(event):
    print(f"Event received: {event['event_type']}")
    print(f"Data: {event['data']}")

unsubscribe = subscribe_to_event("voice.command", on_event)

# Later: unsubscribe() to stop listening
```

---

## 🎨 **GUI Integration**

### Add Tab Content

If your module needs custom GUI elements, edit `RAG_Control_Panel_v3.py`:

```python
def setup_my_module_tab(self):
    tab = self.tabs["My Module"]
    
    # Add your widgets
    my_button = ctk.CTkButton(tab, text="My Action", command=self.my_action)
    my_button.pack(padx=10, pady=10)
```

### Update Metrics Display

```python
def update_my_metrics(self, data):
    # Update your module's metrics in Dashboard
    pass
```

---

## 🔐 **Security**

### AUTH Token

All inter-module calls require AUTH token:

```python
from core.auth_helper import require_auth_token
from core.config_manager import get_auth_token

@app.route('/protected', methods=['POST'])
@require_auth_token
def protected():
    # Only accessible with valid token
    pass

# In requests:
headers = {"Authorization": f"Bearer {get_auth_token()}"}
```

### Localhost-Only

All modules bind to `127.0.0.1` by default:
- Change in `config/suite_config.json` → `security.bind_localhost_only: false`
- Or module config: `api.host: "0.0.0.0"`

---

## 📊 **Health Monitoring**

### Implement Health Endpoint

All modules must implement:

```python
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "module_id": "my_module",
        "version": "1.0.0",
        "uptime_seconds": uptime
    })
```

### Custom Health Checks

In your module's health endpoint:

```python
checks = {
    "database": check_database(),
    "external_api": check_external_api(),
    "disk_space": check_disk_space()
}

return jsonify({
    "status": "healthy" if all(checks.values()) else "degraded",
    "checks": checks
})
```

---

## 🔄 **Resource Management**

### Throttling

Use suite config for resource limits:

```python
from core.config_manager import get_suite_config

config = get_suite_config()
max_workers = config.get("resources", {}).get("max_concurrent_workers", 4)
max_ram = config.get("resources", {}).get("max_ram_mb", 4096)

# Enforce limits in your module
```

### Queue System

For rate-limited operations:

```python
from queue import Queue
import threading

task_queue = Queue(maxsize=100)

def worker():
    while True:
        task = task_queue.get()
        process_task(task)
        task_queue.task_done()

threading.Thread(target=worker, daemon=True).start()
```

---

## 📝 **Logging**

Use unified logger:

```python
from logger import log, log_exception

log("Module operation started", "MY_MODULE")
log("Warning message", "MY_MODULE", level="WARNING")
log_exception("MY_MODULE", exception, "Error context")
```

---

## 🧪 **Testing**

### Test Your Module

```python
# Standalone test
python modules/my_module/api.py

# Health check
curl http://127.0.0.1:5004/health

# Integration test
from core.module_registry import get_registry
registry = get_registry()
module = registry.get_module("my_module")
assert module is not None
```

---

## 📚 **Best Practices**

1. **Keep It Lightweight:** Minimize dependencies, use lazy loading
2. **Use Config Files:** Store settings in `config/{module}_config.json`
3. **Event-Driven:** Publish events for important actions
4. **Graceful Degradation:** Handle missing dependencies gracefully
5. **Documentation:** Include `README.md` in module folder

---

## 🔗 **Module Communication**

### Direct HTTP

```python
import requests
from core.module_registry import get_registry

registry = get_registry()
other_module = registry.get_module("other_module")
port = other_module.get('port')

response = requests.post(
    f"http://127.0.0.1:{port}/endpoint",
    json={"data": "value"},
    headers={"Authorization": f"Bearer {get_auth_token()}"}
)
```

### Event Bus

```python
# Publish
publish_event("my_module.done", "my_module", {"result": "success"})

# Subscribe (in other module)
subscribe_to_event("my_module.done", callback_function)
```

### Shared Memory

```python
from core.memory_manager import get_memory_manager

memory = get_memory_manager()
memory.remember("julian", "shared_state", {"key": "value"})
# Other modules can recall this
```

---

**Happy Developing!** 🚀




