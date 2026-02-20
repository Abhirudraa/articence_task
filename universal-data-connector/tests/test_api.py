"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Fixture for test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_health_check(self, client):
        """Test basic health check."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_readiness_check(self, client):
        """Test readiness check endpoint."""
        response = client.get("/health/readiness")
        assert response.status_code == 200
        assert response.json()["ready"] is True
    
    def test_liveness_check(self, client):
        """Test liveness check endpoint."""
        response = client.get("/health/liveness")
        assert response.status_code == 200
        assert response.json()["alive"] is True


class TestDataEndpoints:
    """Tests for data endpoints."""
    
    def test_get_customers(self, client):
        """Test get customers endpoint."""
        response = client.get("/data/customers")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "metadata" in data
        assert "total_results" in data["metadata"]
        assert "returned_results" in data["metadata"]
    
    def test_get_customers_with_status_filter(self, client):
        """Test get customers with status filter."""
        response = client.get("/data/customers?status=active")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    
    def test_get_customers_with_limit(self, client):
        """Test get customers with limit parameter."""
        response = client.get("/data/customers?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 5
    
    def test_get_support_tickets(self, client):
        """Test get support tickets endpoint."""
        response = client.get("/data/support-tickets")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "metadata" in data
    
    def test_get_analytics(self, client):
        """Test get analytics endpoint."""
        response = client.get("/data/analytics")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "metadata" in data
    
    def test_get_data_generic_endpoint(self, client):
        """Test generic data endpoint."""
        response = client.get("/data/customers")
        assert response.status_code == 200
        
        response = client.get("/data/support-tickets")
        assert response.status_code == 200
        
        response = client.get("/data/analytics")
        assert response.status_code == 200


class TestConnectorInfo:
    """Tests for connector information endpoints."""
    
    def test_get_connectors_info(self, client):
        """Test getting connector information."""
        response = client.get("/data/connectors/info")
        assert response.status_code == 200
        data = response.json()
        assert "customers" in data
        assert "support_tickets" in data
        assert "analytics" in data


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "version" in data
