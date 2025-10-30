"""
Context Graph Builder - Aggregates live data from all sources
Builds unified context payload for LLM queries
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
    from core.memory_manager import get_memory_manager
    from core.module_registry import get_registry
    from core.health_monitor import get_health_monitor
    from modules.system_monitor.monitor import get_system_monitor
except ImportError:
    def log(msg, category="CONTEXT"):
        print(f"[{category}] {msg}")
    def get_memory_manager():
        return None
    def get_registry():
        return None
    def get_health_monitor():
        return None
    def get_system_monitor():
        return None

class ContextGraph:
    """Builds unified context graph from all data sources"""
    
    def __init__(self, user: str = "julian"):
        self.user = user
        self.max_facts = 10
        self.max_docs = 5
        self.max_history = 5
    
    def build_context(self, query: Optional[str] = None, include_rag: bool = True, use_cache: bool = True) -> Dict[str, Any]:
        """
        Build complete context graph
        
        Args:
            query: Optional query text (for RAG retrieval)
            include_rag: Whether to include RAG context
            use_cache: Whether to use cached context if available
        
        Returns:
            Complete context dictionary
        """
        # Check cache first
        if use_cache and query:
            cached = self._get_cached_context(query)
            if cached:
                log("Using cached context", "CONTEXT")
                return cached
        
        # Build local context
        context = {
            "timestamp": datetime.now().isoformat(),
            "user": self.user,
            "memory": self._get_memory_context(),
            "system": self._get_system_context(),
            "voice": self._get_voice_context(),
            "clo": self._get_clo_context(),
            "rag": None,
            "metadata": {
                "sources": [],
                "fact_count": 0,
                "semantic_count": 0,
                "doc_count": 0,
                "remote_synced": False
            }
        }
        
        # Add RAG context if requested
        if include_rag and query:
            rag_context = self._get_rag_context(query)
            context["rag"] = rag_context
            context["metadata"]["doc_count"] = len(rag_context.get("documents", []))
        
        # Try to merge remote context if available
        try:
            from core.cloud_bridge import get_cloud_bridge
            bridge = get_cloud_bridge()
            if bridge.enabled:
                remote_context = bridge.fetch_remote_context()
                if remote_context:
                    context = self.merge_remote_context(context, remote_context)
        except:
            pass  # Remote context optional
        
        # Update metadata
        context["metadata"]["fact_count"] = len(context["memory"].get("facts", []))
        context["metadata"]["semantic_count"] = len(context["memory"].get("semantic_facts", []))
        context["metadata"]["sources"] = self._get_source_list(context)
        
        # Cache context for future use
        if query:
            self._cache_context(query, context)
        
        return context
    
    def merge_remote_context(self, local_ctx: Dict[str, Any], remote_ctx: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge local and remote context bundles
        
        Deduplicates by key, prefers newest timestamps
        Returns unified context bundle for LLM calls
        """
        try:
            merged = local_ctx.copy()
            
            # Merge memory facts
            local_facts = {f.get("key"): f for f in local_ctx.get("memory", {}).get("facts", [])}
            remote_facts = {f.get("key"): f for f in remote_ctx.get("memory", {}).get("facts", [])}
            
            # Merge: prefer newest timestamp
            for key, remote_fact in remote_facts.items():
                if key not in local_facts:
                    local_facts[key] = remote_fact
                else:
                    # Compare timestamps
                    local_time = local_facts[key].get("updated_at", "")
                    remote_time = remote_fact.get("updated_at", "")
                    if remote_time > local_time:
                        local_facts[key] = remote_fact
            
            merged["memory"]["facts"] = list(local_facts.values())
            merged["memory"]["fact_count"] = len(local_facts)
            
            # Merge RAG documents (combine, deduplicate by source)
            local_docs = local_ctx.get("rag", {}).get("documents", [])
            remote_docs = remote_ctx.get("rag", {}).get("documents", [])
            
            doc_sources = {doc.get("source"): doc for doc in local_docs}
            for doc in remote_docs:
                source = doc.get("source")
                if source not in doc_sources or doc.get("relevance", 0) > doc_sources[source].get("relevance", 0):
                    doc_sources[source] = doc
            
            if merged.get("rag"):
                merged["rag"]["documents"] = list(doc_sources.values())
                merged["rag"]["source_count"] = len(doc_sources)
            
            # Add remote metadata
            merged["metadata"]["remote_synced"] = True
            merged["metadata"]["remote_timestamp"] = remote_ctx.get("timestamp")
            
            log("Merged local and remote context", "CONTEXT")
            
            return merged
            
        except Exception as e:
            log(f"Error merging remote context: {e}", "CONTEXT", level="ERROR")
            return local_ctx  # Return local if merge fails
    
    def _get_cached_context(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached context if available and not expired"""
        try:
            import hashlib
            from core.memory_manager import get_memory_manager
            
            memory = get_memory_manager()
            query_hash = hashlib.md5(query.encode()).hexdigest()
            
            cursor = memory.conn.cursor()
            cursor.execute('''
                SELECT context_json, expires_at FROM context_cache
                WHERE user = ? AND query_hash = ? AND expires_at > CURRENT_TIMESTAMP
                ORDER BY created_at DESC
                LIMIT 1
            ''', (self.user, query_hash))
            
            row = cursor.fetchone()
            if row:
                import json
                return json.loads(row[0])
        except:
            pass
        return None
    
    def _cache_context(self, query: str, context: Dict[str, Any]):
        """Cache context for future use"""
        try:
            import hashlib
            import json
            from datetime import timedelta
            from core.memory_manager import get_memory_manager
            
            memory = get_memory_manager()
            query_hash = hashlib.md5(query.encode()).hexdigest()
            expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
            
            cursor = memory.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO context_cache (user, query_hash, context_json, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (self.user, query_hash, json.dumps(context), expires_at))
            memory.conn.commit()
        except:
            pass
    
    def _get_memory_context(self) -> Dict[str, Any]:
        """Get memory facts context (SQLite + ChromaDB semantic)"""
        try:
            memory = get_memory_manager()
            if memory:
                # Get facts from SQLite
                facts = memory.context_bundle(self.user, limit=self.max_facts)
                all_facts = memory.get_all_facts(self.user)
                
                # Get semantic memory from ChromaDB (if available)
                semantic_facts = self._get_semantic_memory()
                
                return {
                    "facts": facts,
                    "semantic_facts": semantic_facts,
                    "all_facts": all_facts,
                    "preferences": {
                        k: v for k, v in all_facts.items() if "prefer" in k.lower() or "preference" in k.lower()
                    },
                    "fact_count": len(facts),
                    "semantic_count": len(semantic_facts)
                }
        except Exception as e:
            log(f"Error getting memory context: {e}", "CONTEXT", level="ERROR")
        
        return {"facts": [], "semantic_facts": [], "all_facts": {}, "preferences": {}, "fact_count": 0, "semantic_count": 0}
    
    def _get_semantic_memory(self) -> List[Dict[str, Any]]:
        """Get semantic memory from ChromaDB"""
        try:
            import chromadb
            
            # Use semantic memory collection if exists
            chroma_path = os.path.join(BASE_DIR, "data", "chroma")
            if not os.path.exists(chroma_path):
                return []
            
            client = chromadb.PersistentClient(path=chroma_path)
            
            # Try to get semantic memory collection
            try:
                collection = client.get_collection("semantic_memory")
                
                # Get recent semantic memories (limit to 5)
                results = collection.get(limit=5)
                
                semantic_facts = []
                for i, metadata in enumerate(results.get('metadatas', [])):
                    semantic_facts.append({
                        "key": metadata.get('key', f'semantic_{i}'),
                        "value": results.get('documents', [])[i] if i < len(results.get('documents', [])) else "",
                        "category": "semantic",
                        "confidence": metadata.get('confidence', 0.8)
                    })
                
                return semantic_facts
            except:
                # Collection doesn't exist yet
                return []
                
        except Exception as e:
            log(f"Error getting semantic memory: {e}", "CONTEXT", level="WARNING")
            return []
    
    def _get_system_context(self) -> Dict[str, Any]:
        """Get system status context"""
        try:
            monitor = get_system_monitor()
            health_monitor = get_health_monitor()
            
            system_context = {
                "metrics": {},
                "module_status": {},
                "ollama_running": False
            }
            
            # Get metrics
            if monitor:
                metrics = monitor.get_metrics()
                system_context["metrics"] = {
                    "cpu_percent": metrics.get("cpu_percent", 0),
                    "ram_percent": metrics.get("ram_percent", 0),
                    "ram_mb": metrics.get("ram_mb", 0),
                    "gpu_percent": metrics.get("gpu_percent")
                }
                system_context["ollama_running"] = metrics.get("ollama_running", False)
            
            # Get module health
            if health_monitor:
                all_health = health_monitor.get_all_health()
                for module_id, health in all_health.items():
                    system_context["module_status"][module_id] = {
                        "status": health.get("status", "unknown"),
                        "port": health.get("port"),
                        "uptime": health.get("uptime_seconds", 0)
                    }
            
            return system_context
            
        except Exception as e:
            log(f"Error getting system context: {e}", "CONTEXT", level="ERROR")
            return {"metrics": {}, "module_status": {}, "ollama_running": False}
    
    def _get_voice_context(self) -> Dict[str, Any]:
        """Get recent voice command context"""
        try:
            from core.event_bus import get_event_bus
            
            bus = get_event_bus()
            # Get recent voice command events
            recent_voice_events = bus.get_recent_events(count=10, event_type="voice.command")
            
            return {
                "recent_commands": [
                    {
                        "command": e.get("data", {}).get("command"),
                        "action": e.get("data", {}).get("action"),
                        "timestamp": e.get("timestamp")
                    }
                    for e in recent_voice_events
                ],
                "command_count": len(recent_voice_events)
            }
            
        except Exception as e:
            log(f"Error getting voice context: {e}", "CONTEXT", level="ERROR")
            return {"recent_commands": [], "command_count": 0}
    
    def _get_clo_context(self) -> Dict[str, Any]:
        """Get CLO Companion active project context"""
        try:
            # Check for recent render events
            from core.event_bus import get_event_bus
            
            bus = get_event_bus()
            # Get recent render events
            recent_renders = bus.get_recent_events(count=3, event_type="render.complete")
            
            active_project = None
            if recent_renders:
                latest = recent_renders[-1]
                active_project = {
                    "obj_file": latest.get("data", {}).get("obj_file"),
                    "prompt": latest.get("data", {}).get("prompt"),
                    "timestamp": latest.get("timestamp")
                }
            
            return {
                "active_project": active_project,
                "recent_generations": [
                    {
                        "obj_file": e.get("data", {}).get("obj_file"),
                        "timestamp": e.get("timestamp")
                    }
                    for e in recent_renders
                ]
            }
            
        except Exception as e:
            log(f"Error getting CLO context: {e}", "CONTEXT", level="ERROR")
            return {"active_project": None, "recent_generations": []}
    
    def _get_rag_context(self, query: str) -> Dict[str, Any]:
        """Get RAG retrieval context"""
        try:
            from modules.academic_rag.query_llm import retrieve_local_context
            
            contexts, avg_distance, sources = retrieve_local_context(query, n_results=self.max_docs)
            
            return {
                "documents": [
                    {
                        "content": ctx[:500],  # Truncate for context
                        "source": src.get("source", "unknown"),
                        "relevance": 1.0 - avg_distance if avg_distance else 0.5
                    }
                    for ctx, src in zip(contexts, sources)
                ],
                "average_relevance": 1.0 - avg_distance if avg_distance else 0.5,
                "source_count": len(sources),
                "sources": sources
            }
            
        except Exception as e:
            log(f"Error getting RAG context: {e}", "CONTEXT", level="ERROR")
            return {"documents": [], "average_relevance": 0.0, "source_count": 0, "sources": []}
    
    def _get_source_list(self, context: Dict[str, Any]) -> List[str]:
        """Get list of all context sources"""
        sources = []
        
        if context.get("memory", {}).get("facts"):
            sources.append("memory")
        
        if context.get("rag", {}).get("documents"):
            sources.append("rag")
        
        if context.get("voice", {}).get("recent_commands"):
            sources.append("voice")
        
        if context.get("clo", {}).get("active_project"):
            sources.append("clo")
        
        if context.get("system", {}).get("metrics"):
            sources.append("system")
        
        return sources
    
    def context_preview(self, query: Optional[str] = None) -> str:
        """
        Generate human-readable context preview
        
        Returns:
            Formatted string showing what context will be included
        """
        context = self.build_context(query=query, include_rag=True)
        
        preview_lines = [
            "=== Context Graph Preview ===",
            f"Timestamp: {context['timestamp']}",
            f"User: {context['user']}",
            "",
            f"Memory Facts: {context['metadata']['fact_count']} facts",
            f"RAG Documents: {context['metadata']['doc_count']} documents",
            f"Sources: {', '.join(context['metadata']['sources'])}",
            "",
            "--- Memory Preferences ---"
        ]
        
        prefs = context['memory'].get('preferences', {})
        for key, value in list(prefs.items())[:5]:
            preview_lines.append(f"  {key}: {value}")
        
        if context.get('rag', {}).get('documents'):
            preview_lines.append("")
            preview_lines.append("--- RAG Context ---")
            for doc in context['rag']['documents'][:3]:
                preview_lines.append(f"  Source: {doc.get('source', 'unknown')}")
                preview_lines.append(f"  Relevance: {doc.get('relevance', 0):.2f}")
        
        preview_lines.append("")
        preview_lines.append("=== End Preview ===")
        
        return "\n".join(preview_lines)

# Global context graph instance
_context_graph_instance = None

def get_context_graph(user: str = "julian"):
    """Get global context graph builder (singleton)"""
    global _context_graph_instance
    if _context_graph_instance is None or _context_graph_instance.user != user:
        _context_graph_instance = ContextGraph(user=user)
    return _context_graph_instance

