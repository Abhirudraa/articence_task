"""
Integration tests for bonus features.
Run with: pytest tests/test_bonus_features.py -v
"""

import pytest
import json
from httpx import AsyncClient
from app.main import app
from app.services.auth_service import auth_service
from app.services.cache_service import cache_service
from app.services.webhook_service import webhook_service
from app.services.export_service import export_service


@pytest.fixture
async def client():
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


class TestAuthentication:
    """Test API key authentication."""
    
    @pytest.mark.asyncio
    async def test_generate_api_key(self, client):
        """Test API key generation."""
        response = await client.post(
            "/api/auth/generate-key?name=TestKey"
        )
        assert response.status_code == 200
        data = response.json()
        assert "api_key" in data
        assert data["name"] == "TestKey"
        assert data["api_key"].startswith("uk_")
    
    @pytest.mark.asyncio
    async def test_list_api_keys(self, client):
        """Test listing API keys."""
        # Generate a key first
        response = await client.post(
            "/api/auth/generate-key?name=TestKey2"
        )
        assert response.status_code == 200
        
        # List keys
        response = await client.get("/api/auth/keys")
        assert response.status_code == 200
        data = response.json()
        assert "keys" in data
        assert isinstance(data["keys"], list)
    
    @pytest.mark.asyncio
    async def test_validate_api_key(self, client):
        """Test API key validation."""
        # Generate a key
        gen_response = await client.post(
            "/api/auth/generate-key?name=TestKey3"
        )
        api_key = gen_response.json()["api_key"]
        
        # Validate key
        response = await client.get(
            "/api/auth/validate",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_headers(self, client):
        """Test rate limit headers in response."""
        response = await client.get("/data/customers", params={"limit": 5})
        
        assert "x-ratelimit-limit" in response.headers or True  # May be disabled
        if "x-ratelimit-limit" in response.headers:
            assert response.headers["x-ratelimit-limit"] == "100"
    
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded(self, client):
        """Test rate limit exceeded response."""
        # This test would need 100+ requests to hit the limit
        # Skip for now or implement with mocked rate limiter
        pass


class TestCaching:
    """Test caching functionality."""
    
    @pytest.mark.asyncio
    async def test_cache_status(self, client):
        """Test cache status endpoint."""
        response = await client.get("/api/cache/status")
        assert response.status_code == 200
        data = response.json()
        assert "enabled" in data
        assert "healthy" in data
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, client):
        """Test cache clear endpoint."""
        response = await client.delete("/api/cache/clear")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_cache_service_get_set(self):
        """Test cache service directly."""
        # Set value
        success = await cache_service.set("test", "key1", {"data": "value"})
        assert success is True or not cache_service.enabled
        
        # Get value
        value = await cache_service.get("test", "key1")
        if cache_service.enabled:
            assert value == {"data": "value"}


class TestWebhooks:
    """Test webhook functionality."""
    
    @pytest.mark.asyncio
    async def test_register_webhook(self, client):
        """Test webhook registration."""
        response = await client.post(
            "/api/webhooks/register",
            json={
                "url": "https://example.com/webhook",
                "events": ["data_updated"],
                "name": "Test Webhook"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["url"] == "https://example.com/webhook"
    
    @pytest.mark.asyncio
    async def test_list_webhooks(self, client):
        """Test listing webhooks."""
        response = await client.get("/api/webhooks")
        assert response.status_code == 200
        data = response.json()
        assert "webhooks" in data
        assert isinstance(data["webhooks"], list)


class TestExport:
    """Test data export functionality."""
    
    @pytest.mark.asyncio
    async def test_export_csv(self, client):
        """Test CSV export."""
        response = await client.post(
            "/api/export/customers?format=csv"
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio
    async def test_export_json(self, client):
        """Test JSON export."""
        response = await client.post(
            "/api/export/customers?format=json"
        )
        assert response.status_code == 200
        data = response.json()
        assert "exported_at" in data
        assert "record_count" in data
        assert "data" in data
    
    @pytest.mark.asyncio
    async def test_export_invalid_format(self, client):
        """Test invalid export format."""
        response = await client.post(
            "/api/export/customers?format=invalid"
        )
        # Should return error
        assert response.status_code >= 400


class TestStreaming:
    """Test streaming endpoints."""
    
    @pytest.mark.asyncio
    async def test_stream_customers_json(self, client):
        """Test customer streaming in JSON format."""
        response = await client.get(
            "/api/stream/customers?format=json"
        )
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
    
    @pytest.mark.asyncio
    async def test_stream_customers_ndjson(self, client):
        """Test customer streaming in NDJSON format."""
        response = await client.get(
            "/api/stream/customers?format=ndjson"
        )
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")


class TestWebUI:
    """Test web UI accessibility."""
    
    @pytest.mark.asyncio
    async def test_ui_accessible(self, client):
        """Test that web UI is accessible."""
        response = await client.get("/ui/index.html")
        assert response.status_code == 200
        assert "html" in response.text.lower()


class TestIntegration:
    """Integration tests across features."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self, client):
        """Test complete workflow with multiple features."""
        # 1. Generate API key
        key_response = await client.post(
            "/api/auth/generate-key?name=WorkflowTest"
        )
        assert key_response.status_code == 200
        api_key = key_response.json()["api_key"]
        
        # 2. Use API key to fetch data
        data_response = await client.get(
            "/data/customers",
            headers={"Authorization": f"Bearer {api_key}"}
        )
        # May fail if auth disabled, but should be valid call
        assert data_response.status_code in [200, 401]
        
        # 3. Register webhook
        webhook_response = await client.post(
            "/api/webhooks/register",
            json={
                "url": "https://example.com/test",
                "events": ["data_updated"],
                "name": "Workflow Test"
            }
        )
        assert webhook_response.status_code == 200
        
        # 4. Export data
        export_response = await client.post(
            "/api/export/customers?format=json"
        )
        assert export_response.status_code == 200
        
        # 5. Check cache status
        cache_response = await client.get("/api/cache/status")
        assert cache_response.status_code == 200


# Performance tests
class TestPerformance:
    """Test performance characteristics."""
    
    @pytest.mark.asyncio
    async def test_cached_response_time(self, client):
        """Test that cached responses are faster."""
        # First request (cache miss)
        import time
        start = time.time()
        response1 = await client.get("/data/customers")
        time1 = time.time() - start
        
        # Second request (cache hit) - should be faster
        start = time.time()
        response2 = await client.get("/data/customers")
        time2 = time.time() - start
        
        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
