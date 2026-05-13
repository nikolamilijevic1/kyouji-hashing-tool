import pytest
from fastapi.testclient import TestClient
from backend.main import app  # Adjust if your entry file is backend/app.py

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200

def test_hash_endpoint():
    payload = {"data": "data to verify"}
    response = client.post("/hash", json=payload)
    assert response.status_code == 200
    assert "hash" in response.json()
