import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.settings import settings
import uuid
from datetime import datetime

# Test database URL (use in-memory SQLite for testing)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_database():
    """Create test database tables"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.mark.integration
def test_complete_workflow(setup_database):
    """Test complete workflow: sync import -> stats -> health"""
    
    # Step 1: Import test data via sync endpoint
    doc_id = str(uuid.uuid4())
    qa_id = str(uuid.uuid4())
    
    sync_payload = {
        "documents": [
            {
                "id": doc_id,
                "title": "Integration Test Law",
                "doc_type": "law",
                "jurisdiction": "Test Jurisdiction",
                "authority": "Test Authority",
                "source_url": "https://example.com/test-law",
                "legal_units": [
                    {
                        "unit_type": "article",
                        "num_label": "ماده ۱",
                        "heading": "Test Article",
                        "text_plain": "This is a test article for integration testing.",
                        "order_index": 1
                    },
                    {
                        "unit_type": "paragraph",
                        "num_label": "بند الف",
                        "heading": "Test Paragraph",
                        "text_plain": "This is a test paragraph under the article.",
                        "order_index": 2
                    }
                ]
            }
        ],
        "qa_entries": [
            {
                "id": qa_id,
                "question": "What is the integration test law about?",
                "answer": "The integration test law is designed to test the complete system workflow.",
                "topic_tags": ["integration", "testing", "law"],
                "author": "Test Author",
                "org": "Test Organization",
                "quality_score": 0.95,
                "licensing": "allowed",
                "pii_status": "clean",
                "moderation_status": "published"
            }
        ],
        "batch_ts": datetime.utcnow().isoformat() + "Z"
    }
    
    # Import data
    headers = {"X-Bridge-Token": settings.BRIDGE_TOKEN}
    sync_response = client.post("/sync/import", json=sync_payload, headers=headers)
    
    assert sync_response.status_code == 200
    sync_data = sync_response.json()
    assert sync_data["status"] == "success"
    assert sync_data["imported"]["documents"] == 1
    assert sync_data["imported"]["qa_entries"] == 1
    
    # Step 2: Check stats endpoint reflects imported data
    stats_response = client.get("/stats")
    assert stats_response.status_code == 200
    
    stats_data = stats_response.json()
    assert stats_data["official_documents"]["total"] >= 1
    assert stats_data["qa_entries"]["total"] >= 1
    
    # Check document breakdown
    assert "by_status" in stats_data["official_documents"]
    assert "by_type" in stats_data["official_documents"]
    assert stats_data["official_documents"]["by_status"]["published"] >= 1
    assert stats_data["official_documents"]["by_type"]["law"] >= 1
    
    # Step 3: Verify health endpoint
    health_response = client.get("/health")
    assert health_response.status_code == 200
    
    health_data = health_response.json()
    assert health_data["status"] in ["ok", "degraded"]
    assert "db" in health_data
    assert "env" in health_data
    
    # Step 4: Test duplicate import (upsert functionality)
    # Import the same data again to test upsert
    sync_response_2 = client.post("/sync/import", json=sync_payload, headers=headers)
    assert sync_response_2.status_code == 200
    
    # Stats should remain the same (upsert, not duplicate)
    stats_response_2 = client.get("/stats")
    stats_data_2 = stats_response_2.json()
    assert stats_data_2["official_documents"]["total"] == stats_data["official_documents"]["total"]
    assert stats_data_2["qa_entries"]["total"] == stats_data["qa_entries"]["total"]


@pytest.mark.integration
def test_error_handling(setup_database):
    """Test error handling scenarios"""
    
    # Test invalid bridge token
    invalid_payload = {
        "documents": [],
        "qa_entries": [],
        "batch_ts": datetime.utcnow().isoformat() + "Z"
    }
    
    # No token
    response = client.post("/sync/import", json=invalid_payload)
    assert response.status_code == 422
    
    # Invalid token
    headers = {"X-Bridge-Token": "invalid_token"}
    response = client.post("/sync/import", json=invalid_payload, headers=headers)
    assert response.status_code == 401
    
    # Test malformed data
    malformed_payload = {
        "documents": [
            {
                "id": "not-a-uuid",  # Invalid UUID
                "title": "Test",
                "doc_type": "invalid_type"  # Invalid enum value
            }
        ],
        "qa_entries": [],
        "batch_ts": "invalid-timestamp"  # Invalid timestamp
    }
    
    valid_headers = {"X-Bridge-Token": settings.BRIDGE_TOKEN}
    response = client.post("/sync/import", json=malformed_payload, headers=valid_headers)
    assert response.status_code == 422  # Validation error


@pytest.mark.integration
def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "environment" in data
    assert settings.PROJECT_NAME in data["message"]
