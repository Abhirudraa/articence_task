# Quick Start Guide - Bonus Features

## ⚡ Get Started in 5 Minutes

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start Redis (Skip if using Docker Compose)
```bash
docker run -d -p 6379:6379 redis:latest
```

### 3. Run the Server

**Option A: Local Run**
```bash
uvicorn app.main:app --reload
```

**Option B: Docker Compose (Recommended)**
```bash
docker-compose up --build
```

### 4. Access the Dashboard
Open your browser: **http://localhost:8000/ui/index.html**

---

## 🚀 Quick Examples

### Generate API Key
```bash
curl -X POST "http://localhost:8000/api/auth/generate-key?name=MyKey"
```

Response:
```json
{
  "api_key": "uk_...",
  "name": "MyKey",
  "created_at": "2024-02-20T10:30:00"
}
```

### Use API Key
```bash
curl -H "Authorization: Bearer uk_..." \
  http://localhost:8000/data/customers
```

### Stream Large Data
```bash
# JSON format
curl http://localhost:8000/api/stream/customers?format=json

# NDJSON (line-delimited)
curl http://localhost:8000/api/stream/customers?format=ndjson
```

### Export Data
```bash
# CSV
curl "http://localhost:8000/api/export/customers?format=csv" -o customers.csv

# Excel
curl "http://localhost:8000/api/export/customers?format=excel" -o customers.xlsx

# JSON
curl "http://localhost:8000/api/export/customers?format=json"
```

### Register Webhook
```bash
curl -X POST http://localhost:8000/api/webhooks/register \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/webhook",
    "events": ["data_updated"],
    "name": "My Webhook"
  }'
```

### Check Cache Status
```bash
curl http://localhost:8000/api/cache/status
```

### Clear Cache
```bash
curl -X DELETE http://localhost:8000/api/cache/clear
```

---

## 📊 Feature Checklist

- ✅ **Redis Caching** - Automatic 1-hour TTL
- ✅ **Rate Limiting** - 100 requests/minute
- ✅ **Authentication** - API key-based
- ✅ **Webhooks** - Event-driven callbacks
- ✅ **Data Export** - CSV, Excel, JSON
- ✅ **Streaming** - JSON and NDJSON
- ✅ **Web UI** - Interactive dashboard

---

## 📚 Documentation

- [BONUS_FEATURES.md](BONUS_FEATURES.md) - Complete feature documentation
- [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) - Technical implementation details
- [README.md](README.md) - Main project documentation

---

## 🐛 Common Issues

### Redis Connection Error
**Problem**: `Failed to initialize Redis cache`
**Solution**: Start Redis with `docker run -d -p 6379:6379 redis:latest`

### Rate Limit Exceeded
**Problem**: `429 Too Many Requests`
**Solution**: Use an API key or wait 60 seconds

### Export Fails
**Problem**: `Export failed` error
**Solution**: Ensure Pandas and openpyxl are installed

---

## 💡 Tips

1. **Use the Web UI** - Most intuitive way to test all features
2. **Check Logs** - `app.log` provides detailed debugging info
3. **Validate Keys** - Use `/api/auth/validate` to check key status
4. **Monitor Webhooks** - Check delivery count and last delivery time
5. **Clear Cache** - Use before testing to ensure fresh data

---

## 🔗 Useful Links

- OpenAPI Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health
- Web UI: http://localhost:8000/ui/index.html

---

## ⚙️ Configuration (Optional)

Edit `.env` to customize:

```bash
# Disable features
AUTH_ENABLED=false
CACHE_ENABLED=false
WEBHOOK_ENABLED=false

# Adjust rate limits
RATE_LIMIT_REQUESTS=200
RATE_LIMIT_PERIOD_SECONDS=30

# Change cache TTL
CACHE_TTL_SECONDS=1800  # 30 minutes
```

---

## 🎯 Next Steps

1. ✅ Start the server
2. ✅ Visit the Web UI
3. ✅ Generate an API key
4. ✅ Try an export
5. ✅ Register a webhook
6. ✅ Explore streaming

Enjoy! 🎉
