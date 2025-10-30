# Julian Assistant Suite - Complete File Structure Map

**Version:** v4.1.0-Julian-PolishFinal  
**Date:** 2025-10-29  
**Base Path:** `C:\Users\Julian Poopat\Documents\Management Class\RAG_System`

---

## 📋 **TABLE OF CONTENTS**

1. [CORE SYSTEM](#core-system)
2. [MAIN LAUNCHER](#main-launcher)
3. [MODULES](#modules)
4. [REMOTE/VPS COMPONENTS](#remotevps-components)
5. [CONFIGURATION](#configuration)
6. [DATA STORAGE](#data-storage)
7. [LOG FILES](#log-files)
8. [DOCUMENTATION](#documentation)
9. [SCRIPTS & UTILITIES](#scripts--utilities)
10. [DEPENDENCIES & RUNTIME](#dependencies--runtime)

---

## 🎯 **CORE SYSTEM**

### Core Library (`/core/`)

| Path | Purpose | User-Facing | Notes |
|------|---------|-------------|-------|
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\core\__init__.py` | Package marker for core module | ❌ Backend | Python package initialization |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\core\auth_helper.py` | Authentication decorator for API endpoints | ❌ Backend | Requires AUTH_TOKEN in headers |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\core\cloud_bridge.py` | Cloud Bridge client for VPS sync | ❌ Backend | Handles encrypted sync, auto-reconnect |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\core\config_encrypt.py` | Encrypts sensitive config values at rest | ❌ Backend | Fernet-based encryption |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\core\config_manager.py` | Centralized config management | ❌ Backend | Suite-wide and module configs |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\core\context_graph.py` | Builds unified context from all modules | ❌ Backend | Merges memory, RAG, voice, CLO context |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\core\event_bus.py` | In-process pub/sub event system | ❌ Backend | Inter-module communication |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\core\health_monitor.py` | Monitors module health and system status | ❌ Backend | Pings `/health` endpoints |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\core\memory_manager.py` | Persistent SQLite memory management | ❌ Backend | Facts, sessions, context cache |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\core\module_registry.py` | Auto-discovers and registers modules | ❌ Backend | Port allocation, module lifecycle |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\core\schema.sql` | SQLite database schema | ❌ Backend | Tables for memory, logs, sessions |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\core\sync_manager.py` | Backup and restore operations | ❌ Backend | VPS sync, backup compression |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\core\version_manager.py` | Version tracking and update checking | ❌ Backend | Module version coordination |

---

## 🚀 **MAIN LAUNCHER**

### Primary Entry Point

| Path | Purpose | User-Facing | GUI Component |
|------|---------|-------------|---------------|
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\RAG_Control_Panel.py` | Main GUI launcher and control panel | ✅ Primary | Entire application window |

**Features:**
- Status indicators (Python, Ollama, ChromaDB, API, Cloud Bridge)
- Action buttons (Index, Start/Stop API, Test Query, Health Check, etc.)
- Live log viewer
- Graceful shutdown routine
- Auto-start API server (5s delay)
- First-launch walkthrough

---

## 📦 **MODULES**

### Module Base Path
`C:\Users\Julian Poopat\Documents\Management Class\RAG_System\modules\`

---

### 1️⃣ **Academic RAG Assistant** (`/modules/academic_rag/`)

**Port:** `5000` (default)  
**Auto-Start:** ✅ Yes (via GUI auto-start)  
**Status:** ✅ Active  
**GUI Tab:** Academic (Priority 1)

| Path | Purpose | User-Facing |
|------|---------|-------------|
| `modules/academic_rag/__init__.py` | Package marker | ❌ Backend |
| `modules/academic_rag/api.py` | Flask API server (Academic RAG) | ❌ Backend |
| `modules/academic_rag/index_documents.py` | Indexes Obsidian vault to ChromaDB | ✅ Via GUI button |
| `modules/academic_rag/query_llm.py` | RAG query processing with Llama 3.2 | ❌ Backend |
| `modules/academic_rag/knowledge_profiles.py` | Profile management (MN3102, SD4117, etc.) | ✅ Via API/config |
| `modules/academic_rag/module_info.json` | Module metadata and configuration | ❌ Backend |
| `modules/academic_rag/semantic_tagging.py` | Auto-tagging documents with topics | ❌ Backend |

**Endpoints:**
- `POST /v1/chat/completions` - OpenAI-compatible chat
- `POST /query` - Direct query with citations
- `GET /health` - Health check
- `POST /reindex` - Trigger reindexing
- `POST /summarize` - Summarize file/text
- `POST /plan_essay` - Generate essay plan
- `GET /context/preview` - View current context graph

---

### 2️⃣ **CLO Companion** (`/modules/clo_companion/`)

**Port:** `5001` (default)  
**Auto-Start:** ❌ No (starts on-demand)  
**Status:** ✅ Active  
**GUI Tab:** 👗 CLO Companion (Priority 2)

| Path | Purpose | User-Facing |
|------|---------|-------------|
| `modules/clo_companion/__init__.py` | Package marker | ❌ Backend |
| `modules/clo_companion/clo_api.py` | FastAPI server (CLO Companion) | ❌ Backend |
| `modules/clo_companion/api.py` | Legacy Flask API (deprecated) | ❌ Backend |
| `modules/clo_companion/garment_gen.py` | Procedural garment generation | ❌ Backend |
| `modules/clo_companion/module_info.json` | Module metadata | ❌ Backend |
| `modules/clo_companion/CLO_COMPANION_SPEC.md` | Specification document | ✅ Documentation |
| `modules/clo_companion/CLO_COMPANION_USER_GUIDE.md` | User guide | ✅ Documentation |
| `modules/clo_companion/outputs/` | Generated garment files | ✅ User accessible |
| `modules/clo_companion/outputs/previews/` | Preview images | ✅ User accessible |

**Endpoints:**
- `POST /generate_garment` - Generate garment from text prompt
- `GET /list_outputs` - List all generated garments
- `GET /preview/{id}` - Get preview image
- `GET /metadata/{id}` - Get generation metadata
- `GET /download/{id}` - Download OBJ file
- `GET /health` - Health check

**Features:**
- Procedural mesh generation (8 garment types)
- Material library (8 materials)
- Attribute parsing (oversized, fitted, long, short, etc.)
- Seed-based randomization
- Preview generation (trimesh/Open3D)
- CLO3D export support

---

### 3️⃣ **Web Retriever** (`/modules/web_retriever/`)

**Port:** `5002` (default)  
**Auto-Start:** ❌ No  
**Status:** 🔧 Stub  
**GUI Tab:** Web (Priority 3)

| Path | Purpose | User-Facing |
|------|---------|-------------|
| `modules/web_retriever/__init__.py` | Package marker | ❌ Backend |
| `modules/web_retriever/api.py` | Flask API server (Web Retriever) | ❌ Backend |
| `modules/web_retriever/module_info.json` | Module metadata | ❌ Backend |

**Endpoints:**
- `POST /summarize_web` - Summarize web content
- `POST /search_web` - Search and retrieve web pages

---

### 4️⃣ **Automation Hub** (`/modules/automation_hub/`)

**Port:** `5003` (default)  
**Auto-Start:** ❌ No  
**Status:** 🔧 Stub  
**GUI Tab:** Automation (Priority 4)

| Path | Purpose | User-Facing |
|------|---------|-------------|
| `modules/automation_hub/__init__.py` | Package marker | ❌ Backend |
| `modules/automation_hub/api.py` | Flask API server (Automation Hub) | ❌ Backend |
| `modules/automation_hub/module_info.json` | Module metadata | ❌ Backend |

**Features:**
- n8n webhook integration
- Supabase sync
- VPS task offloading

---

### 5️⃣ **System Monitor** (`/modules/system_monitor/`)

**Port:** None (background process)  
**Auto-Start:** ✅ Yes (if enabled)  
**Status:** ✅ Active  
**GUI Tab:** System (Priority 5)

| Path | Purpose | User-Facing |
|------|---------|-------------|
| `modules/system_monitor/__init__.py` | Package marker | ❌ Backend |
| `modules/system_monitor/monitor.py` | Process and resource monitoring | ❌ Backend |
| `modules/system_monitor/module_info.json` | Module metadata | ❌ Backend |

**Features:**
- CPU/RAM/GPU monitoring (via `psutil`)
- Ollama process tracking
- Module port status
- Resource usage alerts

---

### 6️⃣ **Voice Control** (`/modules/voice_control/`)

**Port:** None (local listener)  
**Auto-Start:** ❌ No  
**Status:** ✅ Active  
**GUI Tab:** Voice (Priority 6)

| Path | Purpose | User-Facing |
|------|---------|-------------|
| `modules/voice_control/__init__.py` | Package marker | ❌ Backend |
| `modules/voice_control/voice_listener.py` | Voice command listener (push-to-talk F9) | ✅ Via hotkey |
| `modules/voice_control/module_info.json` | Module metadata | ❌ Backend |
| `modules/voice_control/config/commands.json` | Command mappings (if exists) | ✅ Configurable |
| `modules/voice_control/config/voice_feedback.json` | Feedback settings (if exists) | ✅ Configurable |

**Features:**
- Push-to-talk (F9 by default)
- whisper-cpp speech-to-text
- Command mapping to Suite actions
- Event bus integration

---

## ☁️ **REMOTE/VPS COMPONENTS**

### Remote Bridge (`/remote/`)

| Path | Purpose | User-Facing | Deployment |
|------|---------|-------------|------------|
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\remote\cloud_bridge_server.py` | FastAPI server for VPS | ❌ VPS-side | Copy to Hostinger VPS |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\remote\rsa_generate.py` | Generates RSA key pair | ✅ Via script | Run locally |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\remote\deploy.sh` | VPS deployment script | ✅ Via SSH | Run on VPS (Ubuntu) |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\remote\keys/private.pem` | RSA private key (KEEP SECRET) | ❌ Local only | Never upload |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\remote\keys/public.pem` | RSA public key | ❌ Copy to VPS | Upload to `~/assistant/keys/` |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\remote\keys/aes.key` | AES shared secret | ❌ Sync to VPS | Must match on both sides |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\remote\keys/config.key` | Config encryption key | ❌ Local | For encrypting `vps_config.json` |

**VPS Server Endpoints:**
- `GET /health` - Health check
- `GET /ping` - Latency test
- `POST /context/push` - Receive local context
- `GET /context/pull` - Send VPS context
- `POST /execute` - Remote task execution

---

## ⚙️ **CONFIGURATION**

### Config Directory (`/config/`)

| Path | Purpose | User-Facing | Encryption |
|------|---------|-------------|------------|
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\config\suite_config.json` | Suite-wide configuration | ✅ Editable | Sensitive values encrypted |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\config\vps_config.json` | Cloud Bridge VPS configuration | ✅ Editable | `api_token` encrypted |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\config\modules.json` | Module registry cache | ❌ Auto-generated | No |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\config\academic_rag_config.json` | Academic RAG module config | ✅ Editable | No |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\config\clo_companion_config.json` | CLO Companion module config | ✅ Editable | No |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\config\web_retriever_config.json` | Web Retriever module config | ✅ Editable | No |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\config\automation_hub_config.json` | Automation Hub module config | ✅ Editable | Tokens encrypted |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\config\user_prefs.json` | User preferences and profiles | ✅ Editable | No |

---

## 💾 **DATA STORAGE**

### Data Directory (`/data/`)

| Path | Purpose | User-Facing | Size |
|------|---------|-------------|------|
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\data\memory.db` | SQLite persistent memory | ❌ Backend | ~MB (grows with use) |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\data\chroma/` | Semantic memory (ChromaDB) | ❌ Backend | ~MB |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\data\cache.sqlite` | Retrieval cache (if exists) | ❌ Backend | Variable |

### ChromaDB Collections
- `.chromadb/` (root) - Main document embeddings
- `data/chroma/semantic_memory/` - Semantic facts collection

### Obsidian Integration
- **Vault Path:** `C:\Users\Julian Poopat\Documents\Obsidian\`
- **Output:** `Notes/AI_Conversations/` - Query responses with citations
- **Web Imports:** `Notes/Web_Imports/` - Web retrieval summaries
- **Web Insights:** `Notes/Web_Insights/` - Web Retriever output (future)

---

## 📝 **LOG FILES**

### Logs Directory (`/Logs/`)

| Path | Purpose | Rotation | Retention |
|------|---------|----------|-----------|
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\Logs\YYYY-MM-DD.log` | Daily log file | Daily | 7 days (then gzip) |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\Logs\*.log.gz` | Compressed old logs | Auto | 7 days (then delete) |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\Logs\operations.log` | Legacy operations log (if exists) | Size-based | Variable |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\Logs\launch.log` | GUI launcher log | Append | Persistent |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\Logs\api_startup_errors.log` | API startup errors | Per-session | Cleared on start |

**Log Categories:**
- `[API]` - RAG API operations
- `[INDEX]` - Document indexing
- `[GUI]` - Control Panel events
- `[LLM]` - Llama/Ollama calls
- `[CLOUD]` - Cloud Bridge sync
- `[MEMORY]` - Memory manager
- `[CONTEXT]` - Context graph
- `[EVENT_BUS]` - Inter-module events
- `[CLO]` - CLO Companion
- `[VOICE]` - Voice Control
- `[DIAG]` - Diagnostics
- `[SYNC]` - Backup/restore

---

## 📚 **DOCUMENTATION**

### Documentation Files (Root)

| Path | Purpose | Audience |
|------|---------|----------|
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\README.md` | Main project README | All users |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\CHANGELOG.md` | Version history and changes | Developers/Users |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\PHASE4_SUMMARY.md` | Phase 4 Cloud Bridge overview | Developers |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\PHASE4_POLISH_SUMMARY.md` | Phase 4.1 polish summary | Developers |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\VPS_BRIDGE_SETUP.md` | Hostinger VPS setup guide | Administrators |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\ENCRYPTION_OVERVIEW.md` | RSA/AES encryption flow | Security/Sysadmins |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\JULIAN_SUITE_FILE_STRUCTURE.md` | This document | All |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\SUITE_USER_GUIDE.md` | User manual (if exists) | End users |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\DEVELOPER_NOTES.md` | Developer documentation | Developers |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\MEMORY_ARCHITECTURE.md` | Memory system design (if exists) | Developers |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\JULIAN_ASSISTANT_SUITE_ARCHITECTURE.md` | Full architecture (if exists) | Architects/Developers |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\POST_DEPLOYMENT_SUMMARY.md` | Deployment report (if exists) | Stakeholders |

---

## 🛠️ **SCRIPTS & UTILITIES**

### Root Scripts

| Path | Purpose | User-Facing | Usage |
|------|---------|-------------|-------|
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\diagnostics.py` | Comprehensive health check | ✅ Via GUI | Click "Health Check" or run `python diagnostics.py` |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\logger.py` | Unified logging system | ❌ Backend | Imported by all modules |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\backup_restore.py` | Backup/restore utilities | ✅ Via GUI | "Backup System" / "Restore System" buttons |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\update_checker.py` | Version update checker | ❌ Backend | Called by GUI |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\semantic_tagging.py` | Document tagging utility | ❌ Backend | Called during indexing |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\query_helper.py` | Query processing helper | ❌ Backend | Utility functions |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\index_documents.py` | Legacy indexing script (if exists) | ✅ Via GUI | Wrapped by module |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\query_llm.py` | Legacy query script (if exists) | ❌ Backend | Replaced by module |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\rag_api.py` | Legacy API (if exists) | ❌ Backend | Replaced by module API |

### Utility Scripts (if exist)

| Path | Purpose | User-Facing |
|------|---------|-------------|
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\create_icon.py` | Generate application icon | ✅ One-time setup |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\fix_tkinter_complete.py` | Tkinter path fixer | ✅ Troubleshooting |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\test_api_startup.py` | API startup test | ❌ Development |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\test_tkinter.py` | Tkinter test | ❌ Development |

---

## 🔧 **LOCAL ENGINES**

### Engine Manager (`/local_engines/`)

| Path | Purpose | User-Facing |
|------|---------|-------------|
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\local_engines\engine_manager.py` | Manages LLM backend selection | ❌ Backend |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\local_engines\llama_cpp/` | llama.cpp fallback engine | ❌ Backend |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\local_engines\engines.json` | Engine metadata and config | ✅ Editable |

**Supported Engines:**
- Ollama (default) - `llama3.2` model
- llama.cpp (CPU fallback) - Low-power mode

---

## 📦 **OTHER DIRECTORIES**

| Path | Purpose | User-Facing |
|------|---------|-------------|
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\docker/` | Docker orchestration files | ✅ Optional |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\Installer_Package/` | Windows installer build | ❌ Build-time |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\Scripts/` | PowerShell/VBS scripts | ✅ Utilities |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\Lib/` | Virtual environment libs | ❌ Backend |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\.chromadb/` | ChromaDB storage | ❌ Backend |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\__pycache__/` | Python bytecode cache | ❌ Backend |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\Backups/` | System backups | ✅ User accessible |
| `C:\Users\Julian Poopat\Documents\Management Class\RAG_System\restore_temp/` | Restore staging area | ✅ User review |

---

## 🌐 **EXTERNAL INTEGRATIONS**

### Obsidian Vault
- **Path:** `C:\Users\Julian Poopat\Documents\Obsidian\`
- **Integration:** ChatGPT MD plugin
- **API Endpoint:** `http://127.0.0.1:5000/v1/chat/completions`
- **Model Name:** `local-rag-llama3.2`

### Commands (Obsidian):
- `#ask {query}` - Query RAG system
- `#reindex` - Trigger reindexing
- `#summarize {file}` - Summarize document
- `#plan {topic}` - Generate essay plan

---

## 🔌 **PORT ALLOCATION**

| Module | Port | Auto-Start | Status |
|--------|------|------------|--------|
| Academic RAG | 5000 | ✅ Yes | ✅ Active |
| CLO Companion | 5001 | ❌ No | 🔧 Stub |
| Web Retriever | 5002 | ❌ No | 🔧 Stub |
| Automation Hub | 5003 | ❌ No | 🔧 Stub |
| System Monitor | None | ✅ Optional | ✅ Active |
| Voice Control | None | ❌ No | ✅ Active |
| Ollama | 11434 | ✅ Required | ✅ External |

---

## 📋 **GUI COMPONENTS**

### Control Panel Tabs/Buttons

| Component | Type | Action |
|-----------|------|--------|
| Status Indicators | Display | Real-time system status |
| Index Documents | Button | Triggers indexing |
| Start API Server | Button | Starts port 5000 API |
| Stop API Server | Button | Stops API gracefully |
| Test Query | Button | Tests `/query` endpoint |
| Health Check | Button | Runs diagnostics |
| Full System Test | Button | Comprehensive test |
| Backup System | Button | Creates backup ZIP |
| Restore System | Button | Restores from backup |
| Cloud Sync Now | Button | Manual VPS sync |
| Cloud Status | Button | Shows bridge status |
| Export Diagnostics | Button | Exports JSON report |
| About | Button | Shows version info |
| Open Logs Folder | Button | Opens Explorer |

---

## 🔐 **SECURITY & ENCRYPTION**

### Key Files
- `remote/keys/private.pem` - RSA private key (**NEVER UPLOAD**)
- `remote/keys/public.pem` - RSA public key (safe to share)
- `remote/keys/aes.key` - AES shared secret (must match VPS)
- `remote/keys/config.key` - Config encryption key (local)

### Encrypted Config Values
- `config/vps_config.json` → `api_token` (ENCRYPTED:...)
- `config/automation_hub_config.json` → webhook tokens (if encrypted)

---

## 📊 **RUNTIME DEPENDENCIES**

### Python Packages (requirements.txt)
- `chromadb>=0.4.0` - Vector database
- `flask>=3.0.0` - API framework
- `flask-cors>=4.0.0` - CORS support
- `ollama>=0.1.0` - Ollama Python client
- `pypdf2>=3.0.0` - PDF parsing
- `python-docx>=1.0.0` - DOCX parsing
- `requests>=2.31.0` - HTTP client
- `psutil>=5.9.0` - System monitoring
- `pygame>=2.5.0` - Audio (voice control)
- `torch>=2.0.0` - GPU (CLO Companion)
- `duckduckgo-search>=3.9.0` - Web search
- `fastapi>=0.104.0` - VPS server
- `uvicorn>=0.24.0` - ASGI server
- `customtkinter>=5.2.0` - Modern GUI (if v3 GUI exists)
- `Pillow>=10.0.0` - Image handling
- `cryptography>=41.0.0` - Encryption

### External Dependencies
- **Python:** 3.8+ (recommended 3.12)
- **Ollama:** Service running on `localhost:11434`
- **Llama 3.2:** Model installed in Ollama (`ollama pull llama3.2`)
- **whisper-cpp:** For voice control (optional)
- **CLO3D:** For CLO Companion (optional, stub)
- **ChromaDB:** Embedded (no separate service)

### Environment Expectations
- **Windows 10/11:** Primary platform
- **Tkinter:** Python GUI library (auto-configured)
- **UTF-8:** All file operations use UTF-8 encoding
- **Localhost Binding:** Default `127.0.0.1` (secure by default)
- **TLS:** Certificate verification enabled (configurable)

---

## 🎯 **USER-FACING vs BACKEND**

### User-Facing Files (✅)
- `RAG_Control_Panel.py` - Main launcher (double-click)
- `diagnostics.py` - Health check tool
- `config/*.json` - Configuration files (editable)
- `Backups/` - Backup ZIPs
- `Logs/` - Log files (viewable)
- Documentation (`*.md` files)
- `remote/rsa_generate.py` - Key generation script

### Backend-Only Files (❌)
- `core/*.py` - Core library
- `modules/*/api.py` - API servers
- `modules/*/query_llm.py` - Query processing
- `logger.py` - Logging system
- `*.db` - Database files
- `.chromadb/` - Vector store
- `__pycache__/` - Python cache
- `remote/keys/` - Encryption keys
- `data/` - Data storage

---

## 📈 **MODULE AUTO-START CONFIGURATION**

| Module | Auto-Start Default | Config Location |
|--------|-------------------|-----------------|
| Academic RAG | ✅ Yes | `config/suite_config.json` → `startup.auto_start_modules` |
| System Monitor | ✅ Yes | `config/suite_config.json` → `startup.auto_start_modules` |
| CLO Companion | ❌ No | Module config |
| Web Retriever | ❌ No | Module config |
| Automation Hub | ❌ No | Module config |
| Voice Control | ❌ No | Manual hotkey (F9) |

---

## 🔄 **BACKUP & RESTORE**

### Backup Includes
- `/config/` - All configuration files
- `/data/` - Memory database, ChromaDB semantic
- Module `module_info.json` files

### Backup Excludes
- `/Logs/` - Log files (too large)
- `/Web_Imports/` - Obsidian folder (backup separately)
- `/__pycache__/` - Python cache
- `/.chromadb/` - Main ChromaDB (backed up separately)

### Backup Location
- `Backups/RAG_Backup_YYYYMMDD_HHMMSS.zip`

---

## 🎓 **SUMMARY**

**Total Modules:** 6 (Academic RAG, CLO Companion, Web Retriever, Automation Hub, System Monitor, Voice Control)

**Active Modules:** 4 (Academic RAG, CLO Companion, System Monitor, Voice Control)

**Stub Modules:** 2 (Web Retriever, Automation Hub)

**Total Ports Used:** 4 (5000, 5001, 5002, 5003) + Ollama (11434)

**User-Facing Entry Points:** 1 (RAG_Control_Panel.py)

**Configuration Files:** 9+ JSON files in `/config/`

**Data Stores:** 2 (SQLite memory.db, ChromaDB)

**Documentation Files:** 12+ markdown files

---

**Last Updated:** 2025-10-29  
**Version:** v4.1.0-Julian-PolishFinal  
**Status:** Production-Ready

---

*This document provides a complete inventory of all files, modules, and resources in the Julian Assistant Suite. Use it for documentation sync, troubleshooting, and development planning.*

