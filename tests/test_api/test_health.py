"""
Tests for health check endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


def test_health_check_sync(client: TestClient):
    """Test synchronous health check endpoint."""
    response = client.get("/healthz")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
    assert "database" in data
    assert "environment" in data


@pytest.mark.asyncio
async def test_health_check_async(async_client: AsyncClient):
    """Test asynchronous health check endpoint."""
    response = await async_client.get("/healthz")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] in ["healthy", "unhealthy"]
    assert data["version"] == "0.1.0"


def test_root_endpoint(client: TestClient):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Welcome to Indian Palmistry AI Backend"
    assert data["version"] == "0.1.0"
    assert data["health_check"] == "/healthz"


def test_api_v1_health(client: TestClient):
    """Test API v1 health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["api_version"] == "v1"
    assert "timestamp" in data


def test_not_found_handler(client: TestClient):
    """Test 404 error handler."""
    response = client.get("/nonexistent")
    assert response.status_code == 404
    
    data = response.json()
    assert data["detail"] == "Not found"
    assert data["path"] == "/nonexistent"
    assert data["method"] == "GET"