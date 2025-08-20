import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_stats_endpoint():
    """Test stats endpoint"""
    response = client.get("/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert "official_documents" in data
    assert "qa_entries" in data
    
    # Check official documents structure
    official_docs = data["official_documents"]
    assert "total" in official_docs
    assert "by_status" in official_docs
    assert "by_type" in official_docs
    assert isinstance(official_docs["total"], int)
    
    # Check Q&A entries structure
    qa_entries = data["qa_entries"]
    assert "total" in qa_entries
    assert isinstance(qa_entries["total"], int)
