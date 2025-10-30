# Julian Assistant Suite - System Architecture v2.0

**Status:** Architecture Design Phase  
**Date:** 2025-10-29  
**Target:** Modular multi-tool local AI control hub

---

## 🎯 **System Overview**

The **Julian Assistant Suite** evolves from a single-purpose RAG system into a modular control hub that manages multiple local AI modules, each serving a distinct purpose (academic research, design assistance, web retrieval, automation, system monitoring).

### **Core Principles**
1. **Modularity:** Each module is self-contained with clear interfaces
2. **Independence:** Modules can run standalone or integrated
3. **Shared Infrastructure:** Common logger, health monitor, config system
4. **Lightweight:** Minimal overhead, easy to extend
5. **Portability:** Easy to add/remove modules without core changes

---

## 🏗️ **System Architecture**

### **High-Level Diagram**

```
┌─────────────────────────────────────────────────────────────────┐
│              JULIAN ASSISTANT SUITE CONTROL PANEL              │
│                     (RAG_Control_Panel.py v2.0)                 │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Academic │  │ CLO      │  │ Web      │  │ Auto     │      │
│  │ RAG      │  │ Companion│  │ Retriever│  │ Hub      │      │
│  │ Module   │  │ Module   │  │ Module   │  │ Module   │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         System Monitor Module (Always Active)             │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │        Shared Infrastructure Layer                      │  │
│  │  • Unified Logger    • Config Manager                    │  │
│  │  • Health Monitor    • Version Manager                  │  │
│  │  • Module Registry   • Inter-Module Communication       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Manages
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MODULE INSTANCES                              │
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐│
│  │ Flask Server    │  │ Flask Server   │  │ Flask Server    ││
│  │ :5000           │  │ :5001           │  │ :5002           ││
│  │ (Academic RAG)  │  │ (CLO Companion)│  │ (Web Retriever) ││
│  └─────────────────┘  └─────────────────┘  └─────────────────┘│
│                                                                 │
│  ┌─────────────────┐  ┌─────────────────┐                      │
│  │ Background      │  │ System Monitor  │                      │
│  │ Process         │  │ (Ollama/Flask) │                      │
│  │ (Automation)    │  │ (Resource CPU/GPU)                     ││
│  └─────────────────┘  └─────────────────┘                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 **File & Folder Structure**

```
RAG_System/
│
├── core/                          # Core infrastructure (unchanged on module add)
│   ├── __init__.py
│   ├── logger.py                  # Unified logging (already exists)
│   ├── config_manager.py          # NEW: JSON config handler
│   ├── module_registry.py         # NEW: Module discovery & registration
│   ├── health_monitor.py          # NEW: Centralized health checking
│   ├── version_manager.py         # NEW: Version sync across modules
│   ├── inter_module_bus.py        # NEW: Message bus for module communication
│   └── utils.py                   # NEW: Shared utilities
│
├── modules/                        # All modules live here
│   │
│   ├── academic_rag/              # Module 1 (existing, refactored)
│   │   ├── __init__.py
│   │   ├── module_info.json       # Module metadata (name, version, port, etc.)
│   │   ├── api.py                 # Flask server (rag_api.py moved here)
│   │   ├── query_llm.py           # Existing
│   │   ├── index_documents.py     # Existing
│   │   ├── semantic_tagging.py   # Existing
│   │   └── knowledge_profiles.py  # NEW: Course/profile switching
│   │
│   ├── clo_companion/             # Module 2 (NEW)
│   │   ├── __init__.py
│   │   ├── module_info.json
│   │   ├── api.py                 # Flask server on :5001
│   │   ├── clo_interface.py      # CLO3D integration
│   │   ├── design_prompt_handler.py
│   │   └── design_history.py     # Undo/redo tracking
│   │
│   ├── web_retriever/             # Module 3 (NEW)
│   │   ├── __init__.py
│   │   ├── module_info.json
│   │   ├── api.py                 # Flask server on :5002
│   │   ├── web_crawler.py
│   │   ├── summarizer.py
│   │   └── obsidian_writer.py     # Writes to Obsidian vault
│   │
│   ├── automation_hub/            # Module 4 (NEW)
│   │   ├── __init__.py
│   │   ├── module_info.json
│   │   ├── n8n_connector.py       # n8n workflow triggers
│   │   ├── supabase_connector.py  # Database sync
│   │   ├── vps_connector.py       # Hostinger VPS tasks
│   │   └── task_scheduler.py      # Nightly jobs
│   │
│   └── system_monitor/            # Module 5 (Always active)
│       ├── __init__.py
│       ├── module_info.json
│       ├── process_monitor.py     # Ollama, Flask processes
│       ├── resource_monitor.py    # CPU, GPU, RAM
│       └── quick_launch.py        # One-click module starts
│
├── config/                        # User preferences & module configs
│   ├── suite_config.json          # Main suite configuration
│   ├── modules.json               # Module registry (auto-generated)
│   ├── academic_rag_config.json   # Per-module configs
│   ├── clo_companion_config.json
│   ├── web_retriever_config.json
│   └── automation_hub_config.json
│
├── shared/                        # Shared resources
│   ├── templates/                 # Common templates/UI elements
│   ├── assets/                    # Icons, images
│   └── schemas/                   # JSON schemas for validation
│
├── logs/                          # Unified logs (existing structure)
│   ├── suite.log                  # Main suite operations
│   ├── academic_rag.log           # Module-specific logs
│   ├── clo_companion.log
│   └── ...
│
├── RAG_Control_Panel.py           # Main GUI (refactored for multi-module)
├── module_loader.py               # NEW: Dynamic module loader
├── diagnostics.py                 # Enhanced for multi-module
├── backup_restore.py             # Works for entire suite
├── update_checker.py             # Checks all modules
│
└── requirements.txt               # Updated with new dependencies

