"""
RAG engine smoke test - basic ingestion and query
"""

from core.rag_engine import RAGEngine


def test_ingest_and_query(tmp_path):
    """Test basic document ingestion and querying"""
    # Create a sample text file
    p = tmp_path / "sample.txt"
    p.write_text("St Andrews is in Fife, Scotland. The University is historic.")
    
    # Initialize RAG engine with temporary directory
    eng = RAGEngine(store_dir=str(tmp_path / "vec"))
    
    # Ingest the document
    eng.ingest_path(str(p))
    
    # Query the system
    out = eng.query("Where is St Andrews?")
    
    # Verify Scotland appears in answer or contexts
    assert "Scotland" in out["answer"] or any("Scotland" in ctx for ctx in out["contexts"])

