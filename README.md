### CLO 3D Bridge — Windows Firewall Note

If the CLO Bridge listener isn't reachable (timeout/refused), Windows Defender Firewall may be blocking the port.

Quick steps:

1. Open Windows Security → Firewall & network protection → Advanced settings.
2. Inbound Rules → New Rule… → Port → TCP → Specific local ports: 9933 (or your configured port).
3. Allow the connection → apply to Domain/Private (and Public if needed) → Name: "CLO Bridge".
4. Re-run the listener in CLO: Script → Run Script… → `modules\clo_companion\clo_bridge_listener.py`.
5. Test locally:

```bash
curl -s "http://127.0.0.1:8000/clo/health?port=9933" | jq
```

# RAGGITY ZYZTEM 2.0 🎯

**Local-First RAG Engine with Premium UI and CLO 3D Integration**

A production-ready Retrieval Augmented Generation system combining powerful document processing, a beautiful dark-themed desktop interface, and direct CLO 3D garment design control. Built for academic research, knowledge management, and fashion tech workflows with optional cloud synchronization.

---

## ✨ Features

- 🧠 **RAG Engine**: FAISS/ChromaDB vector search + Ollama/OpenAI LLM integration
- 🎨 **Premium UI**: CustomTkinter dark theme with real-time monitoring and visual metrics
- 👗 **CLO 3D Bridge**: TCP listener + client for garment import/export/simulation/screenshots
- ☁️ **Hybrid Cloud**: Optional telemetry and vector backup to remote VPS
- 📊 **System Monitor**: Live CPU/RAM/GPU tracking with color-coded progress bars
- 🔍 **Smart Troubleshooter**: Automatic log analysis and fix suggestions
- 📝 **Export Tools**: Query results to Markdown, system snapshots to JSON
- ⚡ **Performance Optimizations**:
  - **Embedding Cache**: Disk-backed cache prevents redundant API calls
  - **Batched Embeddings**: Process chunks in batches of 64 for efficiency
  - **Paragraph-Aware Chunking**: Intelligent text splitting with 10-15% overlap
  - **Concurrent Ingestion**: Thread-pooled document processing
  - **Deduplication**: Automatic removal of duplicate chunks
- 🎯 **Advanced Features**:
  - **Streaming Answers**: Real-time token streaming for faster perceived responses
  - **Vector Store Switcher**: Easy toggle between FAISS and ChromaDB in UI
  - **Toast Notifications**: Non-intrusive success/error feedback
  - **Debounced Queries**: Prevents accidental duplicate submissions
  - **Profiling**: Built-in span profiler for performance monitoring
  - **Structured Telemetry**: JSON event logging with Prometheus metrics

---

## 🚀 Quick Start (Windows)

### Prerequisites
- Python 3.8+
- Ollama (recommended) or OpenAI API key
- Optional: CLO 3D for garment design integration

### Installation

**Option 1: Automated Setup**
```powershell
.\tools\setup_local.bat
```

**Option 2: Manual Setup**
```powershell
# Create virtual environment
py -3 -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Running the System

**Step 1: Start API Server**
```powershell
.\start_api.bat
```
Server starts at `http://localhost:8000`

**Step 2: Launch UI**
```powershell
.\run_ui.bat
```

That's it! The UI will open with all features ready.

---

## 📋 Core Workflows

### 1. Document Ingestion & Query

**Via UI:**
1. Open **Ingest** tab
2. Browse or drag-and-drop files/folders
3. Click **Ingest Path** or **Ingest File**
4. Switch to **Query** tab
5. Enter multi-line question (Ctrl+Enter to submit)
6. View answer with collapsible context sources
7. Export to Markdown if needed

**Via API:**
```bash
curl -X POST "http://localhost:8000/ingest-path?path=C:/Documents"
curl -X GET "http://localhost:8000/query?q=What%20is%20RAG?"
```

### 2. CLO 3D Integration

**Setup CLO Bridge:**
1. Launch CLO 3D application
2. In CLO: `File > Script > Run Script...`
3. Navigate to: `modules/clo_companion/clo_bridge_listener.py`
4. Click Run — you should see: *"CLO Bridge listening on 127.0.0.1:51235"*