```

---

## 🔌 **Module Registration System**

### **Module Discovery Pattern**

When the suite starts:
1. **Scan `modules/` directory** for folders
2. **Read `module_info.json`** from each module folder
3. **Validate module** (check required files, port availability)
4. **Register module** in `config/modules.json`
5. **Load module** into GUI tabs/sidebar

### **module_info.json Schema**

```json
{
  "module_id": "academic_rag",
  "name": "Academic RAG Assistant",
  "version": "1.2.0",
  "description": "Local NotebookLM for Obsidian academic notes",
  "author": "Julian Poopat",
  "status": "active",  // active | disabled | deprecated
  
  "ports": {
    "api": 5000,
    "websocket": null  // optional
  },
  
  "dependencies": {
    "python_packages": ["chromadb", "flask", "ollama"],
    "external": ["ollama", "llama3.2"],
    "other_modules": []  // e.g., ["web_retriever"] if needs it
  },
  
  "entry_points": {
    "api": "modules/academic_rag/api.py",
    "cli": null  // optional command-line entry
  },
  
  "gui": {
    "tab_name": "Academic",
    "icon": "book",
    "priority": 1,  // Display order (1 = first)
    "widget_class": "AcademicModuleWidget"  // Optional custom UI
  },
  
  "permissions": {
    "file_system_access": ["obsidian_vault_path"],
    "network_access": false,
    "require_api_keys": []
  },
  
  "features": [
    "document_indexing",
    "rag_queries",
    "citation_generation",
    "knowledge_profiles"
  ]
}
```

### **config/modules.json** (Auto-generated Registry)

```json
{
  "version": "2.0.0",
  "registered_modules": [
    {
      "module_id": "academic_rag",
      "path": "modules/academic_rag",
      "status": "active",
      "last_health_check": "2025-10-29T18:00:00",
      "port": 5000,
      "process_id": 12345
    },
    {
      "module_id": "clo_companion",
      "path": "modules/clo_companion",
      "status": "disabled",
      "last_health_check": null,
      "port": 5001,
      "process_id": null
    }
    // ... other modules
  ],
  "port_allocations": {
    "5000": "academic_rag",
    "5001": "clo_companion",
    "5002": "web_retriever",
    "5003": "automation_hub"
  }
}
```

---

## 🖥️ **GUI Layout Redesign**

### **Main Window Structure**

```
┌──────────────────────────────────────────────────────────────────┐
│  Julian Assistant Suite v2.0              [Model: Llama 3.2]     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │Academic │ │  CLO    │ │   Web   │ │  Auto   │ │ System  │   │
│  │  RAG    │ │Companion│ │Retriever│ │   Hub   │ │ Monitor │   │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘   │
│    [Tab 1]     [Tab 2]     [Tab 3]     [Tab 4]     [Tab 5]      │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  [SELECTED MODULE CONTROL PANEL]                           │ │
│  │                                                             │ │
│  │  • Status Indicators (Module-specific)                      │ │
│  │  • Action Buttons (Index, Start API, etc.)                  │ │
│  │  • Module-specific Settings                                 │ │
│  │                                                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────────────────┐ ┌──────────────────────────────┐ │
│  │  Suite-Wide Status        │ │  Module-Specific Logs        │ │
│  │                           │ │                              │ │
│  │  • All Modules Health     │ │  [Live log output from        │ │
│  │  • Quick Actions          │ │   selected module]           │ │
│  │  • Resource Usage         │ │                              │ │
│  └──────────────────────────┘ └──────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  Status Messages Console (Last 5 Suite-wide updates)        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [Ready] [Full Suite Test] [Backup Suite] [Quit]                │
└──────────────────────────────────────────────────────────────────┘
```

### **Navigation Options**

**Option A: Tab-Based (Recommended for 5 modules)**
- Tabs at top for module switching
- Active module panel below
- Suite-wide status sidebar (right)

**Option B: Sidebar Navigation**
- Left sidebar with module icons
- Main panel shows selected module
- Suite status bar at bottom

**Option C: Dashboard + Modules**
- Default dashboard view (all modules overview)
- Click module → dedicated module view
- "Back to Dashboard" button

---

## 🔄 **Module Lifecycle Management**

### **Startup Sequence (Desktop Shortcut → Full Suite)**

```
1. Desktop Shortcut Double-Click
   ↓
