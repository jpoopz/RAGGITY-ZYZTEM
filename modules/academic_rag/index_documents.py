"""
Academic RAG Document Indexer
Uses core RAGEngine for unified document ingestion
"""

import os
import sys

# Force UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Add parent directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from logger import get_logger
from core.rag_engine import RAGEngine
from core.paths import ensure_dirs
from core.config_manager import get_module_config

log = get_logger("academic_rag_index")


def index_documents():
    """
    Index documents from Obsidian vault using core RAG engine
    """
    try:
        # Get configuration
        module_config = get_module_config("academic_rag")
        vault_path = module_config.get("vault_path", 
                                      os.path.expanduser(r"C:\Users\Julian Poopat\Documents\Obsidian"))
        notes_path = os.path.join(vault_path, module_config.get("notes_path", "Notes"))
        
        if not os.path.exists(notes_path):
            log.error(f"Notes path does not exist: {notes_path}")
            return False
        
        log.info("=" * 60)
        log.info("Academic RAG Document Indexer")
        log.info("=" * 60)
        log.info(f"Vault path: {vault_path}")
        log.info(f"Notes path: {notes_path}")
        
        # Ensure directories exist
        ensure_dirs()
        
        # Initialize RAG engine
        log.info("Initializing RAG engine...")
        rag = RAGEngine()
        
        # Load existing index first
        rag.build_or_load_index()
        
        # Ingest documents from notes path
        log.info(f"Scanning for documents in: {notes_path}")
        rag.ingest_path(notes_path)
        
        log.info("=" * 60)
        log.info("Indexing process completed successfully")
        log.info("=" * 60)
        
        return True
        
    except Exception as e:
        log.error(f"Indexing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        success = index_documents()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        log.info("Indexing interrupted by user")
        sys.exit(130)
    except Exception as e:
        log.error(f"Fatal error: {e}")
        sys.exit(1)
