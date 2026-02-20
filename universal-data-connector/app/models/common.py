from pydantic import BaseModel, Field
from typing import Any, List, Dict, Optional, Literal
from datetime import datetime
from enum import Enum


class DataTypeEnum(str, Enum):
    """Enum for different data types."""
    TABULAR = "tabular"
    TIME_SERIES = "time_series"
    HIERARCHICAL = "hierarchical"
    EMPTY = "empty"
    UNKNOWN = "unknown"


class Metadata(BaseModel):
    """Metadata about the returned data."""
    total_results: int = Field(..., description="Total number of results available")
    returned_results: int = Field(..., description="Number of results returned in this response")
    data_type: DataTypeEnum = Field(..., description="Type of data returned")
    data_freshness: str = Field(..., description="Timestamp and freshness info of the data")
    context: str = Field(..., description="Human-readable context about the data")
    has_more: bool = Field(..., description="Whether more results are available")


class DataResponse(BaseModel):
    """Standard response format for all data endpoints."""
    data: List[Any] = Field(..., description="The actual data items")
    metadata: Metadata = Field(..., description="Metadata about the response")


# CRM Models
class Customer(BaseModel):
    """Customer data model."""
    customer_id: int
    name: str
    email: str
    created_at: str
    status: Literal["active", "inactive"]


class CRMResponse(BaseModel):
    """Response for CRM data."""
    data: List[Customer]
    metadata: Metadata


# Support Ticket Models
class SupportTicket(BaseModel):
    """Support ticket data model."""
    ticket_id: int
    customer_id: int
    subject: str
    priority: Literal["low", "medium", "high"]
    created_at: str
    status: Literal["open", "closed"]


class SupportResponse(BaseModel):
    """Response for support ticket data."""
    data: List[SupportTicket]
    metadata: Metadata


# Analytics Models
class AnalyticsMetric(BaseModel):
    """Analytics metric data model."""
    metric: str
    date: str
    value: float


class AnalyticsResponse(BaseModel):
    """Response for analytics data."""
    data: List[AnalyticsMetric]
    metadata: Metadata


# Query Parameters Models
class PaginationParams(BaseModel):
    """Pagination parameters."""
    limit: int = Field(10, ge=1, le=100, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class FilterParams(BaseModel):
    """Filter parameters."""
    status: Optional[str] = Field(None, description="Filter by status")
    priority: Optional[str] = Field(None, description="Filter by priority")
    date_from: Optional[str] = Field(None, description="Filter from date")
    date_to: Optional[str] = Field(None, description="Filter to date")


# Query Models
class QueryRequest(BaseModel):
    """Request for natural language query processing."""
    query: str = Field(..., description="Natural language query")
    use_llm_if_needed: bool = Field(True, description="Allow LLM fallback for complex queries")
    max_tokens: Optional[int] = Field(None, description="Max tokens for LLM response")


class QueryAnalysis(BaseModel):
    """Analysis of a query."""
    query: str
    query_type: str
    complexity: str
    confidence: float
    parameters: Dict[str, str] = Field(default_factory=dict)
    limit: int


class QueryResponse(BaseModel):
    """Response from query processing."""
    status: str = Field(..., description="success, error, or fallback_to_llm")
    query: str
    query_type: str
    complexity: str
    message: str
    response_type: str
    used_llm: bool
    data: List[Any] = Field(default_factory=list)
    count: int = 0
    confidence: float
    metadata: Dict[str, Any] = Field(default_factory=dict)
    fallback: Optional[Dict[str, Any]] = None
    instructions: Optional[Dict[str, Any]] = None


# ==================== AUTHENTICATION MODELS ====================

class APIKeyResponse(BaseModel):
    """Response with generated API key."""
    api_key: str = Field(..., description="Generated API key")
    name: str = Field(..., description="API key name")
    created_at: str = Field(..., description="Creation timestamp")
    rate_limit: Optional[str] = Field("unlimited", description="Rate limit")


class APIKeyInfo(BaseModel):
    """Information about an API key."""
    key_preview: Optional[str] = Field(None, description="Preview of API key (first 10 chars)")
    name: str
    created_at: Optional[str] = None
    last_used: Optional[str] = None
    active: bool = True
    rate_limit: Optional[int] = 1000


# ==================== WEBHOOK MODELS ====================

class WebhookPayload(BaseModel):
    """Payload for triggering a webhook."""
    event_type: str = Field(..., description="Type of event")
    data: Dict[str, Any] = Field(..., description="Event data")
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Event timestamp")


class WebhookRequest(BaseModel):
    """Request to register a webhook."""
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to subscribe to")
    name: Optional[str] = Field(None, description="Webhook name")


class WebhookResponse(BaseModel):
    """Response with webhook information."""
    webhook_id: str = Field(..., description="Webhook ID")  # Note: changed from 'id' to 'webhook_id' for clarity
    url: str
    events: List[str]
    name: Optional[str] = None
    created_at: str
    status: str = Field("active", description="Webhook status")  # Added status field
    active: bool = True  # Keep for backward compatibility
    delivery_count: Optional[int] = 0
    last_delivery: Optional[str] = None
    success_count: Optional[int] = 0
    failure_count: Optional[int] = 0


# ==================== EXPORT MODELS ====================

class ExportRequest(BaseModel):
    """Request to export data."""
    format: Literal["csv", "excel", "json"] = Field(..., description="Export format")
    filename: Optional[str] = Field(None, description="Output filename")
    limit: Optional[int] = Field(1000, description="Maximum number of records to export")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters to apply")


class ExportResponse(BaseModel):
    """Response from export."""
    status: str = Field(..., description="Export status")
    format: str
    records_count: int
    exported_at: str
    download_url: Optional[str] = Field(None, description="URL to download exported file")
    expires_at: Optional[str] = Field(None, description="Expiration timestamp")


# ==================== RATE LIMIT MODELS ====================

class RateLimitInfo(BaseModel):
    """Rate limit information."""
    limited: bool = Field(..., description="Whether request is rate limited")
    limit: int = Field(..., description="Rate limit")
    remaining: int = Field(..., description="Remaining requests")
    reset: int = Field(..., description="Reset timestamp (Unix time)")


# ==================== CACHE MODELS ====================

class CacheStats(BaseModel):
    """Cache statistics."""
    enabled: bool = Field(..., description="Whether cache is enabled")
    redis_connected: Optional[bool] = Field(None, description="Redis connection status")
    fallback_cache_size: int = Field(0, description="Fallback cache size")
    ttl: int = Field(..., description="Cache TTL in seconds")
    redis: Optional[Dict[str, Any]] = Field(None, description="Redis stats")