2. Launch RAG_Control_Panel.py (Main Entry Point)
   ↓
3. Initialize Core Infrastructure
   ├─ logger.py → Setup unified logging
   ├─ config_manager.py → Load suite_config.json
   ├─ module_registry.py → Scan modules/ folder
   │  └─ Discover all module_info.json files
   │  └─ Validate modules
   │  └─ Generate config/modules.json
   ├─ health_monitor.py → Start background health checker
   └─ version_manager.py → Check all module versions
   ↓
4. Initialize GUI
   ├─ Create main window
   ├─ Load tabs/sidebar from module registry
   ├─ Display suite-wide status indicators
   └─ Show "Dashboard" or first active module
   ↓
5. Auto-Start Modules (Per User Preference)
   ├─ Read suite_config.json → "auto_start_modules"
   ├─ For each module in auto_start list:
   │  ├─ Check if module is enabled
   │  ├─ Verify port availability
   │  ├─ Launch module's Flask server (background process)
   │  ├─ Wait for health check
   │  └─ Update status indicator
   └─ Log startup summary
   ↓
6. System Monitor Starts (Always Active)
   ├─ Begin monitoring Ollama
   ├─ Track all Flask server processes
   ├─ Monitor CPU/GPU usage
   └─ Display in System Monitor tab
   ↓
7. Ready State
   └─ GUI shows "✅ Suite Ready"
```

### **Module Start/Stop Flow**

```
START MODULE:
├─ User clicks "Start [Module Name]" button
├─ module_registry.py:
│  ├─ Check port availability
│  ├─ Validate dependencies (other modules, packages)
│  └─ Spawn subprocess: python modules/{module_id}/api.py
├─ health_monitor.py:
│  ├─ Wait 2-3 seconds
│  ├─ Ping module's /health endpoint
│  └─ Retry up to 3 times
├─ Update GUI status indicator (green/yellow/red)
└─ Log to logs/{module_id}.log

