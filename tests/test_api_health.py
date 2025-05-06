"""Test the API health check endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.main import app


@pytest.fixture
def client():
    """Create a test client for the API."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to NeuroSpark Core API"}


def test_health_check_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert "status" in data
    assert "version" in data
    assert "uptime" in data
    assert "services" in data
    
    # Check services
    services = ["postgres", "redis", "qdrant", "elasticlite", "minio"]
    for service in services:
        assert service in data["services"]
        assert "status" in data["services"][service]
        assert "details" in data["services"][service]


def test_service_health_check_endpoint(client):
    """Test the service-specific health check endpoint."""
    services = ["postgres", "redis", "qdrant", "elasticlite", "minio"]
    
    for service in services:
        response = client.get(f"/health/{service}")
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "status" in data
        assert "details" in data


def test_service_health_check_invalid_service(client):
    """Test the service-specific health check endpoint with an invalid service."""
    response = client.get("/health/invalid_service")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_list_agents_endpoint(client):
    """Test the list agents endpoint."""
    response = client.get("/agents")
    assert response.status_code == 200
    data = response.json()
    
    # Check response structure
    assert isinstance(data, list)
    
    # Check agents
    expected_agents = [
        "curator",
        "vectoriser",
        "professor",
        "reviewer",
        "tutor",
        "auditor",
        "custodian",
        "governor",
    ]
    
    assert sorted(data) == sorted(expected_agents)
