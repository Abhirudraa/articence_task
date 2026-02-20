"""Tests for data connectors."""

import pytest
import json
from pathlib import Path
from app.connectors.crm_connector import CRMConnector
from app.connectors.support_connector import SupportConnector
from app.connectors.analytics_connector import AnalyticsConnector


@pytest.fixture
def crm_connector():
    """Fixture for CRM connector."""
    return CRMConnector()


@pytest.fixture
def support_connector():
    """Fixture for Support connector."""
    return SupportConnector()


@pytest.fixture
def analytics_connector():
    """Fixture for Analytics connector."""
    return AnalyticsConnector()


class TestCRMConnector:
    """Tests for CRM connector."""
    
    def test_fetch_returns_list(self, crm_connector):
        """Test that fetch returns a list."""
        result = crm_connector.fetch()
        assert isinstance(result, list)
    
    def test_fetch_contains_valid_fields(self, crm_connector):
        """Test that fetched data contains required fields."""
        result = crm_connector.fetch()
        if result:
            first_item = result[0]
            required_fields = ["customer_id", "name", "email", "status"]
            for field in required_fields:
                assert field in first_item
    
    def test_fetch_with_status_filter(self, crm_connector):
        """Test fetching with status filter."""
        result = crm_connector.fetch(status="active")
        if result:
            for item in result:
                assert item.get("status") == "active"
    
    def test_fetch_respects_limit(self, crm_connector):
        """Test that fetch respects limit parameter."""
        limit = 5
        result = crm_connector.fetch(limit=limit)
        assert len(result) <= limit
    
    def test_get_metadata(self, crm_connector):
        """Test metadata retrieval."""
        metadata = crm_connector.get_metadata()
        assert "name" in metadata
        assert "description" in metadata


class TestSupportConnector:
    """Tests for Support connector."""
    
    def test_fetch_returns_list(self, support_connector):
        """Test that fetch returns a list."""
        result = support_connector.fetch()
        assert isinstance(result, list)
    
    def test_fetch_contains_valid_fields(self, support_connector):
        """Test that fetched data contains required fields."""
        result = support_connector.fetch()
        if result:
            first_item = result[0]
            required_fields = ["ticket_id", "customer_id", "subject", "priority", "status"]
            for field in required_fields:
                assert field in first_item
    
    def test_get_open_tickets(self, support_connector):
        """Test getting open tickets."""
        result = support_connector.get_open_tickets()
        if result:
            for item in result:
                assert item.get("status") == "open"
    
    def test_get_high_priority_tickets(self, support_connector):
        """Test getting high priority tickets."""
        result = support_connector.get_high_priority_tickets()
        if result:
            for item in result:
                assert item.get("priority") == "high"


class TestAnalyticsConnector:
    """Tests for Analytics connector."""
    
    def test_fetch_returns_list(self, analytics_connector):
        """Test that fetch returns a list."""
        result = analytics_connector.fetch()
        assert isinstance(result, list)
    
    def test_fetch_contains_valid_fields(self, analytics_connector):
        """Test that fetched data contains required fields."""
        result = analytics_connector.fetch()
        if result:
            first_item = result[0]
            required_fields = ["metric", "date", "value"]
            for field in required_fields:
                assert field in first_item
    
    def test_get_daily_active_users(self, analytics_connector):
        """Test getting DAU metric."""
        result = analytics_connector.get_daily_active_users()
        if result:
            for item in result:
                assert item.get("metric") == "daily_active_users"
    
    def test_summarize_metrics(self, analytics_connector):
        """Test metrics summary."""
        result = analytics_connector.summarize_metrics()
        assert isinstance(result, dict)
