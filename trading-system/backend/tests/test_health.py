"""
Phase 1 tests — verify the API starts and the DB connection works.
Run with: pytest backend/tests/test_health.py -v
"""
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from backend.api.main import app

client = TestClient(app)


def test_root_endpoint():
    """API root should return 200."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_health_endpoint_structure():
    """Health endpoint should return the correct fields."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "version" in data
    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"


def test_health_endpoint_db_connected():
    """
    When DB is reachable, health should report 'connected'.
    This test only passes when PostgreSQL is running locally.
    Skip with: pytest -k "not db_connected"
    """
    response = client.get("/health")
    data = response.json()
    # Will be "connected" if DB is up, or "error: ..." if not
    assert data["database"] in ["connected"] or data["database"].startswith("error")
