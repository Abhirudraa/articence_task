"""Tests for business rules."""

import pytest
from app.services.business_rules import business_rules
from app.models.common import DataTypeEnum


class TestBusinessRules:
    """Tests for business rules engine."""
    
    @pytest.fixture
    def sample_data(self):
        """Sample data for testing."""
        return [
            {"customer_id": 1, "name": "Customer 1", "status": "active"},
            {"customer_id": 2, "name": "Customer 2", "status": "inactive"},
            {"customer_id": 3, "name": "Customer 3", "status": "active"},
        ]
    
    def test_apply_voice_limits(self, sample_data):
        """Test voice limit application."""
        result = business_rules.apply_voice_limits(sample_data, limit=2)
        assert len(result) == 2
    
    def test_filter_by_status(self, sample_data):
        """Test status filtering."""
        result = business_rules.filter_by_status(sample_data, "active")
        assert len(result) == 2
        for item in result:
            assert item["status"] == "active"
    
    def test_apply_pagination(self, sample_data):
        """Test pagination."""
        result, total, returned = business_rules.apply_pagination(sample_data, limit=2, offset=1)
        assert len(result) == 2
        assert total == 3
        assert returned == 2
    
    def test_build_context_message(self):
        """Test context message building."""
        message = business_rules.build_context_message(10, 5, "customer")
        assert "5 of 10" in message
        assert "customer" in message
    
    def test_should_summarize(self, sample_data):
        """Test summarization decision."""
        # Small dataset
        should_summarize = business_rules.should_summarize(sample_data, threshold=10)
        assert should_summarize is False
        
        # Large dataset
        large_data = sample_data * 5
        should_summarize = business_rules.should_summarize(large_data, threshold=10)
        assert should_summarize is True
