# Bonus Features Documentation

## Overview

This document describes the advanced bonus features implemented in the Universal Data Connector API.

## Table of Contents

1. [Caching with Redis](#caching-with-redis)
2. [Rate Limiting](#rate-limiting)
3. [Streaming Responses](#streaming-responses)
4. [Web UI](#web-ui)
5. [Authentication & API Keys](#authentication--api-keys)
6. [Webhooks](#webhooks)
7. [Data Export](#data-export)

---

## Caching with Redis

### Overview
Implements a Redis-based caching layer to optimize frequently accessed data and reduce latency.

### Configuration
```bash
# In .env file
REDIS_ENABLED=true
REDIS_URL=redis://localhost:6379/0
CACHE_ENABLED=true
CACHE_TTL_SECONDS=3600  # 1 hour default
```

### Features
- **Automatic Caching**: Data from connectors is automatically cached with 1-hour TTL
- **Namespace Support**: Cache keys organized by data type (customer, ticket, analytics)
- **Health Checks**: Built-in Redis connectivity verification
- **Cache Management**: Clear cache programmatically via API

### Usage

#### Get Cache Status
```bash
curl http://localhost:8000/api/cache/status
```

Response:
```json
{
  "enabled": true,
  "healthy": true,
  "ttl_seconds": 3600
}
```

#### Clear Cache
```bash
# Clear all cache
curl -X DELETE http://localhost:8000/api/cache/clear

# Clear specific namespace
curl -X DELETE "http://localhost:8000/api/cache/clear?namespace=customer"
```

### Installation
```bash
# Start Redis server (Docker)
docker run -d -p 6379:6379 redis:latest

# Or if you have Redis installed locally
redis-server
```

---

## Rate Limiting

### Overview
Implements request rate limiting to prevent abuse and ensure fair API usage.

### Configuration
```bash
# In .env file
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100      # Max requests per period
RATE_LIMIT_PERIOD_SECONDS=60 # Time window in seconds
```

### Features
- **Per-Client Limiting**: Tracks limits by API key or IP address
- **Header Information**: Returns rate limit info in response headers
- **Graceful Degradation**: Automatic cleanup of old request records

### Usage

#### Response Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1673456789
```

#### Rate Limit Exceeded
When limit is exceeded:
```json
{
  "detail": "Rate limit exceeded. Try again later.",
  "status_code": 429
}
```

### Customization
Adjust in `config.py`:
```python
RATE_LIMIT_REQUESTS = 100       # Requests per period
RATE_LIMIT_PERIOD_SECONDS = 60  # Time window
```

---

## Streaming Responses

### Overview
Implements server-sent streaming for real-time data delivery, ideal for large datasets.

### Endpoints

#### Stream Customers
```bash
curl http://localhost:8000/api/stream/customers?format=json
```

#### Stream Support Tickets
```bash
curl http://localhost:8000/api/stream/tickets?format=ndjson
```

### Formats

#### JSON Array
```bash
curl http://localhost:8000/api/stream/customers?format=json
```

Returns:
```json
[
  {"customer_id": 1, "name": "John Doe", ...},
  {"customer_id": 2, "name": "Jane Smith", ...}
]
```

#### NDJSON (Newline-Delimited JSON)
```bash
curl http://localhost:8000/api/stream/customers?format=ndjson
```

Returns:
```
{"customer_id": 1, "name": "John Doe", ...}
{"customer_id": 2, "name": "Jane Smith", ...}
```

### Use Cases
- Large dataset transfers
- Real-time monitoring dashboards
- Memory-efficient data processing
- Progressive data loading in web UIs

---

## Web UI

### Overview
A modern, interactive web interface for testing and managing the API.

### Access
```
http://localhost:8000/ui/index.html
```

### Features

#### Data Endpoints Tab
- Query data sources (Customers, Tickets, Analytics)
- Choose between normal and streaming responses
- View formatted JSON responses

#### Authentication Tab
- Generate new API keys
- List active API keys
- View key metadata (creation time, rate limits)

#### Export Tab
- Export data in CSV, Excel, or JSON formats
- Original data is retained while exports are generated
- Automatic file download for CSV/Excel

#### Webhooks Tab
- Register webhooks with custom URLs
- Subscribe to specific events
- View webhook delivery history

#### Cache Management Tab
- Check Redis cache status
- Clear cache on demand
- View cache health metrics

### Features
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Updates**: Status indicators update dynamically
- **Dark Theme**: Eye-friendly interface with gradient styling
- **Error Handling**: Clear error messages and suggestions

---

## Authentication & API Keys

### Overview
Implements API key-based authentication for secure endpoint access.

### Configuration
```bash
# In .env file
AUTH_ENABLED=true
SECRET_KEY=your-secret-key-change-in-production
API_KEYS_FILE=api_keys.json
```

### API Key Format
```
uk_<random-base64-string>
```

Example: `uk_eW91ci1zZWNyZXQta2V5LXN0cmluZ2hlcmU=`

### Endpoints

#### Generate API Key
```bash
curl -X POST "http://localhost:8000/api/auth/generate-key?name=My%20Key"
```

Response:
```json
{
  "api_key": "uk_...",
  "name": "My Key",
  "created_at": "2024-02-20T10:30:00"
}
```

#### Validate API Key
```bash
curl -H "Authorization: Bearer uk_..." \
  http://localhost:8000/api/auth/validate
```

#### List API Keys
```bash
curl http://localhost:8000/api/auth/keys
```

#### Revoke API Key
```bash
curl -X POST \
  "http://localhost:8000/api/auth/revoke-key?api_key=uk_..."
```

### Usage

#### Using API Key in Requests
```bash
# Header method
curl -H "Authorization: Bearer uk_your-key-here" \
  http://localhost:8000/data/customers

# Query parameter method (alternative)
curl "http://localhost:8000/data/customers?api_key=uk_your-key-here"
```

### Unprotected Routes
These routes don't require authentication:
- `/` - Root endpoint
- `/docs` - Swagger documentation
- `/redoc` - ReDoc documentation
- `/openapi.json` - OpenAPI schema
- `/health` - Health check endpoint
- `/metrics` - Metrics endpoint

---

## Webhooks

### Overview
Real-time event notification system that triggers HTTP POST requests to registered URLs.

### Configuration
```bash
# In .env file
WEBHOOK_ENABLED=true
WEBHOOK_TIMEOUT_SECONDS=10
WEBHOOKS_FILE=webhooks.json
```

### Events

Available events to subscribe to:
- `data_updated` - When data sources are updated
- `export_completed` - When data export completes
- `rate_limit` - When rate limit is approached
- `health_check` - Periodic system health events

### Endpoints

#### Register Webhook
```bash
curl -X POST http://localhost:8000/api/webhooks/register \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/webhook",
    "events": ["data_updated", "export_completed"],
    "name": "My Webhook"
  }'
```

Response:
```json
{
  "id": "wh_0",
  "url": "https://example.com/webhook",
  "events": ["data_updated", "export_completed"],
  "name": "My Webhook",
  "created_at": "2024-02-20T10:30:00",
  "active": true,
  "delivery_count": 0,
  "last_delivery": null
}
```

#### List Webhooks
```bash
curl http://localhost:8000/api/webhooks
```

#### Unregister Webhook
```bash
curl -X DELETE http://localhost:8000/api/webhooks/wh_0
```

### Webhook Payload

When an event occurs, the following payload is sent:

```json
{
  "event": "data_updated",
  "timestamp": "2024-02-20T10:30:00.123456",
  "data": {
    "source": "customers",
    "record_count": 42,
    "last_updated": "2024-02-20T10:30:00"
  }
}
```

### Testing Webhooks

Use a webhook testing service like [webhook.site](https://webhook.site):

1. Create a temporary webhook URL
2. Register it with the API:
```bash
curl -X POST http://localhost:8000/api/webhooks/register \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://webhook.site/your-unique-id",
    "events": ["data_updated"],
    "name": "Test Webhook"
  }'
```
3. Monitor events in real-time on webhook.site

### Retry Logic
- **Automatic Retry**: Failed webhooks are retried up to 3 times
- **Exponential Backoff**: Wait time increases with each retry
- **Timeout**: 10-second timeout for webhook delivery

---

## Data Export

### Overview
Export data in multiple formats (CSV, Excel, JSON) for use in external tools.

### Configuration
```bash
# In .env file
EXPORT_ENABLED=true
EXPORT_MAX_RECORDS=100000
```

### Endpoints

#### Export Customers
```bash
# CSV format
curl "http://localhost:8000/api/export/customers?format=csv" \
  -o customers.csv

# Excel format
curl "http://localhost:8000/api/export/customers?format=excel" \
  -o customers.xlsx

# JSON format
curl "http://localhost:8000/api/export/customers?format=json"
```

#### Export Support Tickets
```bash
curl "http://localhost:8000/api/export/tickets?format=csv"
curl "http://localhost:8000/api/export/tickets?format=excel"
curl "http://localhost:8000/api/export/tickets?format=json"
```

#### Export Analytics
```bash
curl "http://localhost:8000/api/export/analytics?format=csv"
curl "http://localhost:8000/api/export/analytics?format=excel"
curl "http://localhost:8000/api/export/analytics?format=json"
```

### Formats

#### CSV
Plain text format for use in spreadsheets:
```
customer_id,name,email,created_at,status
1,John Doe,john@example.com,2024-01-15,active
2,Jane Smith,jane@example.com,2024-01-20,active
```

#### Excel (.xlsx)
Native Excel format with proper formatting:
- Column headers
- Data types preserved
- Optional formatting and styles

#### JSON
Structured format with metadata:
```json
{
  "exported_at": "2024-02-20T10:30:00",
  "record_count": 2,
  "data": [
    {"customer_id": 1, "name": "John Doe", ...},
    {"customer_id": 2, "name": "Jane Smith", ...}
  ]
}
```

### Features
- **Large Datasets**: Efficiently handles up to 100,000 records
- **Nested Data Flattening**: Automatically flattens nested structures for CSV/Excel
- **Type Preservation**: JSON exports maintain original data types
- **Progress Tracking**: Web UI shows export progress

### Use Cases
- Data analysis in Excel/Sheets
- Import into BI tools (Tableau, Power BI)
- Backup and archival
- Integration with external systems

---

## Summary of Features

| Feature | Enabled | Purpose |
|---------|---------|---------|
| **Caching** | ✓ | Reduce latency, improve performance |
| **Rate Limiting** | ✓ | Prevent abuse, fair usage |
| **Streaming** | ✓ | Handle large datasets efficiently |
| **Web UI** | ✓ | Interactive testing interface |
| **Authentication** | ✓ | Secure API access |
| **Webhooks** | ✓ | Real-time event notifications |
| **Export** | ✓ | Data extraction in multiple formats |

---

## Troubleshooting

### Redis Connection Issues
```
Error: Failed to initialize Redis cache
```
**Solution**: Ensure Redis is running on localhost:6379
```bash
docker run -d -p 6379:6379 redis:latest
```

### Rate Limit Issues
```
Error: Rate limit exceeded
```
**Solution**: Wait for the timeout period or use an API key with higher limits

### Authentication Failures
```
Error: Invalid or inactive API key
```
**Solution**: Generate a new API key using the generate-key endpoint

### Webhook Delivery Failures
Check webhook status in the web UI or list webhooks endpoint to see delivery count and last delivery time.

---

## Performance Tips

1. **Use Caching**: Enable Redis caching for frequently accessed data
2. **Streaming for Large Data**: Use streaming endpoints instead of normal REST for large datasets
3. **API Rate Limiting**: Respect rate limits in client applications
4. **Webhook Batching**: Batch webhook events to reduce server load
5. **Export in Background**: Use async exports for very large datasets

---

## Security Recommendations

1. **API Key Management**:
   - Rotate keys regularly
   - Don't share keys in version control
   - Revoke unused keys

2. **Webhook Security**:
   - Validate webhook signatures (optional implementation)
   - Use HTTPS for webhook URLs
   - Implement request throttling on webhook endpoints

3. **Rate Limiting**:
   - Adjust limits based on expected traffic
   - Monitor for attack patterns
   - Implement IP whitelisting if needed

4. **Caching**:
   - Keep Redis behind a firewall
   - Use Redis authentication
   - Regular backups of cached data

---

## Next Steps

- Deploy to production with Docker
- Scale Redis for high traffic
- Implement webhook signature verification
- Add metrics and monitoring
- Set up automated backups
