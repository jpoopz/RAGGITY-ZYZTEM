# Julian Assistant Suite v2.0 - Architecture Summary

**Quick Reference Guide** | **Status:** Design Complete, Awaiting Implementation Approval

---

## 🎯 **System Overview**

Transform existing RAG system into **modular multi-tool control hub**:
- **5 Modules:** Academic RAG, CLO Companion, Web Retriever, Automation Hub, System Monitor
- **Independent Flask Servers:** Each module on separate port (5000-5999)
- **Unified Control:** Single GUI manages all modules
- **Zero Breaking Changes:** Existing Academic RAG continues working

---

## 📁 **Key Directory Structure**

```
RAG_System/
├── core/                    # Shared infrastructure (unchanged on module add)
│   ├── logger.py
│   ├── config_manager.py
│   ├── module_registry.py
│   ├── health_monitor.py
│   └── inter_module_bus.py
│
├── modules/                 # All modules (auto-discovered)
│   ├── academic_rag/        # Existing (refactored)
│   ├── clo_companion/       # NEW
│   ├── web_retriever/       # NEW
│   ├── automation_hub/      # NEW
│   └── system_monitor/      # NEW
│
├── config/                  # JSON configs
│   ├── suite_config.json    # Main config
│   └── [module]_config.json # Per-module
│
└── RAG_Control_Panel.py     # Main GUI (refactored)
```

---

## 🔌 **Module Registration (Auto-Discovery)**

**How It Works:**
1. Suite scans `modules/` folder on startup
2. Reads `module_info.json` from each module
3. Validates module (files, ports, dependencies)
4. Registers in `config/modules.json`
5. Adds to GUI automatically

**No core code changes needed** to add new modules!

---

## 🌐 **Port Management**

| Module | Default Port | Port Range |
|--------|-------------|------------|
| Academic RAG | 5000 | 5000-5999 |
| CLO Companion | 5001 | (auto-assigned if conflict) |
| Web Retriever | 5002 | |
| Automation Hub | 5003 | |
| System Monitor | No port (always active) | |

**Conflict Resolution:**
- Check registry → Test port → Auto-reassign if needed → Notify user

---

## 🖥️ **GUI Layout (Recommended: Tabs)**

```
┌────────────────────────────────────────────────────┐
│  Julian Assistant Suite v2.0          [Model Info] │
├────────────────────────────────────────────────────┤
│ [Academic] [CLO] [Web] [Auto] [System]             │
├────────────────────────────────────────────────────┤
│                                                    │
│  [SELECTED MODULE CONTROL PANEL]                   │
│  • Module Status                                   │
│  • Module Actions                                 │
│  • Module Logs                                    │
│                                                    │
├────────────────────────────────────────────────────┤
│  Suite-Wide Status │ Module-Specific Logs          │
└────────────────────────────────────────────────────┘
```

---

## 📡 **Inter-Module Communication**

**3 Methods:**

1. **Event Bus (Pub/Sub)**
   - Real-time events
   - Module publishes → Others subscribe
   - Example: RAG → CLO Companion design queries

2. **HTTP Calls**
   - Direct module-to-module requests
   - Example: Web Retriever → Academic RAG (save results)

3. **Shared Data Store**
   - JSON files in `shared/data/`
   - Example: Design context for RAG/CLO sharing

---

## 🚀 **Startup Flow**

```
Desktop Shortcut
  ↓
RAG_Control_Panel.py
  ↓
Core Infrastructure Init
  ├─ Logger
  ├─ Config Manager
  ├─ Module Registry (scans modules/)
  ├─ Health Monitor
  └─ Version Manager
  ↓
GUI Init (Tab/Sidebar)
  ↓
Auto-Start Modules (per config)
  ├─ Check enabled
  ├─ Allocate port
  ├─ Launch Flask server
  └─ Verify health
  ↓
System Monitor Starts
  ↓
✅ Suite Ready
```

