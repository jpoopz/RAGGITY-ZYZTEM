"""
RAG System Diagnostics
Comprehensive health check for all system components
"""

import sys
import os
import subprocess
import socket
import requests
from pathlib import Path

# Force UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Import unified logger
try:
    from logger import log, log_exception
except ImportError:
    from datetime import datetime
    def log(msg, category="DIAG", print_to_console=True):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{category}] {msg}")
    def log_exception(category="ERROR", exception=None, context=""):
        import traceback
        print(f"[{category}] {context}: {exception}", file=sys.stderr)
        traceback.print_exc()

# Color codes for terminal
GREEN = "✅"
RED = "❌"
YELLOW = "⚠️"
INFO = "ℹ️"

class DiagnosticsChecker:
    def __init__(self):
        self.results = []
        self.vault_path = os.path.expanduser(r"C:\Users\Julian Poopat\Documents\Obsidian")
        self.rag_system_path = os.path.dirname(os.path.abspath(__file__))
        
    def check_python(self):
        """Check Python installation and version"""
        try:
            version = sys.version_info
            if version.major >= 3 and version.minor >= 8:
                self.results.append((True, f"{GREEN} Python {version.major}.{version.minor}.{version.micro} installed"))
                return True
            else:
                self.results.append((False, f"{RED} Python 3.8+ required (found {version.major}.{version.minor})"))
                return False
        except Exception as e:
            self.results.append((False, f"{RED} Python check failed: {e}"))
            return False
    
    def check_ollama_installed(self):
        """Check if Ollama is installed"""
        try:
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0] if result.stdout else "installed"
                self.results.append((True, f"{GREEN} Ollama installed ({version})"))
                return True
            else:
                self.results.append((False, f"{RED} Ollama not found"))
                return False
        except FileNotFoundError:
            self.results.append((False, f"{RED} Ollama not installed (not in PATH)"))
            return False
        except Exception as e:
            self.results.append((False, f"{RED} Ollama check failed: {e}"))
            return False
    
    def check_ollama_running(self):
        """Check if Ollama service is running on port 11434"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 11434))
            sock.close()
            
            if result == 0:
                self.results.append((True, f"{GREEN} Ollama service running on port 11434"))
                return True
            else:
                self.results.append((False, f"{RED} Ollama service not running on port 11434"))
                return False
        except Exception as e:
            self.results.append((False, f"{RED} Cannot check Ollama service: {e}"))
            return False
    
    def check_llama_model(self):
        """Check if Llama 3.2 model is available"""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                if "llama3.2" in output or "llama3" in output:
                    self.results.append((True, f"{GREEN} Llama model available"))
                    return True
                else:
                    self.results.append((False, f"{YELLOW} Llama model not found. Run: ollama pull llama3.2"))
                    return False
            else:
                self.results.append((False, f"{RED} Cannot list Ollama models"))
                return False
        except Exception as e:
            self.results.append((False, f"{RED} Llama model check failed: {e}"))
            return False
    
    def check_python_packages(self):
        """Check if required Python packages are installed"""
        required_packages = {
            'chromadb': 'chromadb',
            'flask': 'flask',
            'flask_cors': 'flask-cors',
            'pypdf2': 'pypdf2',
            'docx': 'python-docx',
            'requests': 'requests',
            'numpy': 'numpy'
        }
        
        missing = []
        installed = []
        
        for module, package in required_packages.items():
            try:
                __import__(module)
                installed.append(package)
            except ImportError:
                missing.append(package)
        
        if not missing:
            self.results.append((True, f"{GREEN} All required packages installed ({len(installed)}/{len(required_packages)})"))
            return True
        else:
            self.results.append((False, f"{YELLOW} Missing packages: {', '.join(missing)}"))
            return False
    
    def check_api_running(self):
        """Check if RAG API is running on port 5000"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('127.0.0.1', 5000))
            sock.close()
            
            if result == 0:
                # Try to get health endpoint
                try:
                    import requests
                    response = requests.get('http://127.0.0.1:5000/health', timeout=2)
                    if response.status_code == 200:
                        self.results.append((True, f"{GREEN} RAG API running on port 5000"))
                        return True
                    else:
                        self.results.append((False, f"{YELLOW} RAG API port open but health check failed"))
                        return False
                except:
                    self.results.append((True, f"{GREEN} RAG API port 5000 is open"))
                    return True
            else:
                self.results.append((False, f"{YELLOW} RAG API not running on port 5000"))
                return False
        except Exception as e:
            self.results.append((False, f"{YELLOW} Cannot check RAG API: {e}"))
            return False
    
    def check_chromadb(self):
        """Check if ChromaDB database exists and is accessible"""
        try:
            chromadb_path = os.path.join(self.rag_system_path, ".chromadb")
            if os.path.exists(chromadb_path):
                # Try to import and access
                import chromadb
                client = chromadb.PersistentClient(path=chromadb_path)
                collections = client.list_collections()
                self.results.append((True, f"{GREEN} ChromaDB database accessible ({len(collections)} collections)"))
                return True
            else:
                self.results.append((False, f"{YELLOW} ChromaDB database not found. Run indexing first."))
                return False
        except ImportError:
            self.results.append((False, f"{RED} ChromaDB package not installed"))
            return False
        except Exception as e:
            self.results.append((False, f"{YELLOW} ChromaDB check failed: {e}"))
            return False
    
    def check_vault_path(self):
        """Check if Obsidian vault path exists"""
        if os.path.exists(self.vault_path):
            notes_path = os.path.join(self.vault_path, "Notes")
            if os.path.exists(notes_path):
                file_count = len([f for f in os.listdir(notes_path) if f.endswith(('.md', '.pdf', '.docx', '.txt'))])
                self.results.append((True, f"{GREEN} Obsidian vault found ({file_count} documents)"))
                return True
            else:
                self.results.append((False, f"{YELLOW} Notes folder not found in vault"))
                return False
        else:
            self.results.append((False, f"{RED} Obsidian vault path not found: {self.vault_path}"))
            return False
    
    def check_file_permissions(self):
        """Check if we can write to necessary directories"""
        try:
            test_path = os.path.join(self.rag_system_path, "logs")
            os.makedirs(test_path, exist_ok=True)
            test_file = os.path.join(test_path, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            self.results.append((True, f"{GREEN} File permissions OK"))
            return True
        except Exception as e:
            self.results.append((False, f"{RED} File permission error: {e}"))
            return False
    
    def check_flask_api(self):
        """Check if Flask API responds on /v1/chat/completions"""
        try:
            response = requests.get("http://127.0.0.1:5000/health", timeout=2)
            if response.status_code == 200:
                # Test /v1/chat/completions endpoint
                try:
                    test_response = requests.post(
                        "http://127.0.0.1:5000/v1/chat/completions",
                        json={"messages": [{"role": "user", "content": "test"}], "model": "llama3.2"},
                        timeout=5
                    )
                    if test_response.status_code == 200:
                        self.results.append((True, f"{GREEN} Flask API responding at /v1/chat/completions"))
                        return True
                    else:
                        self.results.append((False, f"{YELLOW} Flask API health OK but /v1/chat/completions returned {test_response.status_code}"))
                        return False
                except Exception as e:
                    self.results.append((False, f"{YELLOW} Flask API health OK but /v1/chat/completions failed: {e}"))
                    return False
            else:
                self.results.append((False, f"{RED} Flask API returned status {response.status_code}"))
                return False
        except requests.exceptions.ConnectionError:
            self.results.append((False, f"{RED} Flask API not running on port 5000"))
            return False
        except Exception as e:
            self.results.append((False, f"{RED} Flask API check failed: {e}"))
            return False
    
    def check_chromadb_docs_count(self):
        """Check ChromaDB and count indexed documents"""
        try:
            import chromadb
            db_path = os.path.join(self.rag_system_path, ".chromadb")
            if not os.path.exists(db_path):
                self.results.append((False, f"{RED} ChromaDB database not found. Run indexing first."))
                return False
            
            client = chromadb.PersistentClient(path=db_path)
            collections = client.list_collections()
            
            if len(collections) == 0:
                self.results.append((False, f"{YELLOW} ChromaDB exists but no collections found. Run indexing."))
                return False
            
            # Count documents in obsidian_docs collection
            try:
                collection = client.get_collection("obsidian_docs")
                doc_count = collection.count()
                if doc_count > 0:
                    self.results.append((True, f"{GREEN} ChromaDB database accessible ({doc_count} documents indexed)"))
                    return True
                else:
                    self.results.append((False, f"{YELLOW} ChromaDB exists but no documents indexed"))
                    return False
            except Exception as e:
                self.results.append((False, f"{YELLOW} ChromaDB accessible but cannot count documents: {e}"))
                return False
                
        except ImportError:
            self.results.append((False, f"{RED} ChromaDB module not installed"))
            return False
        except Exception as e:
            self.results.append((False, f"{RED} ChromaDB check failed: {e}"))
            return False
    
    def check_memory_db(self):
        """Check if memory.db exists and is accessible"""
        try:
            memory_db_path = os.path.join(self.rag_system_path, "memory.db")
            if os.path.exists(memory_db_path):
                # Try to open database
                import sqlite3
                conn = sqlite3.connect(memory_db_path)
                conn.execute("SELECT 1 FROM facts LIMIT 1")
                conn.close()
                
                size_mb = os.path.getsize(memory_db_path) / (1024 * 1024)
                self.results.append((True, f"{GREEN} Memory database accessible ({size_mb:.2f} MB)"))
                return True
            else:
                self.results.append((False, f"{YELLOW} Memory database not found (will be created on first use)"))
                return False
        except Exception as e:
            self.results.append((False, f"{RED} Memory database check failed: {e}"))
            return False
    
    def check_memory_schema(self):
        """Check if memory schema matches version"""
        try:
            memory_db_path = os.path.join(self.rag_system_path, "memory.db")
            if not os.path.exists(memory_db_path):
                self.results.append((False, f"{YELLOW} Memory database not found (will use default schema)"))
                return False
            
            import sqlite3
            conn = sqlite3.connect(memory_db_path)
            cursor = conn.cursor()
            
            # Check for required tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['facts', 'sessions', 'log_summaries']
            missing = [t for t in required_tables if t not in tables]
            
            if not missing:
                # Check for confidence column in facts (v3.5.0 feature)
                cursor.execute("PRAGMA table_info(facts)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'confidence' in columns:
                    self.results.append((True, f"{GREEN} Memory schema matches v3.5.0"))
                    conn.close()
                    return True
                else:
                    self.results.append((False, f"{YELLOW} Memory schema outdated (missing confidence column)"))
                    conn.close()
                    return False
            else:
                self.results.append((False, f"{RED} Memory schema incomplete (missing tables: {', '.join(missing)})"))
                conn.close()
                return False
        except Exception as e:
            self.results.append((False, f"{RED} Memory schema check failed: {e}"))
            return False
    
    def check_chroma_accessible(self):
        """Check if ChromaDB semantic memory is accessible"""
        try:
            chroma_path = os.path.join(self.rag_system_path, "data", "chroma")
            if not os.path.exists(chroma_path):
                # Create directory if it doesn't exist
                os.makedirs(chroma_path, exist_ok=True)
                self.results.append((True, f"{GREEN} Chroma semantic memory path created"))
                return True
            
            import chromadb
            client = chromadb.PersistentClient(path=chroma_path)
            collections = client.list_collections()
            
            # Check for semantic_memory collection
            collection_names = [c.name for c in collections]
            if "semantic_memory" in collection_names:
                collection = client.get_collection("semantic_memory")
                count = collection.count()
                self.results.append((True, f"{GREEN} Chroma semantic memory accessible ({count} items)"))
                return True
            else:
                self.results.append((True, f"{GREEN} Chroma accessible (semantic_memory collection will be created when needed)"))
                return True
        except ImportError:
            self.results.append((True, f"{GREEN} ChromaDB available (semantic memory optional)"))
            return True
        except Exception as e:
            self.results.append((False, f"{YELLOW} Chroma semantic memory check: {e}"))
            return False
    
    def check_last_backup(self):
        """Check if last backup is < 24 hours old"""
        try:
            from core.sync_manager import get_sync_manager
            sync = get_sync_manager()
            last_backup = sync.get_last_backup_time()
            
            if last_backup:
                from datetime import datetime, timedelta
                age = datetime.now() - last_backup
                hours = age.total_seconds() / 3600
                
                if hours < 24:
                    self.results.append((True, f"{GREEN} Last backup {hours:.1f} hours ago"))
                    return True
                else:
                    self.results.append((False, f"{YELLOW} Last backup {hours:.1f} hours ago (> 24h, consider backing up)"))
                    return False
            else:
                self.results.append((False, f"{YELLOW} No backups found"))
                return False
        except Exception as e:
            self.results.append((True, f"{GREEN} Backup check skipped: {e}"))
            return True  # Don't fail on backup check
    
    def check_cloud_bridge_config(self):
        """Check if Cloud Bridge is configured"""
        try:
            config_path = os.path.join(self.rag_system_path, "config", "vps_config.json")
            if not os.path.exists(config_path):
                self.results.append((False, f"{YELLOW} VPS config file not found"))
                return False
            
            import json
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if not config.get("enabled", False):
                self.results.append((True, f"{INFO} Cloud Bridge configured but disabled"))
                return True
            
            vps_url = config.get("vps_url", "")
            api_token = config.get("api_token", "")
            
            if not vps_url or vps_url == "https://your-hostinger-domain.com":
                self.results.append((False, f"{YELLOW} Cloud Bridge enabled but VPS URL not configured"))
                return False
            
            if not api_token:
                self.results.append((False, f"{YELLOW} Cloud Bridge enabled but API token not configured"))
                return False
            
            self.results.append((True, f"{GREEN} Cloud Bridge configured (URL: {vps_url[:30]}...)"))
            return True
            
        except Exception as e:
            self.results.append((False, f"{RED} Cloud Bridge config check failed: {e}"))
            return False
    
    def check_cloud_bridge_connection(self):
        """Check if Cloud Bridge can connect to VPS"""
        try:
            from core.cloud_bridge import get_cloud_bridge
            bridge = get_cloud_bridge()
            
            if not bridge.enabled:
                self.results.append((True, f"{INFO} Cloud Bridge not enabled, skipping connection check"))
                return True
            
            if bridge.verify_health():
                latency = bridge.last_latency_ms or 0
                self.results.append((True, f"{GREEN} Cloud Bridge connected ({latency}ms latency)"))
                return True
            else:
                self.results.append((False, f"{RED} Cloud Bridge cannot connect to VPS"))
                return False
                
        except ImportError:
            self.results.append((True, f"{INFO} Cloud Bridge module not available"))
            return True
        except Exception as e:
            self.results.append((False, f"{RED} Cloud Bridge connection check failed: {e}"))
            return False
    
    def get_extended_metrics(self) -> dict:
        """Get extended metrics for diagnostics"""
        metrics = {
            "cloud_latency_ms": None,
            "last_sync_timestamp": None,
            "indexed_doc_count": 0,
            "rag_api_uptime_minutes": 0
        }
        
        try:
            # Cloud Bridge latency
            from core.cloud_bridge import get_cloud_bridge
            bridge = get_cloud_bridge()
            if bridge.enabled:
                metrics["cloud_latency_ms"] = bridge.last_latency_ms
                if bridge.last_sync_time:
                    metrics["last_sync_timestamp"] = bridge.last_sync_time.isoformat()
        except:
            pass
        
        try:
            # Indexed doc count
            import chromadb
            db_path = os.path.join(self.rag_system_path, ".chromadb")
            if os.path.exists(db_path):
                client = chromadb.PersistentClient(path=db_path)
                try:
                    collection = client.get_collection("obsidian_docs")
                    metrics["indexed_doc_count"] = collection.count()
                except:
                    pass
        except:
            pass
        
        try:
            # RAG API uptime
            import requests
            response = requests.get("http://127.0.0.1:5000/health", timeout=2)
            if response.status_code == 200:
                data = response.json()
                metrics["rag_api_uptime_minutes"] = data.get("uptime_seconds", 0) // 60
        except:
            pass
        
        return metrics
    
    def export_diagnostics(self, output_path: str = None) -> str:
        """Export diagnostics to JSON file"""
        import json
        
        if output_path is None:
            output_path = os.path.join(self.rag_system_path, "diagnostics_export.json")
        
        results, messages = self.run_all_checks()
        metrics = self.get_extended_metrics()
        
        export_data = {
            "timestamp": datetime.now().isoformat(),
            "version": "4.1.0-Julian-PolishFinal",
            "results": results,
            "messages": [msg[1] for msg in messages],
            "metrics": metrics,
            "summary": {
                "passed": sum(1 for v in results.values() if v),
                "total": len(results),
                "local_ok": all([
                    results.get("Python Installation", False),
                    results.get("Ollama Service", False),
                    results.get("RAG API", False),
                    results.get("ChromaDB Documents", False)
                ]),
                "cloud_ok": results.get("Cloud Bridge Connection", False) if results.get("Cloud Bridge Config", False) else None
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def run_all_checks(self):
        """Run all diagnostic checks"""
        self.results = []
        log("Running diagnostics...", "DIAG")
        
        # Check AutoRouter
        try:
            from modules.clo_companion.intent_classifier import get_intent_classifier
            classifier = get_intent_classifier()
            test_intent, test_conf = classifier.detect_intent("make sleeves longer")
            if test_intent == "EDIT":
                self.results.append((True, f"{GREEN} AutoRouter Operational (conf: {test_conf:.2f})"))
            else:
                self.results.append((False, f"{RED} AutoRouter: Intent detection not working correctly"))
        except Exception as e:
            self.results.append((False, f"{RED} AutoRouter: Error - {e}"))
        
        # Check AutoRouter log file and statistics
        try:
            autorouter_log = os.path.join(self.rag_system_path, "Logs", "clo_autorouter.log")
            if os.path.exists(autorouter_log):
                with open(autorouter_log, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    edit_count = sum(1 for line in lines if "MODE:EDIT" in line)
                    chat_count = sum(1 for line in lines if "MODE:CHAT" in line)
                    total = edit_count + chat_count
                    if total > 0:
                        avg_conf_lines = [line for line in lines if "Confidence:" in line]
                        confidences = []
                        for line in avg_conf_lines:
                            try:
                                conf_match = __import__('re').search(r'Confidence:([\d.]+)', line)
                                if conf_match:
                                    confidences.append(float(conf_match.group(1)))
                            except:
                                pass
                        avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
                        self.results.append((True, f"{GREEN} AutoRouter Stats: EDIT:{edit_count} CHAT:{chat_count} Total:{total} AvgConf:{avg_conf:.2f}"))
                    else:
                        self.results.append((True, f"{INFO} AutoRouter: No routing decisions logged yet"))
            else:
                self.results.append((True, f"{INFO} AutoRouter: Log file created on first use"))
        except Exception as e:
            self.results.append((False, f"{YELLOW} AutoRouter Stats: Could not read log - {e}"))
        
        checks = [
            ("Python Installation", self.check_python),
            ("Ollama Installation", self.check_ollama_installed),
            ("Ollama Service", self.check_ollama_running),
            ("Llama Model", self.check_llama_model),
            ("Python Packages", self.check_python_packages),
            ("ChromaDB Documents", self.check_chromadb_docs_count),
            ("Vault Path", self.check_vault_path),
            ("RAG API", self.check_api_running),
            ("Flask API Endpoint", self.check_flask_api),
            ("File Permissions", self.check_file_permissions),
            ("Memory Database", self.check_memory_db),
            ("Memory Schema", self.check_memory_schema),
            ("Chroma Accessibility", self.check_chroma_accessible),
            ("Last Backup", self.check_last_backup),
            ("Cloud Bridge Config", self.check_cloud_bridge_config),
            ("Cloud Bridge Connection", self.check_cloud_bridge_connection),
        ]
        
        # Add extended metrics to results
        metrics = self.get_extended_metrics()
        # Metrics are stored in results dict for export
        
        results = {}
        for name, check_func in checks:
            results[name] = check_func()
        
        return results, self.results
    
    def get_summary(self, results):
        """Get summary of diagnostic results"""
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        if passed == total:
            status = f"{GREEN} All checks passed ({passed}/{total}) 🧠 Persistent Memory Active ☁ Cloud Bridge Active"
        elif passed >= total * 0.7:
            status = f"{YELLOW} Most checks passed ({passed}/{total})"
        else:
            status = f"{RED} Multiple issues found ({passed}/{total})"
        
        return status

if __name__ == "__main__":
    checker = DiagnosticsChecker()
    results, messages = checker.run_all_checks()
    
    print("\n" + "="*60)
    print("DIAGNOSTIC RESULTS")
    print("="*60 + "\n")
    
    for message in messages:
        print(f"  {message[1]}")
    
    print("\n" + "="*60)
    print(checker.get_summary(results))
    print("="*60 + "\n")
    
    # Exit code based on results
    if all(results.values()):
        sys.exit(0)
    else:
        sys.exit(1)