STOP MODULE:
├─ User clicks "Stop [Module Name]" button
├─ module_registry.py:
│  ├─ Find process ID from config/modules.json
│  ├─ Terminate process gracefully
│  └─ Update registry (remove process_id)
├─ Free port allocation
└─ Update GUI status
```

---

## 🌐 **Port Management & Conflict Resolution**

### **Port Allocation Strategy**

```python
# Pseudocode for port management
PortAllocator:
  - Reserved ports: 5000-5999 (custom range)
  - Port registry: config/modules.json → "port_allocations"
  
  - CheckPort(port):
    ├─ Check if port in registry
    ├─ Check if port actually listening (socket test)
    └─ Return: available | in_use | reserved
    
  - AllocatePort(module_id):
    ├─ Read module_info.json → "ports.api"
    ├─ If port specified:
    │  └─ CheckPort(port) → if available, assign
    ├─ Else:
    │  └─ Find first free port in range 5000-5999
    └─ Update config/modules.json
```

### **Port Conflict Resolution**

**Strategy 1: Fail-Safe (Recommended)**
- If port is in use, show warning dialog:
  - "Port 5000 is in use by [Process Name]. Stop it?"
  - Option: Stop conflicting process
  - Option: Assign different port
  - Option: Cancel module start

**Strategy 2: Auto-Reassign**
- If module's preferred port is taken, automatically assign next available port
- Log port change
- Update module_info.json temporarily

**Strategy 3: Port Reservation**
- On startup, check all configured ports
- Reserve ports in registry even if module not running
- Prevent other applications from using reserved ports

---

## ⚙️ **Configuration Management**

### **suite_config.json** (Main Configuration)

```json
{
  "suite_version": "2.0.0",
  "user_profile": {
    "name": "Julian Poopat",
    "obsidian_vault_path": "C:\\Users\\Julian Poopat\\Documents\\Obsidian",
    "preferred_llm": "llama3.2",
    "ollama_host": "http://localhost:11434"
  },
  
  "startup": {
    "auto_start_modules": ["academic_rag", "system_monitor"],
    "show_dashboard_on_start": true,
    "minimize_to_tray": false
  },
  
  "logging": {
    "level": "INFO",
    "rotation_size_mb": 5,
    "retention_days": 30,
    "module_specific_logs": true
  },
  
  "monitoring": {
    "health_check_interval_seconds": 30,
    "resource_check_interval_seconds": 10,
    "alert_on_module_crash": true
  },
  
  "modules": {
    "academic_rag": {
      "enabled": true,
      "auto_start": true,
      "config_file": "config/academic_rag_config.json"
    },
    "clo_companion": {
      "enabled": false,
      "auto_start": false,
      "config_file": "config/clo_companion_config.json"
    },
    "web_retriever": {
      "enabled": true,
      "auto_start": false,
      "config_file": "config/web_retriever_config.json"
    },
    "automation_hub": {
      "enabled": true,
      "auto_start": false,
      "config_file": "config/automation_hub_config.json"
    },
    "system_monitor": {
      "enabled": true,
      "auto_start": true,
      "config_file": null
    }
  },
  
  "inter_module": {
    "enable_bus": true,
    "message_queue_size": 100,
    "event_logging": true
  },
  
  "updates": {
    "check_on_startup": true,
    "check_interval_hours": 24,
    "update_source": "local_git"  // local_git | github | manual
  }
}
```

### **Per-Module Config Example** (academic_rag_config.json)

```json
{
  "module_id": "academic_rag",
  "version": "1.2.0",
  
  "knowledge_profiles": [
    {
      "name": "Management Class",
      "vault_path": "C:\\Users\\Julian Poopat\\Documents\\Obsidian",
      "active": true
    },
    {
      "name": "Design Studies",
      "vault_path": "C:\\Users\\Julian Poopat\\Documents\\Design_Notes",
      "active": false
    }
  ],
  
  "indexing": {
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "auto_reindex_on_vault_change": false
  },
  
  "api": {
    "host": "127.0.0.1",
    "port": 5000,
    "cors_enabled": true
  },
  
  "rag": {
    "model": "llama3.2",
    "reasoning_modes": ["Analytical", "Concise", "Creative Academic"],
    "citation_format": "inline",
    "similarity_threshold": 0.6
  }
}
```

---

## 📡 **Inter-Module Communication**

### **Message Bus Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│              Inter-Module Bus (Event-Driven)                │
│                                                             │
│  Module A publishes event ──┐                             │
│  Module B subscribes ───────┼─► Event Handler ──► Action  │
│  Module C subscribes ───────┘                              │
└─────────────────────────────────────────────────────────────┘
```

