"""
Health endpoint test for FastAPI RAG API
"""

from fastapi.testclient import TestClient
from rag_api import app


def test_health():
    """Test that the /health endpoint returns ok status"""
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

