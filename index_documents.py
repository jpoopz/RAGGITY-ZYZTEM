"""
Local Document Indexer for Obsidian RAG System
Indexes all Markdown, PDF, and DOCX files from Notes directory
Stores embeddings in ChromaDB with metadata for citations
"""

import os
import re
import sys
import chromadb
from pathlib import Path
from PyPDF2 import PdfReader
from docx import Document
from tqdm import tqdm
import hashlib

# Force UTF-8 encoding for console output (prevents UnicodeEncodeError)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# Import unified logger
try:
    from logger import log, log_exception
except ImportError:
    def log(msg, category="INDEX", print_to_console=True):
        print(f"[{category}] {msg}")
    def log_exception(category="ERROR", exception=None, context=""):
        import traceback
        print(f"[{category}] {context}: {exception}", file=sys.stderr)
        traceback.print_exc()

# Import semantic tagging
try:
    from semantic_tagging import tag_document
    TAGGING_AVAILABLE = True
except ImportError:
    TAGGING_AVAILABLE = False
    log("semantic_tagging module not available, tagging disabled", "INDEX")

# Configuration
VAULT_PATH = os.path.expanduser(r"C:\Users\Julian Poopat\Documents\Obsidian")
NOTES_PATH = os.path.join(VAULT_PATH, "Notes")
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Initialize ChromaDB - store in RAG_System folder relative to script location
RAG_SYSTEM_PATH = os.path.dirname(os.path.abspath(__file__))
CHROMADB_PATH = os.path.join(RAG_SYSTEM_PATH, ".chromadb")
client = chromadb.PersistentClient(path=CHROMADB_PATH)
collection = client.get_or_create_collection(
    name="obsidian_docs",
    metadata={"description": "Indexed Obsidian notes and documents"}
)

# Use Ollama embeddings or fallback to default
try:
    from chromadb.utils import embedding_functions
    # Try Ollama embedding function (if available)
    try:
        embedder = embedding_functions.OllamaEmbeddingFunction(
            model_name="nomic-embed-text"
        )
        log("Using Ollama embeddings (nomic-embed-text)", "INDEX")
    except Exception as e:
        # Fallback to default sentence transformer
        embedder = embedding_functions.DefaultEmbeddingFunction()
        log(f"Using default embeddings (Ollama embedding not available): {str(e)}", "INDEX")
except Exception as e:
    log(f"Using default embeddings: {str(e)}", "INDEX")
    embedder = None

def extract_text(file_path):
    """Extract text from various file formats"""
    try:
        if file_path.endswith((".md", ".txt")):
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()
        elif file_path.endswith(".pdf"):
            pdf = PdfReader(file_path)
            text = "\n".join([
                page.extract_text() for page in pdf.pages 
                if page.extract_text()
            ])
            return text
        elif file_path.endswith(".docx"):
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs])
        return ""
    except Exception as e:
        log_exception("INDEX", e, f"Error reading file: {file_path}")
        return ""

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break
    return chunks

def get_line_range(text, chunk):
    """Estimate line range for a chunk within full text"""
    start_idx = text.find(chunk[:100])
    if start_idx == -1:
        return (0, 0)
    
    start_line = text[:start_idx].count('\n') + 1
    end_idx = start_idx + len(chunk)
    end_line = text[:end_idx].count('\n') + 1
    
    return (start_line, end_line)

def index_documents():
    """Main indexing function"""
    log("Scanning for documents...", "INDEX")
    
    # Find all documents
    documents = []
    for root, dirs, files in os.walk(NOTES_PATH):
        # Skip hidden and system folders
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        
        for file in files:
            if file.endswith((".md", ".pdf", ".docx", ".txt")):
                full_path = os.path.join(root, file)
                documents.append(full_path)
    
    log(f"Found {len(documents)} documents to index", "INDEX")
    
    # Clear existing collection
    log("Clearing existing index...", "INDEX")
    try:
        client.delete_collection("obsidian_docs")
        collection = client.create_collection(
            name="obsidian_docs",
            embedding_function=embedder
        )
    except:
        collection = client.get_or_create_collection(
            name="obsidian_docs",
            embedding_function=embedder
        )
    
    # Index documents
    all_chunks = []
    all_metadata = []
    all_ids = []
    
    for doc_path in tqdm(documents, desc="Indexing"):
        relative_path = os.path.relpath(doc_path, VAULT_PATH)
        filename = os.path.basename(doc_path)
        
        text = extract_text(doc_path)
        if not text.strip():
            continue
        
        # Tag document if tagging is available
        doc_tags = []
        if TAGGING_AVAILABLE:
            try:
                _, doc_tags = tag_document(doc_path, text)
                log(f"Tagged: {filename} -> {', '.join(doc_tags)}", "INDEX")
            except Exception as e:
                log(f"Warning: Tagging failed for {filename}: {e}", "INDEX")
        
        chunks = chunk_text(text)
        full_text = text  # Keep for line range calculation
        
        for i, chunk in enumerate(chunks):
            # Calculate line range
            line_range = get_line_range(full_text, chunk)
            
            # Create unique ID
            chunk_id = hashlib.md5(f"{relative_path}_{i}".encode()).hexdigest()
            
            # Metadata with citation info
            metadata = {
                "source": filename,
                "source_path": relative_path,
                "chunk_index": str(i),
                "total_chunks": str(len(chunks)),
                "line_start": str(line_range[0]),
                "line_end": str(line_range[1]),
                "file_type": Path(doc_path).suffix[1:].lower()
            }
            
            # Add tags to metadata if available
            if doc_tags:
                metadata["tags"] = ", ".join(doc_tags)
            
            all_chunks.append(chunk)
            all_metadata.append(metadata)
            all_ids.append(chunk_id)
    
    # Batch add to ChromaDB
    log(f"Storing {len(all_chunks)} chunks in vector database...", "INDEX")
    batch_size = 100
    for i in tqdm(range(0, len(all_chunks), batch_size), desc="Storing"):
        batch_chunks = all_chunks[i:i+batch_size]
        batch_metadata = all_metadata[i:i+batch_size]
        batch_ids = all_ids[i:i+batch_size]
        
        collection.add(
            documents=batch_chunks,
            metadatas=batch_metadata,
            ids=batch_ids
        )
    
    log(f"Indexing complete: {len(all_chunks)} chunks from {len(documents)} documents", "INDEX")
    log(f"Database location: {CHROMADB_PATH}", "INDEX")

if __name__ == "__main__":
    try:
        log("=" * 60, "INDEX")
        log("Obsidian RAG Document Indexer", "INDEX")
        log("=" * 60, "INDEX")
        index_documents()
        log("Indexing process completed successfully", "INDEX")
    except Exception as e:
        log_exception("INDEX", e, "Indexing failed")
        sys.exit(1)