### **Communication Patterns**

**Pattern 1: Event-Based (Pub/Sub)**
```python
# Module publishes event
inter_module_bus.publish(
    event="document_indexed",
    sender="academic_rag",
    data={"document_count": 150, "vault": "Management Class"}
)

# Other modules subscribe
web_retriever.subscribe("document_indexed", callback_function)
automation_hub.subscribe("document_indexed", backup_trigger)
```

**Pattern 2: Direct HTTP Calls (Module-to-Module)**
```python
# Academic RAG needs web search
response = requests.post(
    "http://127.0.0.1:5002/web_retriever/api/search",
    json={"query": "latest research on blue economy"}
)

# Web Retriever returns formatted markdown
# Academic RAG incorporates into response
```

**Pattern 3: Shared Data Store**
```python
# Modules write to shared JSON/database
shared_store.set("current_design_context", {
    "clo_file": "dress_v2.clo",
    "modifications": ["changed sleeve length", "added pleats"],
    "timestamp": "2025-10-29T18:00:00"
})

# Other modules read
design_context = shared_store.get("current_design_context")
```

### **Example: RAG → CLO Companion Communication**

```
Scenario: User asks Academic RAG "How should I modify this dress for sustainability?"

1. Academic RAG processes query
   ↓
2. RAG identifies this relates to design
   ↓
3. RAG publishes event:
   {
     "event": "design_query_received",
     "query": "How should I modify this dress for sustainability?",
     "context": "Retrieved from notes: sustainable fashion guidelines",
     "sender": "academic_rag"
   }
   ↓
4. CLO Companion subscribes and receives event
   ↓
5. CLO Companion:
   ├─ Opens CLO3D file (if not open)
   ├─ Generates design suggestions using Llama 3.2
   ├─ Creates CLO3D commands to apply changes
   └─ Publishes "design_modification_applied" event
   ↓
6. Academic RAG receives confirmation
   ↓
7. RAG includes CLO Companion's actions in response to user
```

### **Event Types**

```python
# Common events across modules
EVENT_TYPES = {
    "document_indexed": "Academic RAG finished indexing",
    "design_query_received": "CLO Companion received design query",
    "web_search_completed": "Web Retriever finished search",
    "task_completed": "Automation Hub finished task",
    "module_started": "Any module started",
    "module_stopped": "Any module stopped",
    "knowledge_profile_switched": "Academic RAG switched profiles",
    "system_health_changed": "System Monitor detected issue"
}
```

---

## 🔍 **Health Monitoring System**

### **Centralized Health Monitor**

```python
HealthMonitor:
  - Check all registered modules every 30 seconds
  - For each module:
    ├─ Process alive? (check PID)
    ├─ Port responding? (HTTP GET /health)
    ├─ Module-specific checks (read from module_info.json)
    └─ Dependency checks (Ollama, ChromaDB, etc.)
  
  - Status Levels:
    ✅ Healthy: All checks pass
    ⚠️ Warning: Minor issue (e.g., high resource usage)
    ❌ Unhealthy: Critical failure (process dead, port closed)
    ⬜ Disabled: Module not enabled
  
  - Alert System:
    - Log to logs/suite.log
    - Update GUI status indicators
    - Optional: Show notification popup
    - Optional: Trigger automation (restart module)
```

### **Module Health Check Endpoint**

All modules must implement:
```
GET /health
Response:
{
  "status": "healthy" | "degraded" | "unhealthy",
  "module_id": "academic_rag",
  "version": "1.2.0",
  "uptime_seconds": 3600,
  "checks": {
    "process": true,
    "port": true,
    "dependencies": {
      "ollama": true,
      "chromadb": true
    }
  },
  "resources": {
    "cpu_percent": 15.2,
    "memory_mb": 256
  }
}
```

---

## 🔄 **Version Management**

### **Multi-Module Version Sync**

