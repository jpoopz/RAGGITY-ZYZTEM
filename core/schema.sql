-- SQLite Schema for Julian Assistant Suite Memory System
-- Version: 3.5.0

-- Facts table: User preferences, learned information, key-value pairs
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
);

-- Logs table: System logs for summarization
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    message TEXT NOT NULL,
    level TEXT DEFAULT 'INFO',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table: Session tracking and analytics
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    session_id TEXT NOT NULL,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    summary TEXT,
    facts_learned INTEGER DEFAULT 0,
    UNIQUE(user, session_id)
);

-- Log summaries table: Periodic summaries
CREATE TABLE IF NOT EXISTS log_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    period_start DATETIME NOT NULL,
    period_end DATETIME NOT NULL,
    summary_text TEXT,
    key_insights TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Context cache: Cached context bundles for quick retrieval
CREATE TABLE IF NOT EXISTS context_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user TEXT NOT NULL,
    query_hash TEXT,
    context_json TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_facts_user_updated ON facts(user, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_facts_category ON facts(category);
CREATE INDEX IF NOT EXISTS idx_logs_category_time ON logs(category, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_context_cache_user ON context_cache(user, expires_at);