**Control from UI:**
1. Open **CLO3D** tab
2. Click **🔌 Connect** (instructions auto-show on error)
3. Use action buttons:
   - **📁 Import Garment** — Load .zprj, .obj, .fbx files
   - **💾 Export Garment** — Save to various formats
   - **▶️ Run Simulation** — Physics simulation with custom steps
   - **📷 Take Screenshot** — Capture viewport to `/exports/clo_shots/`

**Script Generation (Mode B):**
For air-gapped or one-off tasks, generate standalone CLO scripts:
```python
from modules.clo_companion.script_factory import make_import_script

make_import_script(
    garment_path="C:/Projects/shirt.zprj",
    out_script_path="C:/Scripts/import_shirt.py"
)
# Then in CLO: File > Script > Run Script... > Select import_shirt.py
```

### 3. System Monitoring

**Dashboard Tab:**
- Quick actions: Open data folder, rebuild index, troubleshoot
- Live status: API health, GPU detection, index size, latest logs

**System Tab:**
- Real-time CPU/RAM/GPU metrics with color-coded bars
- Take snapshots to `/logs/system_snapshot-<timestamp>.json`

**Logs Tab:**
- Filter by level: ALL / INFO / WARN / ERROR
- Pause/Resume tailing
- Open logs folder directly

### 4. Hybrid Cloud Bridge (Optional)

**Setup Remote Server:**
```bash
# On VPS
cd RAG_System/remote
uvicorn cloud_bridge_server:app --host 0.0.0.0 --port 9000
```

**Configure Client:**
```bash
# Set environment variables
set CLOUD_URL=https://your-vps.com/api
set CLOUD_KEY=your_secret_key
set HYBRID_MODE=1
```

**Use Bridge Tab:**
- Send test events to verify connectivity
- Push vector backups for redundancy
- Enable auto-backup on ingestion

When `HYBRID_MODE=1`, queries are delegated to cloud if available and healthy.

---

## 🗂️ Project Structure

```
RAG_System/
├── core/                   # Core functionality
│   ├── llm_connector.py    # Ollama/OpenAI abstraction
│   ├── rag_engine.py       # FAISS/ChromaDB RAG logic
│   ├── cloud_bridge.py     # Remote telemetry client
│   ├── config.py           # Centralized config with YAML support
│   └── gpu.py              # Unified GPU monitoring (pynvml/nvidia-smi)
├── modules/                # Feature modules
│   ├── academic_rag/       # Academic document processing
│   ├── web_retriever/      # Web search integration
│   ├── smart_troubleshooter/  # Auto-diagnostic and fixes
│   ├── system_monitor/     # Resource usage tracking
│   ├── clo_companion/      # CLO 3D integration
│   │   ├── clo_bridge_listener.py  # Runs in CLO Python
│   │   ├── clo_client.py   # External client
│   │   └── script_factory.py  # Generate standalone CLO scripts
│   └── cursor_bridge/      # Cursor IDE integration
├── ui/                     # Desktop interface
│   ├── main_window.py      # CustomTkinter app with 7 tabs
│   └── theme.py            # Premium dark theme + components
├── remote/                 # Cloud bridge server
│   └── cloud_bridge_server.py
├── tools/                  # Build & deployment
│   ├── export_local.bat    # Create deployment package
│   └── setup_local.bat     # Automated environment setup
├── rag_api.py             # FastAPI server (main API)
├── config.yaml            # Configuration file
└── requirements.txt       # Python dependencies
```

---

## ⚙️ Configuration

RAGGITY uses a **unified settings system** with a clear precedence order and multiple persistence options.

### Settings Precedence Order

Settings are loaded in this order (highest to lowest priority):

```
1. Environment Variables (highest - always wins)
   ↓
2. ui/config.json (UI runtime settings)
   ↓
3. config.yaml (repository configuration)
   ↓
4. Defaults from Settings schema (lowest - fallback)
```

**Example**: If you set `VECTOR_STORE=chroma` in environment, it will override any value in config.yaml or ui/config.json.

### Configuration Files

#### config.yaml (Repository Settings)
Application-level configuration that's safe to commit to version control:

```yaml
# LLM Provider
provider: "ollama"        # or "openai"
model_name: "llama3.2"
model_secondary: null     # Optional secondary model for complex queries
embedding_model: "nomic-embed-text"

# Generation Settings
temperature: 0.3          # 0.0 (deterministic) to 2.0 (creative)
timeout: 120              # Request timeout in seconds

# Vector Store
vector_store: "faiss"     # or "chroma"
batch_size: 64            # Embedding batch size
max_k: 5                  # Max contexts to retrieve

# Paths
data_dir: "data"
vector_dir: "vectorstore"
chroma_dir: ".chromadb"

# Hybrid Mode
hybrid_mode: true         # Enable cloud query delegation

# UI
theme: "dark"             # dark, light, or auto
show_advanced: false
```

#### ui/config.json (UI Runtime Settings)
User preferences that change frequently (auto-generated, don't edit manually):

```json
{
  "theme": "dark",
  "vector_store": "faiss",
  "max_k": 5,
  "show_advanced": false
}
```

### Secrets Management

**⚠️ SECURITY: Never commit secrets to version control!**

Sensitive keys are **only** loaded from environment variables and **never** saved to config files:

- `OPENAI_API_KEY` - OpenAI API authentication
- `CLOUD_KEY` - Cloud bridge authentication
- `API_KEY` - Local API authentication

**Why?** Prevents accidental commits of secrets to git repositories.

**How to set secrets:**
```bash
# Windows
set OPENAI_API_KEY=sk-your-key-here
set CLOUD_KEY=your-secret-key

# Linux/Mac
export OPENAI_API_KEY=sk-your-key-here
export CLOUD_KEY=your-secret-key
```

Or create a `.env` file (use `env.sample` as template) - this file is git-ignored.

### Using Settings in UI

**Save Button** (Quick Save):
- Saves to `ui/config.json` only
- For UI preferences that change frequently
- Takes effect immediately (no restart)
- Fields: theme, vector_store, max_k, show_advanced

**Persist Button** (Permanent Save):
- Saves to `config.yaml`
- For application-level settings
- Survives UI restarts and updates
- Excludes secrets (safe to commit)

### Settings That Require Restart

Some settings require restarting the API and/or UI to take effect:

**Requires API Restart:**
- `vector_store` (FAISS ↔ ChromaDB)
- `provider` (Ollama ↔ OpenAI)
- `model_name`, `embedding_model`
- `data_dir`, `vector_dir`

**Requires UI Restart:**
- `theme` (if changed via config.yaml)

**No Restart Required:**
- `max_k` (via UI Settings)
- `show_advanced`
- `theme` (via UI Settings)

The UI will show a warning toast if you change settings that require restart.

### Settings Schema

All settings are defined in `core/settings_schema.py` using Pydantic for type safety:

**Groups:**
- **Environment**: env (dev/prod)
- **Paths**: data_dir, vector_dir, chroma_dir
- **Vector Store**: vector_store (faiss/chroma)
- **LLM**: provider, model_name, model_secondary, temperature, max_tokens, timeout
- **Ollama**: ollama_host
- **OpenAI**: openai_api_key, openai_model, openai_embedding_model
- **Hybrid**: hybrid_mode, cloud_url, cloud_key
- **API/Security**: cors_allow, api_key
- **UI**: theme, show_advanced
- **Performance**: batch_size, max_k

**Validation:**
- Temperature: 0.0 - 2.0
- Batch size: 1 - 512
- Max K: 1 - 20
- Provider: "ollama" or "openai" only
- Vector store: "faiss" or "chroma" only

### Vector Store Selection

RAGGITY supports two vector database backends:

**FAISS (Default)**
- Fast and lightweight
- In-memory with file persistence
- No external dependencies
- Best for most use cases

**ChromaDB**
- Feature-rich persistent storage
- Better for large-scale deployments
- Requires `chromadb` package: `pip install chromadb`
- Stores data in `.chromadb/` directory

**Switching Vector Stores:**

1. **Via UI**: Settings tab → Select vector store → Save
2. **Via config.yaml**: Set `vector_store: chroma`
3. **Via environment**: `set VECTOR_STORE=chroma`

**Note**: Changing vector stores requires restarting the API and UI. Your existing index data is stored separately for each backend.

### Environment Variables (Override config.yaml)
```bash
set PROVIDER=ollama
set MODEL_NAME=llama3.2
set OPENAI_API_KEY=sk-...
set VECTOR_STORE=faiss         # or chroma
set HYBRID_MODE=1
set CLOUD_URL=https://vps.example.com/api
set CLOUD_KEY=secret123
set CLO_PORT=51235
```

---

## 📚 API Reference

**Base URL:** `http://localhost:8000`

### Core Endpoints

#### `GET /health`
Health check with service status.

**Response:**
```json
{
  "status": "ok",
  "ollama_running": true,
  "vector_store": "faiss"
}
```

#### `POST /ingest-path?path=<path>`
Ingest documents from directory or file.

**Response:**
```json
{
  "success": true,
  "chunks_added": 142,
  "elapsed": 3.2
}
```

#### `GET /query?q=<question>&k=<top_k>`
Query the RAG system.

**Parameters:**
- `q` (required): Query string
- `k` (optional, default=5): Number of context chunks

**Response:**
```json
{
  "answer": "Based on the documents...",
  "contexts": ["chunk1...", "chunk2..."],
  "delegated": false
}
```

#### `GET /troubleshoot`
Run diagnostic analysis on system logs.

**Response:**
```json
{
  "issues": [...],
  "recommendations": [...]
}
```

#### `GET /system-stats`
Current system resource usage.

**Response:**
```json
{
  "cpu_percent": 23.5,
  "mem_percent": 45.2,
  "gpu": {
    "available": true,
    "name": "NVIDIA GeForce RTX 3060",
    "utilization_percent": 12.0,
    "memory_used_mb": 1024,
    "memory_total_mb": 12288
  },
  "ollama_running": true
}
```

---

## 🛠️ Development

### Running Tests
```powershell
# Unit tests
pytest -q

# With coverage
pytest --cov=core --cov=modules --cov-report=html

# Evaluation tests
pytest tests/test_evals.py -v

# Specific test file
pytest tests/test_clo_client.py -v
```

### Load Testing
```bash
# Simple Python load runner
python tests/load_query.py -n 100 -c 5

# With Locust (install first: pip install locust)
locust -f locustfile.py --host http://localhost:8000 --users 10 --spawn-rate 2 --run-time 60s --headless

# Locust with web UI
locust -f locustfile.py --host http://localhost:8000
# Then open: http://localhost:8089
```

### Pre-commit Hooks
```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### CI/CD
GitHub Actions workflow runs on push/PR:
- Pytest test suite with coverage
- Pre-commit checks (Black, Isort, Flake8)
- Evaluation golden tests
- Coverage upload to Codecov
- Automatic draft release on version tags

---

## 🐛 Troubleshooting

### API won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Try different port
set PORT=8080
python rag_api.py
```

### Ollama connection issues
```bash
# Verify Ollama is running
curl http://localhost:11434/api/tags

# If not installed, download from ollama.ai
```

### CLO Bridge won't connect
1. Ensure CLO 3D is running
2. Check bridge listener is active in CLO script console
3. Verify port 51235 is not blocked by firewall
4. Try setting different port: `set CLO_PORT=52000`
5. Review CLO's Python console for error messages

### GPU not detected
```bash
# Check NVIDIA drivers
nvidia-smi

# Install pynvml for better detection
pip install pynvml
```

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📦 Deployment

### Local Export
```powershell
.\tools\export_local.bat
```
Creates timestamped package in `dist/RAGGITY_Local_<timestamp>/`

### Remote VPS Setup
```bash
# On server
git clone <repo>
cd RAG_System
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start cloud bridge server
cd remote
uvicorn cloud_bridge_server:app --host 0.0.0.0 --port 9000

# Or use systemd service for auto-restart
```

---

## 🤝 Contributing

1. Follow PEP 8 style guide
2. Run `pre-commit` before committing
3. Add tests for new features
4. Update documentation

---

## 📄 License

MIT License - See LICENSE file for details

---

## 🙏 Acknowledgments

- **Ollama** for local LLM inference
- **FAISS** for efficient vector search
- **CustomTkinter** for modern UI components
- **FastAPI** for high-performance API framework
- **CLO 3D** for garment design integration

---

## 📞 Support

- **Issues**: Use GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Logs**: Check `logs/app.log` for detailed error traces

---

**Built with ❤️ for academic research and fashion tech workflows**