```python
VersionManager:
  - Read suite version from suite_config.json
  - Read each module version from module_info.json
  - Check for updates:
    ├─ Local git repository (if available)
    ├─ GitHub releases (if configured)
    └─ Module-specific update sources
  
  - Version Compatibility Matrix:
    {
      "suite_version": "2.0.0",
      "modules": {
        "academic_rag": "1.2.0",  # Compatible
        "clo_companion": "1.0.0",  # Compatible
        "web_retriever": "1.0.0"   # Compatible
      },
      "min_versions": {
        "academic_rag": "1.2.0",
        "system_monitor": "1.0.0"
      }
    }
  
  - Update Notification:
    - Show in GUI: "Module X has update available"
    - Click → Download/install update
    - Verify compatibility before applying
```

### **Module Version Requirements**

Each `module_info.json` can specify:
```json
{
  "version": "1.0.0",
  "requires": {
    "suite_min_version": "2.0.0",
    "python_min_version": "3.8",
    "dependencies": {
      "academic_rag": ">=1.1.0"  // If needs RAG module
    }
  }
}
```

---

## 🚀 **Adding New Modules (Extensibility)**

### **Module Addition Workflow**

**Step 1: Create Module Folder**
```
modules/my_new_module/
├── __init__.py
├── module_info.json  # REQUIRED
└── api.py (or other entry point)
```

**Step 2: Write module_info.json**
- Fill in all required fields
- Specify port or leave null for auto-assignment
- Define dependencies

**Step 3: Restart Suite**
- Suite automatically discovers new module
- Validates module_info.json
- Registers in config/modules.json
- Adds tab/sidebar entry in GUI

**Step 4: Configure Module**
- User enables module in suite_config.json
- Sets module-specific config in config/my_new_module_config.json
- Optionally sets auto-start

**NO CODE CHANGES TO CORE NEEDED**

### **Module Interface Contract**

All modules must implement:

1. **module_info.json** (required fields)
2. **GET /health endpoint** (for health monitoring)
3. **Shutdown handler** (graceful termination)
4. **Config loader** (reads from config/{module}_config.json)

Optional:
- Custom GUI widget (for advanced UI)
- Inter-module communication handlers
- Scheduled tasks

---

## 🗄️ **Data Storage & Persistence**

### **Shared Data Store** (for inter-module communication)

```
shared/
└── data/
    ├── design_context.json       # CLO Companion ↔ Academic RAG
    ├── web_insights_cache.json   # Web Retriever ↔ Academic RAG
    ├── automation_state.json     # Automation Hub state
    └── suite_state.json          # Overall suite state
```

### **Module Data Isolation**

Each module stores its own data:
```
modules/academic_rag/
└── data/
    ├── .chromadb/              # Vector database
    └── knowledge_profiles.json

modules/clo_companion/
└── data/
    ├── design_history.json
    └── clo_templates/
```

---

## 🔒 **Security & Permissions**

### **Permission Model**

Each module's `module_info.json` declares permissions:
```json
{
  "permissions": {
    "file_system_access": [
      "read:obsidian_vault_path",
      "write:obsidian_vault_path/Web_Imports"
    ],
    "network_access": true,
    "require_api_keys": ["openai_api_key"],  // If needs external APIs
    "process_spawning": true  // If needs to launch other apps
  }
}
```

**User grants permissions** on first module start:
- "Module X requests file access to Y. Allow?"
- Saved in suite_config.json → permissions section

---

## 📊 **GUI Implementation Details**

### **Tab/Sidebar Widget Structure**

```python
# Each module tab contains:
class ModuleTab:
  - ModuleHeader (name, version, status indicator)
  - ModuleControls (Start/Stop, Settings, Test)
  - ModuleStatus (module-specific indicators)
  - ModuleLogs (scrollable log window)
  - ModuleActions (module-specific buttons)
```

### **Suite-Wide Dashboard**

When no specific module selected:
- Overview of all modules (status grid)
- Quick actions (start all, stop all, health check)
- Resource usage (CPU, GPU, RAM, Ollama)
- Recent suite events
- System Monitor integration

---

## 🔌 **External Integrations**

### **CLO3D Integration**

