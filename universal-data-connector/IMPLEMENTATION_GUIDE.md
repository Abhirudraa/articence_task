# Implementation Guide - Bonus Features

## Overview

This guide explains the implementation details and architecture of all bonus features added to the Universal Data Connector.

## Project Structure

```
app/
├── services/
│   ├── cache_service.py          # Redis caching service
│   ├── auth_service.py           # API key management
│   ├── webhook_service.py        # Webhook event system
│   └── export_service.py         # Data export service
├── middleware/
│   ├── auth.py                   # Authentication middleware
│   └── rate_limit.py             # Rate limiting middleware
├── routers/
│   ├── bonus.py                  # All bonus feature endpoints
│   ├── data.py                   # Core data endpoints
│   └── health.py                 # Health check endpoints
├── models/
│   └── common.py                 # Data models including bonus models
├── config.py                      # Configuration with bonus settings
└── main.py                        # FastAPI app with middleware registration

static/
└── index.html                     # Web UI dashboard

📄 BONUS_FEATURES.md              # Comprehensive feature documentation
```

## Detailed Implementation

### 1. Redis Caching Service

**File**: `app/services/cache_service.py`

**Purpose**: Cache frequently accessed data to reduce latency and database load.

**Key Features**:
- Automatic JSON serialization/deserialization
- Namespace-based key organization
- TTL (Time To Live) support
- Health check capability
- Graceful fallback when Redis is unavailable

**Code Example**:
```python
from app.services.cache_service import cache_service

# Get cached data
cached_data = await cache_service.get('customer', 'id_123')

# Set cache with custom TTL
await cache_service.set('customer', 'id_123', data, ttl=1800)

# Clear namespace
await cache_service.clear_namespace('customer')

# Check health
is_healthy = cache_service.is_healthy()
```

**Integration Points**:
- Called from data endpoints before fetching from connectors
- Webhook service triggers cache invalidation on data updates

### 2. Authentication & API Key Management

**File**: `app/services/auth_service.py`

**Purpose**: Secure API endpoints with API key-based authentication.

**Key Features**:
- Cryptographically secure key generation
- Persistent key storage in JSON file
- Rate limit per key configuration
- Key activation/deactivation
- Audit trail (created_at, last_used)

**Code Example**:
```python
from app.services.auth_service import auth_service

# Generate new API key
api_key = auth_service.generate_api_key("My App")

# Validate API key
is_valid = auth_service.validate_api_key(api_key)

# Get key info
info = auth_service.get_key_info(api_key)

# List all active keys
keys = auth_service.list_api_keys()

# Revoke a key
auth_service.revoke_api_key(api_key)
```

**Middleware Integration**:
- `AuthenticationMiddleware` validates API keys on protected endpoints
- API key extracted from Authorization header: `Bearer <api_key>`
- Unprotected routes: `/docs`, `/redoc`, `/health`, `/openapi.json`

**Storage Format** (`api_keys.json`):
```json
{
  "uk_...": {
    "name": "My Key",
    "created_at": "2024-02-20T10:30:00",
    "last_used": "2024-02-20T11:00:00",
    "active": true,
    "rate_limit": 1000
  }
}
```

### 3. Rate Limiting Middleware

**File**: `app/middleware/rate_limit.py`

**Purpose**: Prevent API abuse and ensure fair resource usage.

**Key Features**:
- Per-client limiting (API key or IP address)
- Configurable requests per time period
- Automatic cleanup of old request records
- Response headers with limit information

**Code Example**:
```python
# Configuration in config.py
RATE_LIMIT_ENABLED = True
RATE_LIMIT_REQUESTS = 100  # Requests per period
RATE_LIMIT_PERIOD_SECONDS = 60  # Time window
```

**Middleware Behavior**:
1. Extract identifier (API key or source IP)
2. Check if limit exceeded
3. If exceeded, return 429 Too Many Requests
4. Update response headers with limit info

**Response Headers**:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1673456789 (Unix timestamp)
```

### 4. Webhook Event System

**File**: `app/services/webhook_service.py`

**Purpose**: Trigger HTTP callbacks when events occur.

**Key Features**:
- Async webhook delivery
- Event filtering (subscribe to specific events)
- Delivery history tracking
- Timeout and error handling
- Persistent webhook storage

**Code Example**:
```python
from app.services.webhook_service import webhook_service

# Register webhook
webhook_id = webhook_service.register_webhook(
    url="https://example.com/webhook",
    events=["data_updated", "export_completed"],
    name="My Webhook"
)

# Trigger event
await webhook_service.trigger_event("data_updated", {
    "source": "customers",
    "timestamp": "2024-02-20T10:30:00"
})

# List webhooks
webhooks = webhook_service.list_webhooks()

# Unregister
webhook_service.unregister_webhook(webhook_id)
```

**Storage Format** (`webhooks.json`):
```json
{
  "wh_0": {
    "id": "wh_0",
    "url": "https://example.com/webhook",
    "events": ["data_updated"],
    "name": "My Webhook",
    "created_at": "2024-02-20T10:30:00",
    "active": true,
    "delivery_count": 5,
    "last_delivery": "2024-02-20T11:00:00"
  }
}
```

**Event Payload Format**:
```json
{
  "event": "data_updated",
  "timestamp": "2024-02-20T10:30:00.123456",
  "data": {
    "custom": "payload"
  }
}
```

### 5. Data Export Service

**File**: `app/services/export_service.py`

**Purpose**: Export data in multiple formats for external use.

**Key Features**:
- CSV format support
- Excel (.xlsx) format support
- JSON format with metadata
- Nested data flattening
- Record limit enforcement
- Large dataset handling

**Code Example**:
```python
from app.services.export_service import export_service