---

## ⚙️ **Configuration System**

**Hierarchy:**
1. `suite_config.json` - Main suite settings
   - User profile, auto-start, logging
   - Module enable/disable
   - Port allocations

2. `config/modules.json` - Auto-generated registry
   - Discovered modules
   - Port assignments
   - Process IDs

3. `config/{module}_config.json` - Per-module settings
   - Module-specific configuration

---

## 🔍 **Health Monitoring**

**Centralized Health Monitor:**
- Checks all modules every 30 seconds
- Verifies: Process alive, Port responding, Dependencies available
- Updates GUI status indicators
- Alerts on failures

**Each Module Must:**
- Implement `GET /health` endpoint
- Return status JSON

---

## 🔄 **Version Management**

**Multi-Module Version Sync:**
- Suite version: `suite_config.json`
- Module versions: `module_info.json`
- Compatibility matrix checks
- Update notifications per module

---

## ➕ **Adding New Modules**

**4 Steps (Zero Core Changes):**

1. **Create folder:** `modules/my_module/`
2. **Write `module_info.json`** (required fields)
3. **Restart suite** (auto-discovery)
4. **Configure & enable** in `suite_config.json`

**That's it!** Module appears in GUI automatically.

---

## 📊 **Module Lifecycle**

```
START:
  ├─ Check dependencies
  ├─ Allocate port
  ├─ Spawn Flask process
  ├─ Wait for health check
  └─ Update status (green)

STOP:
  ├─ Find process ID
  ├─ Graceful shutdown
  ├─ Free port
  └─ Update status (gray)

MONITOR:
  ├─ Process alive?
  ├─ Port responding?
  ├─ Dependencies OK?
  └─ Update status indicator
```

---

## 🔗 **Example: RAG ↔ CLO Communication**

**Scenario:** User asks RAG "How to make this sustainable?"

1. RAG processes query, retrieves context
2. RAG publishes event: `design_query_received`
3. CLO Companion receives event
4. CLO generates design suggestions, applies to CLO3D
5. CLO publishes: `design_modification_applied`
6. RAG includes CLO actions in response

**User sees:** Complete answer with academic context + design actions

---

## 📋 **Design Validation Checklist**

- ✅ Modular (add/remove modules independently)
- ✅ Port conflict resolution
- ✅ Configuration management
- ✅ GUI layout planned
- ✅ Shared infrastructure
- ✅ Inter-module communication
- ✅ Lightweight & extensible
- ✅ Startup flow defined
- ✅ Update checking system
- ✅ Filesystem structure defined
- ✅ Migration path from v1.2.0

---

## 📚 **Documentation Files**

1. **JULIAN_ASSISTANT_SUITE_ARCHITECTURE.md** (Main design document)
2. **ARCHITECTURE_DIAGRAM.txt** (ASCII diagrams)
3. **MODULE_IMPLEMENTATION_GUIDE.md** (Module dev guide)
4. **ARCHITECTURE_SUMMARY.md** (This file - quick reference)

---

## 🎯 **Implementation Phases**

**Phase 1: Core Infrastructure** (Week 1)
- `config_manager.py`, `module_registry.py`
- Refactor Academic RAG to module structure
- Basic multi-module GUI

**Phase 2: Module Development** (Week 2)
- CLO Companion MVP
- Web Retriever MVP
- Inter-module bus

**Phase 3: Integration** (Week 3)
- System Monitor
- Automation Hub
- Full health monitoring

**Phase 4: Polish** (Week 4)
- Dashboard view
- Performance optimization
- Documentation

---

## ✅ **Ready for Review**

**Architecture Status:** ✅ **Complete**

All design decisions documented. Ready for implementation approval.

**Next Step:** Review architecture documents → Approve → Begin Phase 1 implementation

---

**Architecture Version:** 2.0  
**Design Date:** 2025-10-29  
**Status:** ✅ Awaiting Approval




