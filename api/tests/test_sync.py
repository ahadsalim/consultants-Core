import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.settings import settings
import uuid
from datetime import datetime

client = TestClient(app)


def test_sync_import_endpoint():
    """Test sync import endpoint with valid data"""
    # Test data
    doc_id = str(uuid.uuid4())
    qa_id = str(uuid.uuid4())
    
    payload = {
        "documents": [
            {
                "id": doc_id,
                "title": "Test Law Document",
                "doc_type": "law",
                "jurisdiction": "Test Jurisdiction",
                "authority": "Test Authority",
                "source_url": "https://example.com/test-law",
                "legal_units": [
                    {
                        "unit_type": "article",
                        "num_label": "ماده ۱",
                        "heading": "Test Article",
                        "text_plain": "This is a test article content.",
                        "order_index": 1
                    }
                ]
            }
        ],
        "qa_entries": [
            {
                "id": qa_id,
                "question": "What is the test law about?",
                "answer": "The test law is about testing the system.",
                "topic_tags": ["test", "law"],
                "author": "Test Author",
                "org": "Test Organization",
                "quality_score": 0.9,
                "licensing": "allowed",
                "pii_status": "clean",
                "moderation_status": "published"
            }
        ],
        "batch_ts": datetime.utcnow().isoformat() + "Z"
    }
    
    headers = {"X-Bridge-Token": settings.BRIDGE_TOKEN}
    response = client.post("/sync/import", json=payload, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["imported"]["documents"] == 1
    assert data["imported"]["qa_entries"] == 1


def test_sync_import_unauthorized():
    """Test sync import endpoint without valid token"""
    payload = {
        "documents": [],
        "qa_entries": [],
        "batch_ts": datetime.utcnow().isoformat() + "Z"
    }
    
    # No token
    response = client.post("/sync/import", json=payload)
    assert response.status_code == 422  # Missing header
    
    # Invalid token
    headers = {"X-Bridge-Token": "invalid_token"}
    response = client.post("/sync/import", json=payload, headers=headers)
    assert response.status_code == 401