```
CLO Companion Module:
├─ Connects to CLO3D via:
│  ├─ CLO API (if available)
│  ├─ File watching (monitors .clo file changes)
│  └─ Command injection (via CLO scripts)
├─ Receives design queries from Llama 3.2
├─ Translates to CLO3D commands
└─ Publishes design events for other modules
```

### **n8n / Automation Hub**

```
Automation Hub Module:
├─ HTTP webhook endpoints:
│  ├─ /trigger/index_documents → Calls Academic RAG
│  ├─ /trigger/backup_suite → Backup workflow
│  └─ /trigger/nightly_tasks → Scheduled jobs
├─ Receives events from other modules
├─ Triggers external workflows (n8n, VPS scripts)
└─ Logs automation actions
```

---

## 🧪 **Testing Strategy**

### **Module Testing**

Each module should include:
```
modules/academic_rag/
└── tests/
    ├── test_api.py
    ├── test_indexing.py
    └── test_integration.py
```

### **Suite Integration Testing**

```
tests/
├── test_module_discovery.py  # Can suite find new modules?
├── test_port_allocation.py   # Port conflict handling
├── test_inter_module_bus.py  # Event communication
└── test_health_monitor.py    # Health checking
```

---

## 📈 **Performance Considerations**

### **Resource Management**

- **Lazy Loading:** Modules only load when activated
- **Process Pooling:** Reuse Flask processes when possible
- **Log Rotation:** Per-module log files with size limits
- **Config Caching:** Cache configs to avoid repeated JSON reads

### **Startup Optimization**

- **Parallel Module Start:** Start multiple modules simultaneously
- **Health Check Batching:** Batch health checks to avoid spam
- **Delayed Heavy Operations:** Defer expensive operations (indexing) until needed

---

## 🎯 **Migration Path from v1.2.0**

### **Phase 1: Core Infrastructure** (No Breaking Changes)
1. Add `core/` directory structure
2. Create `config_manager.py`, `module_registry.py`
3. Refactor existing code into `modules/academic_rag/`
4. Maintain backward compatibility (old entry points still work)

### **Phase 2: Multi-Module GUI**
1. Refactor `RAG_Control_Panel.py` to tab-based layout
2. Implement module loading system
3. Add dashboard view

### **Phase 3: New Modules**
1. Implement CLO Companion (basic)
2. Implement Web Retriever (basic)
3. Add inter-module communication

### **Phase 4: Polish & Optimize**
1. Add System Monitor
2. Add Automation Hub
3. Full integration testing
4. Documentation updates

---

## 🔮 **Future Enhancements**

### **Potential Additions**

1. **Module Marketplace:** Download/install community modules
2. **Plugin System:** Third-party plugins for existing modules
3. **Cloud Sync:** Optional encrypted sync across devices
4. **Web Dashboard:** Browser-based control panel (alternative to GUI)
5. **API Gateway:** Single entry point that routes to modules
6. **Module Templates:** Scaffold generator for new modules

---

## ✅ **Architecture Validation Checklist**

- [x] Modular design (modules can be added/removed independently)
- [x] Port conflict resolution strategy
- [x] Configuration management system
- [x] GUI layout plan (tabs/sidebar)
- [x] Shared infrastructure (logger, health, versioning)
- [x] Inter-module communication mechanism
- [x] Lightweight and extensible
- [x] Startup flow defined
- [x] Update checking system
- [x] Filesystem structure for modules
- [x] Migration path from v1.2.0

---

## 📝 **Implementation Priority**

**Phase 1: Foundation** (Week 1)
- Core infrastructure (config_manager, module_registry)
- Refactor Academic RAG into module structure
- Basic multi-module GUI (tabs)

**Phase 2: Module Development** (Week 2)
- CLO Companion (MVP)
- Web Retriever (MVP)
- Inter-module bus (basic)

**Phase 3: Integration** (Week 3)
- System Monitor
- Automation Hub (basic)
- Full health monitoring

**Phase 4: Polish** (Week 4)
- Dashboard view
- Performance optimization
- Documentation

---

**Architecture Status:** ✅ **Complete - Ready for Review**

*This architecture provides a clear blueprint for implementing Julian Assistant Suite v2.0 while maintaining backward compatibility and extensibility.*