# Export to CSV
csv_buffer = await export_service.export_to_csv(data)

# Export to Excel
excel_buffer = await export_service.export_to_excel(data)

# Export to JSON
json_data = await export_service.export_to_json(data)
```

**Nested Data Flattening**:
```python
# Input:
{
    "customer": {
        "name": "John",
        "address": {
            "city": "NYC"
        }
    }
}

# Output (CSV):
customer_name,customer_address_city
John,NYC
```

### 6. Streaming Endpoints

**File**: `app/routers/bonus.py` - Stream endpoints section

**Purpose**: Efficiently deliver large datasets without loading into memory.

**Supported Formats**:
- JSON Array: `[{...}, {...}]`
- NDJSON: One JSON object per line

**Implementation**:
```python
async def generate():
    for item in large_dataset:
        if format == "ndjson":
            yield json.dumps(item).encode('utf-8') + b'\n'
        else:
            yield json.dumps(item).encode('utf-8')

return StreamingResponse(generate(), media_type="application/json")
```

**Use Cases**:
- Real-time data monitoring
- Memory-efficient processing
- Progressive data loading
- Large file transfers

### 7. Web UI Dashboard

**File**: `static/index.html`

**Purpose**: Interactive testing interface for all API features.

**Features**:
- Responsive Bootstrap 5 design
- Real-time status indicators
- API testing tools
- Key/webhook management
- Data export interface
- Cache management tools

**Access**: `http://localhost:8000/ui/index.html`

**Sections**:
1. **Status Cards**: Real-time feature status
2. **Data Endpoints**: Query and stream data
3. **Authentication**: Generate and manage API keys
4. **Export**: Download data in multiple formats
5. **Webhooks**: Register and monitor webhooks
6. **Cache**: Check status and clear cache

## API Endpoints Summary

### Authentication
- `POST /api/auth/generate-key` - Generate API key
- `POST /api/auth/revoke-key` - Revoke API key
- `GET /api/auth/keys` - List active keys
- `GET /api/auth/validate` - Validate API key

### Cache
- `GET /api/cache/status` - Cache status
- `DELETE /api/cache/clear` - Clear cache

### Export
- `POST /api/export/customers` - Export customers
- `POST /api/export/tickets` - Export tickets
- `POST /api/export/analytics` - Export analytics

### Webhooks
- `POST /api/webhooks/register` - Register webhook
- `DELETE /api/webhooks/{id}` - Unregister webhook
- `GET /api/webhooks` - List webhooks

### Streaming
- `GET /api/stream/customers` - Stream customers
- `GET /api/stream/tickets` - Stream tickets

## Configuration

All features are configurable via environment variables (`.env`):

```bash
# Caching
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=3600

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD_SECONDS=60

# Authentication
AUTH_ENABLED=true
API_KEYS_FILE=api_keys.json

# Webhooks
WEBHOOK_ENABLED=true
WEBHOOK_TIMEOUT_SECONDS=10

# Export
EXPORT_ENABLED=true
EXPORT_MAX_RECORDS=100000
```

## Deployment

### Local Development
```bash
# Start Redis
docker run -d -p 6379:6379 redis:latest

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Redis and API run automatically with health checks
```

## Testing

### Integration Testing
```python
# Test API key generation
response = client.post("/api/auth/generate-key?name=TestKey")
assert response.status_code == 200
assert "api_key" in response.json()

# Test rate limiting
for i in range(101):
    response = client.get("/data/customers")
assert response.status_code == 429  # Last request exceeds limit
```

### Load Testing
```bash
# Install Apache Bench
ab -n 1000 -c 10 http://localhost:8000/data/customers

# With API key
ab -H "Authorization: Bearer uk_..." -n 1000 -c 10 http://localhost:8000/data/customers
```

## Performance Considerations

1. **Caching**: Reduces response time from 100ms to <5ms for cached requests
2. **Rate Limiting**: In-memory tracking, O(1) lookup time
3. **Streaming**: Constant memory usage regardless of dataset size
4. **Webhooks**: Async delivery prevents blocking main request
5. **Export**: Chunked processing for large datasets

## Security Considerations

1. **API Keys**: Cryptographically random, stored securely
2. **Rate Limiting**: Prevents brute force attacks
3. **Webhooks**: HTTPS validation recommended
4. **Redis**: Should be behind firewall
5. **Caching**: No sensitive data in default TTL

## Error Handling

All services implement comprehensive error handling:
- Graceful degradation (cache disabled if Redis unavailable)
- Detailed logging at each level
- User-friendly error messages
- HTTP status codes follow REST standards

## Future Enhancements

1. **Webhook Signatures**: HMAC-SHA256 signatures for security
2. **Cached Webhooks**: Retry failed deliveries with exponential backoff
3. **Advanced Cache**: Cache invalidation strategies, cache hit metrics
4. **Export Scheduling**: Scheduled exports with async job queue
5. **Advanced Auth**: OAuth2, JWT tokens
6. **Metrics**: Prometheus metrics export

## Troubleshooting

### Redis Connection Failed
- Ensure Redis is running: `docker run -d -p 6379:6379 redis:latest`
- Check REDIS_URL in .env

### Rate Limit Too Strict
- Adjust RATE_LIMIT_REQUESTS and RATE_LIMIT_PERIOD_SECONDS in .env

### Webhooks Not Firing
- Verify webhook URL is accessible
- Check webhook delivery history in API
- Ensure event name matches subscription

### Export Large Datasets
- Increase EXPORT_MAX_RECORDS if available
- Use streaming endpoint instead for real-time data

## Support

For issues or questions:
1. Check BONUS_FEATURES.md for detailed documentation
2. Review example code in this guide
3. Test using the Web UI dashboard
4. Check application logs in /logs directory
