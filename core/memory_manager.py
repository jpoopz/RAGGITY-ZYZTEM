"""
Persistent Memory Manager - SQLite-based long-term memory
Stores facts, preferences, and session summaries
"""

import os
import sys
import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log
except ImportError:
    def log(msg, category="MEMORY"):
        print(f"[{category}] {msg}")

class MemoryManager:
    """Manages persistent memory using SQLite"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(BASE_DIR, "memory.db")
        
        self.db_path = db_path
        self.conn = None
        self.summary_thread = None
        self._init_database()
        self._start_auto_summary_thread()
    
    def close(self):
        """Gracefully close database connection"""
        try:
            # Stop summary thread
            if hasattr(self, '_summary_running'):
                self._summary_running = False
            
            if self.summary_thread and self.summary_thread.is_alive():
                # Wait for thread to finish
                self.summary_thread.join(timeout=2)
            
            if self.conn:
                self.conn.close()
                log("Memory database closed", "MEMORY")
        except Exception as e:
            log(f"Error closing memory database: {e}", "MEMORY", level="WARNING")
    
    def _init_database(self):
        """Initialize SQLite database with tables using schema.sql"""
        try:
            # Enable WAL mode for better concurrency
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            # Enable WAL mode
            self.conn.execute('PRAGMA journal_mode=WAL')
            self.conn.execute('PRAGMA synchronous=NORMAL')
            self.conn.execute('PRAGMA cache_size=10000')
            self.conn.execute('PRAGMA temp_store=MEMORY')
            
            cursor = self.conn.cursor()
            
            # Load schema from file if exists, otherwise use inline schema
            schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
            if os.path.exists(schema_path):
                with open(schema_path, 'r', encoding='utf-8') as f:
                    schema_sql = f.read()
                    cursor.executescript(schema_sql)
            else:
                # Fallback to inline schema (same as schema.sql)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS facts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user TEXT NOT NULL,
                        key TEXT NOT NULL,
                        value TEXT NOT NULL,
                        confidence REAL DEFAULT 1.0,
                        category TEXT DEFAULT 'general',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user, key)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        message TEXT NOT NULL,
                        level TEXT DEFAULT 'INFO',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user TEXT NOT NULL,
                        session_id TEXT NOT NULL,
                        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                        end_time DATETIME,
                        summary TEXT,
                        facts_learned INTEGER DEFAULT 0,
                        UNIQUE(user, session_id)
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS log_summaries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user TEXT NOT NULL,
                        period_start DATETIME NOT NULL,
                        period_end DATETIME NOT NULL,
                        summary_text TEXT,
                        key_insights TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS context_cache (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user TEXT NOT NULL,
                        query_hash TEXT,
                        context_json TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        expires_at DATETIME
                    )
                ''')
                
                # Create indexes
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_facts_user_updated ON facts(user, updated_at DESC)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_logs_category_time ON logs(category, created_at DESC)')
            
            self.conn.commit()
            
            # Check database size and compact if needed
            self._check_and_compact()
            
            log("Memory database initialized with WAL mode", "MEMORY")
            
        except Exception as e:
            log(f"Error initializing memory database: {e}", "MEMORY", level="ERROR")
            raise
    
    def _check_and_compact(self):
        """Check database size and compact if > 100 MB"""
        try:
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            size_mb = db_size / (1024 * 1024)
            
            if size_mb > 100:
                log(f"Database size {size_mb:.1f}MB > 100MB, compacting...", "MEMORY")
                cursor = self.conn.cursor()
                cursor.execute('VACUUM')
                self.conn.commit()
                new_size = os.path.getsize(self.db_path) / (1024 * 1024)
                log(f"Database compacted: {size_mb:.1f}MB -> {new_size:.1f}MB", "MEMORY")
        except Exception as e:
            log(f"Error during compaction: {e}", "MEMORY", level="WARNING")
    
    def remember(self, user: str, key: str, value: Any, category: str = "general", confidence: float = 1.0):
        """
        Remember a fact about the user
        
        Args:
            user: User identifier
            key: Fact key (e.g., "prefers_concise")
            value: Fact value (will be JSON-encoded if not string)
            category: Optional category for organization
        """
        try:
            if not isinstance(value, str):
                value = json.dumps(value)
            
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO facts (user, key, value, category, confidence, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user, key, value, category, confidence))
            
            self.conn.commit()
            log(f"Remembered: {user}.{key} = {value[:50]}", "MEMORY")
            
        except Exception as e:
            log(f"Error remembering fact: {e}", "MEMORY", level="ERROR")
    
    def recall(self, user: str, key: Optional[str] = None, limit: int = 10, default: Any = None) -> Any:
        """
        Recall facts about the user
        
        Args:
            user: User identifier
            key: Fact key (if None, returns multiple facts up to limit)
            limit: Maximum number of facts to return (if key is None)
            default: Default value if key specified and not found
        
        Returns:
            If key specified: Single fact value or default
            If key is None: List of facts up to limit
        """
        try:
            cursor = self.conn.cursor()
            
            if key:
                # Single fact lookup
                cursor.execute('''
                    SELECT value, confidence FROM facts
                    WHERE user = ? AND key = ?
                ''', (user, key))
                
                row = cursor.fetchone()
                if row:
                    value = row[0]
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                else:
                    return default
            else:
                # Multiple facts (limit)
                cursor.execute('''
                    SELECT key, value, confidence, category, updated_at FROM facts
                    WHERE user = ?
                    ORDER BY updated_at DESC, confidence DESC
                    LIMIT ?
                ''', (user, limit))
                
                facts = []
                for row in cursor.fetchall():
                    value = row[1]
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        pass
                    
                    facts.append({
                        "key": row[0],
                        "value": value,
                        "confidence": row[2],
                        "category": row[3],
                        "updated_at": row[4]
                    })
                
                return facts
                
        except Exception as e:
            log(f"Error recalling facts: {e}", "MEMORY", level="ERROR")
            return default if key else []
    
    def context_bundle(self, user: str, limit: int = 10, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get context bundle of recent/relevant facts
        
        Args:
            user: User identifier
            limit: Maximum number of facts to return
            category: Optional category filter
        
        Returns:
            List of facts as dictionaries
        """
        try:
            cursor = self.conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT key, value, category, updated_at
                    FROM facts
                    WHERE user = ? AND category = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                ''', (user, category, limit))
            else:
                cursor.execute('''
                    SELECT key, value, category, updated_at
                    FROM facts
                    WHERE user = ?
                    ORDER BY updated_at DESC
                    LIMIT ?
                ''', (user, limit))
            
            facts = []
            for row in cursor.fetchall():
                value = row[1]
                try:
                    value = json.loads(value)
                except json.JSONDecodeError:
                    pass
                
                facts.append({
                    "key": row[0],
                    "value": value,
                    "category": row[2],
                    "updated_at": row[3]
                })
            
            return facts
            
        except Exception as e:
            log(f"Error getting context bundle: {e}", "MEMORY", level="ERROR")
            return []
    
    def forget(self, user: str, key: str):
        """Forget a specific fact"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                DELETE FROM facts
                WHERE user = ? AND key = ?
            ''', (user, key))
            self.conn.commit()
            log(f"Forgot: {user}.{key}", "MEMORY")
        except Exception as e:
            log(f"Error forgetting fact: {e}", "MEMORY", level="ERROR")
    
    def get_all_facts(self, user: str) -> Dict[str, Any]:
        """Get all facts for a user as dictionary"""
        facts = {}
        context_bundle = self.context_bundle(user, limit=1000)
        for fact in context_bundle:
            facts[fact["key"]] = fact["value"]
        return facts
    
    def summarize_recent(self, user: str = "julian", hours: int = 6):
        """
        Auto-summarize recent logs and sessions
        
        Args:
            user: User identifier
            hours: How many hours back to summarize
        """
        try:
            from logger import get_recent_logs
            
            # Get recent logs
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # Read recent log entries
            log_entries = get_recent_logs(lines=1000)  # Adjust as needed
            
            if not log_entries:
                return
            
            # Simple extraction of key patterns (can be enhanced with LLM)
            insights = []
            fact_count = 0
            
            for entry in log_entries:
                # Look for preference patterns
                if "prefers" in entry.lower() or "preference" in entry.lower():
                    insights.append(entry)
                    fact_count += 1
                
                # Look for error patterns
                if "[ERROR]" in entry:
                    insights.append(f"Error occurred: {entry[:100]}")
            
            if insights:
                summary_text = "\n".join(insights[:20])  # Limit summary length
                
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO log_summaries (user, period_start, period_end, summary_text, key_insights)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user, cutoff_time.isoformat(), datetime.now().isoformat(), summary_text, str(fact_count)))
                
                self.conn.commit()
                log(f"Auto-summarized {fact_count} insights from last {hours} hours", "MEMORY")
                
        except Exception as e:
            log(f"Error in auto-summarize: {e}", "MEMORY", level="ERROR")
    
    def _start_auto_summary_thread(self):
        """Start background thread for periodic summarization"""
        import threading
        import time
        
        def summary_loop():
            while hasattr(self, '_summary_running') and self._summary_running:
                try:
                    time.sleep(6 * 60 * 60)  # 6 hours
                    if hasattr(self, '_summary_running') and self._summary_running:
                        self.summarize_recent()
                except Exception as e:
                    log(f"Error in summary loop: {e}", "MEMORY", level="ERROR")
        
        self._summary_running = True
        self.summary_thread = threading.Thread(target=summary_loop, daemon=True)
        self.summary_thread.start()
        log("Auto-summary thread started (6-hour interval)", "MEMORY")
    
    def start_session(self, user: str, session_id: Optional[str] = None):
        """Start a new session"""
        if session_id is None:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR IGNORE INTO sessions (user, session_id)
                VALUES (?, ?)
            ''', (user, session_id))
            self.conn.commit()
            return session_id
        except Exception as e:
            log(f"Error starting session: {e}", "MEMORY", level="ERROR")
            return None
    
    def end_session(self, user: str, session_id: str, summary: Optional[str] = None):
        """End a session with optional summary"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE sessions
                SET end_time = CURRENT_TIMESTAMP, summary = ?
                WHERE user = ? AND session_id = ?
            ''', (summary, user, session_id))
            self.conn.commit()
        except Exception as e:
            log(f"Error ending session: {e}", "MEMORY", level="ERROR")
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            log("Memory database closed", "MEMORY")

# Global memory manager instance
_memory_manager_instance = None

def get_memory_manager():
    """Get global memory manager (singleton)"""
    global _memory_manager_instance
    if _memory_manager_instance is None:
        _memory_manager_instance = MemoryManager()
    return _memory_manager_instance

