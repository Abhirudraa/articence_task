# Step-by-Step Guide: Run and Test Universal Data Connector

Complete guide with executable code examples for running and testing all features.

---

## 📋 Table of Contents

1. [Prerequisites Check](#prerequisites-check)
2. [Installation](#installation)
3. [Running the Application](#running-the-application)
4. [Testing API Endpoints](#testing-api-endpoints)
5. [Using the Web UI](#using-the-web-ui)
6. [Complete Testing Workflow](#complete-testing-workflow)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites Check

### Check Python Installation
```bash
python --version
# Expected: Python 3.11 or higher
```

If Python is not installed, download from https://www.python.org

---

## Installation

### Step 1: Navigate to Project Directory
```bash
cd c:\Users\ABJ\Downloads\universal-data-connector\universal-data-connector

# On Linux/Mac:
cd ~/Downloads/universal-data-connector/universal-data-connector
```

### Step 2: Create Virtual Environment (Optional but Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed redis-5.0.0
Successfully installed slowapi-0.1.9
Successfully installed pandas-2.0.0
... (other packages)
```

### ✅ Verify Installation
```bash
pip list | grep redis
pip list | grep pandas
```

---

## Running the Application

### Option A: Local Development (Easy)

#### Step 1: Start Redis Server
```bash
# Using Docker (Recommended)
docker run -d -p 6379:6379 redis:latest

# Verify Redis is running
docker ps

# Or if you have Redis installed locally:
redis-server
```

**Expected output:**
```
CONTAINER ID   IMAGE          COMMAND                  CREATED         STATUS       PORTS
abc123def456   redis:latest   "docker-entrypoint.s…"  2 seconds ago   Up 1 second  0.0.0.0:6379->6379/tcp
```

#### Step 2: Start the FastAPI Server
```bash
uvicorn app.main:app --reload

# Or with custom host/port:
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

#### Step 3: Server is Running! 🎉
Access the API:
```
http://localhost:8000/docs
http://localhost:8000/ui/index.html
http://localhost:8000/health
```

---

### Option B: Docker Compose (Recommended for Production)

#### One Command to Run Everything
```bash
docker-compose up --build
```

**Expected output:**
```
[+] Building 2.5s (8/8) FINISHED
[+] Running 2/2
 ✓ Container udc_redis created
 ✓ Container udc_api created

udc_api      | INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### Verify Services Running
```bash
docker-compose ps

# Expected output:
# NAME       COMMAND                  SERVICE  STATUS
# udc_redis  redis-server             redis    Up 2 seconds
# udc_api    uvicorn app.main:app     api      Up 1 second
```

#### Stop Services
```bash
docker-compose down
```

#### View Logs
```bash
# API logs
docker-compose logs udc_api

# Redis logs
docker-compose logs udc_redis

# All logs with follow
docker-compose logs -f
```

---

## Testing API Endpoints

### 1. Health Check
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "ok",
  "timestamp": "2024-02-20T10:30:00"
}
```

### 2. Root Endpoint
```bash
curl http://localhost:8000/
```

**Expected response:**
```json
{
  "app_name": "Universal Data Connector",
  "version": "1.0.0",
  "description": "Universal Data Connector for LLM Function Calling",
  "documentation": "/docs",
  "features": {
    "caching": true,
    "rate_limiting": true,
    "authentication": true,
    "webhooks": true,
    "export": true
  }
}
```

---

## Authentication Examples

### Generate API Key
```bash
curl -X POST "http://localhost:8000/api/auth/generate-key?name=TestKey1"
```

**Response:**
```json
{
  "api_key": "uk_eW91cl9zZWNyZXRfa2V5X3N0cmluZ2hlcmU=",
  "name": "TestKey1",
  "created_at": "2024-02-20T10:30:00.123456"
}
```

**⚠️ Save this API key!** You'll use it for authenticated requests.

### Store API Key in Variable (PowerShell)
```powershell
$API_KEY = "uk_eW91cl9zZWNyZXRfa2V5X3N0cmluZ2hlcmU="
```

### Store API Key in Variable (Bash)
```bash
API_KEY="uk_eW91cl9zZWNyZXRfa2V5X3N0cmluZ2hlcmU="
```

### Validate API Key
```bash
# PowerShell
curl -H "Authorization: Bearer $API_KEY" `
  http://localhost:8000/api/auth/validate

# Bash
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8000/api/auth/validate
```

**Response:**
```json
{
  "valid": true,
  "key_name": "TestKey1",
  "rate_limit": "unlimited"
}
```

### List All API Keys
```bash
curl http://localhost:8000/api/auth/keys
```

**Response:**
```json
{
  "keys": [
    {
      "key": "uk_...",
      "name": "TestKey1",
      "created_at": "2024-02-20T10:30:00",
      "last_used": "2024-02-20T10:31:00",
      "active": true,
      "rate_limit": "unlimited"
    }
  ]
}
```

---

## Data Queries with Authentication

### Fetch Customers
```bash
# PowerShell
curl -H "Authorization: Bearer $API_KEY" `
  "http://localhost:8000/data/customers?limit=5"

# Bash
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8000/data/customers?limit=5"
```

**Response:**
```json
{
  "data": [
    {
      "customer_id": 1,
      "name": "John Doe",
      "email": "john@example.com",
      "created_at": "2024-01-15",
      "status": "active"
    }
  ],
  "metadata": {
    "total_results": 50,
    "returned_results": 1,
    "data_type": "tabular",
    "context": "showing 1 of 50 customers"
  }
}
```

### Fetch Support Tickets
```bash
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8000/data/tickets?status=open&limit=5"
```

### Fetch Analytics
```bash
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8000/data/analytics?limit=10"
```

---

## Streaming Endpoints

### Stream Customers (JSON Format)
```bash
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8000/api/stream/customers?format=json" | python -m json.tool
```

### Stream Customers (NDJSON Format)
```bash
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8000/api/stream/customers?format=ndjson"
```

**Output (one JSON per line):**
```
{"customer_id": 1, "name": "John Doe", "email": "john@example.com", ...}
{"customer_id": 2, "name": "Jane Smith", "email": "jane@example.com", ...}
{"customer_id": 3, "name": "Bob Johnson", "email": "bob@example.com", ...}
```

---

## Cache Management

### Check Cache Status
```bash
curl http://localhost:8000/api/cache/status
```

**Response:**
```json
{
  "enabled": true,
  "healthy": true,
  "ttl_seconds": 3600
}
```

### Clear All Cache
```bash
curl -X DELETE http://localhost:8000/api/cache/clear
```

**Response:**
```json
{
  "status": "success",
  "message": "Cleared all cache"
}
```

### Clear Specific Namespace
```bash
curl -X DELETE "http://localhost:8000/api/cache/clear?namespace=customer"
```

---

## Data Export

### Export Customers as CSV
```bash
# PowerShell
curl -H "Authorization: Bearer $API_KEY" `
  "http://localhost:8000/api/export/customers?format=csv" `
  -o customers.csv

# Bash
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8000/api/export/customers?format=csv" \
  -o customers.csv
```

**File created:** `customers.csv` (in current directory)

**File content:**
```csv
customer_id,name,email,created_at,status
1,John Doe,john@example.com,2024-01-15,active
2,Jane Smith,jane@example.com,2024-01-20,active
```

### Export Customers as Excel
```bash
# PowerShell
curl -H "Authorization: Bearer $API_KEY" `
  "http://localhost:8000/api/export/customers?format=excel" `
  -o customers.xlsx

# Bash
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8000/api/export/customers?format=excel" \
  -o customers.xlsx
```

**File created:** `customers.xlsx` (Excel spreadsheet)

### Export Customers as JSON
```bash
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8000/api/export/customers?format=json" | python -m json.tool
```

**Response:**
```json
{
  "exported_at": "2024-02-20T10:30:00",
  "record_count": 50,
  "data": [
    {"customer_id": 1, "name": "John Doe", ...},
    {"customer_id": 2, "name": "Jane Smith", ...}
  ]
}
```

### Export Tickets
```bash
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8000/api/export/tickets?format=csv" \
  -o tickets.csv
```

### Export Analytics
```bash
curl -H "Authorization: Bearer $API_KEY" \
  "http://localhost:8000/api/export/analytics?format=excel" \
  -o analytics.xlsx
```

---

## Webhook Management

### Register a Webhook
```bash
# PowerShell
curl -X POST http://localhost:8000/api/webhooks/register `
  -H "Content-Type: application/json" `
  -d '{
    "url": "https://webhook.site/unique-id-here",
    "events": ["data_updated", "export_completed"],
    "name": "My Test Webhook"
  }' | python -m json.tool

# Bash
curl -X POST http://localhost:8000/api/webhooks/register \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://webhook.site/unique-id-here",
    "events": ["data_updated", "export_completed"],
    "name": "My Test Webhook"
  }' | python -m json.tool
```

**Response:**
```json
{
  "id": "wh_0",
  "url": "https://webhook.site/unique-id-here",
  "events": ["data_updated", "export_completed"],
  "name": "My Test Webhook",
  "created_at": "2024-02-20T10:30:00",
  "active": true,
  "delivery_count": 0,
  "last_delivery": null
}
```

**💡 Tip:** Use https://webhook.site for free webhook testing

### List All Webhooks
```bash
curl http://localhost:8000/api/webhooks
```

**Response:**
```json
{
  "webhooks": [
    {
      "id": "wh_0",
      "url": "https://webhook.site/unique-id",
      "events": ["data_updated"],
      "name": "My Webhook",
      "active": true,
      "delivery_count": 5,
      "last_delivery": "2024-02-20T10:35:00"
    }
  ]
}
```

### Unregister a Webhook
```bash
curl -X DELETE http://localhost:8000/api/webhooks/wh_0
```

**Response:**
```json
{
  "status": "success",
  "message": "Webhook unregistered"
}
```

---

## Rate Limiting

### Make Multiple Requests to See Rate Limiting
```bash
# PowerShell - Make 10 requests
for ($i=1; $i -le 10; $i++) {
  curl -H "Authorization: Bearer $API_KEY" `
    http://localhost:8000/data/customers | python -m json.tool
  Write-Host "Request $i completed"
  Start-Sleep -Milliseconds 100
}

# Bash - Make 10 requests
for i in {1..10}; do
  echo "Request $i"
  curl -H "Authorization: Bearer $API_KEY" \
    http://localhost:8000/data/customers | python -m json.tool
  sleep 0.1
done
```

### Check Rate Limit Headers
```bash
curl -i -H "Authorization: Bearer $API_KEY" \
  http://localhost:8000/data/customers 2>&1 | grep -i "x-ratelimit"
```

**Expected output:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1673456789
```

### Exceed Rate Limit (100 requests per 60 seconds)
```bash
# PowerShell - Rapid requests to hit limit
for ($i=1; $i -le 110; $i++) {
  $response = curl -H "Authorization: Bearer $API_KEY" `
    http://localhost:8000/data/customers
  if ($response -like "*429*") {
    Write-Host "Rate limit hit at request $i"
    break
  }
}

# Bash
for i in {1..110}; do
  response=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: Bearer $API_KEY" \
    http://localhost:8000/data/customers)
  if [ "$response" = "429" ]; then
    echo "Rate limit hit at request $i"
    break
  fi
done
```

**When limit exceeded:**
```json
{
  "detail": "Rate limit exceeded. Try again later."
}
```

---

## Using the Web UI

### Open Web UI
```
http://localhost:8000/ui/index.html
```

### Features in Web UI

#### 1. Data Testing
- Select data source (Customers, Tickets, Analytics)
- Choose response type (Normal or Streaming)
- Click "Fetch Data"
- View formatted JSON response

#### 2. Authentication Tab
- Generate new API key with custom name
- View all active API keys
- See key creation date and rate limits

#### 3. Export Tab
- Select data source
- Choose format (CSV, Excel, JSON)
- Download file automatically

#### 4. Webhooks Tab
- Enter webhook URL
- Select events to subscribe
- Register and monitor deliveries
- View delivery history

#### 5. Cache Tab
- Check Redis connection status
- View cache health
- Clear cache on demand

---

## Complete Testing Workflow

### Full End-to-End Test
```bash
# 1. Generate API Key
echo "=== 1. Generating API Key ==="
$API_KEY = (curl -s -X POST "http://localhost:8000/api/auth/generate-key?name=TestWorkflow" | python -m json.tool | Select-String "api_key").ToString().Split('"')[3]
Write-Host "API Key: $API_KEY"

# 2. Validate Key
echo "`n=== 2. Validating API Key ==="
curl -H "Authorization: Bearer $API_KEY" http://localhost:8000/api/auth/validate | python -m json.tool

# 3. Fetch Data
echo "`n=== 3. Fetching Customer Data ==="
curl -H "Authorization: Bearer $API_KEY" "http://localhost:8000/data/customers?limit=3" | python -m json.tool

# 4. Check Cache
echo "`n=== 4. Checking Cache Status ==="
curl http://localhost:8000/api/cache/status | python -m json.tool

# 5. Register Webhook
echo "`n=== 5. Registering Webhook ==="
curl -X POST http://localhost:8000/api/webhooks/register `
  -H "Content-Type: application/json" `
  -d '{"url":"https://webhook.site/test","events":["data_updated"],"name":"Test"}' | python -m json.tool

# 6. Export Data
echo "`n=== 6. Exporting Data as JSON ==="
curl -H "Authorization: Bearer $API_KEY" "http://localhost:8000/api/export/customers?format=json" | python -m json.tool

# 7. Stream Data
echo "`n=== 7. Streaming Data ==="
curl -H "Authorization: Bearer $API_KEY" "http://localhost:8000/api/stream/customers?format=ndjson" | head -n 3

echo "`n=== ✅ All tests completed! ==="
```

### Same workflow in Bash
```bash
#!/bin/bash

# 1. Generate API Key
echo "=== 1. Generating API Key ==="
API_KEY=$(curl -s -X POST "http://localhost:8000/api/auth/generate-key?name=TestWorkflow" | python -m json.tool | grep "api_key" | awk -F'"' '{print $4}')
echo "API Key: $API_KEY"

# 2. Validate Key
echo -e "\n=== 2. Validating API Key ==="
curl -s -H "Authorization: Bearer $API_KEY" http://localhost:8000/api/auth/validate | python -m json.tool

# 3. Fetch Data
echo -e "\n=== 3. Fetching Customer Data ==="
curl -s -H "Authorization: Bearer $API_KEY" "http://localhost:8000/data/customers?limit=3" | python -m json.tool

# 4. Check Cache
echo -e "\n=== 4. Checking Cache Status ==="
curl -s http://localhost:8000/api/cache/status | python -m json.tool

# 5. Register Webhook
echo -e "\n=== 5. Registering Webhook ==="
curl -s -X POST http://localhost:8000/api/webhooks/register \
  -H "Content-Type: application/json" \
  -d '{"url":"https://webhook.site/test","events":["data_updated"],"name":"Test"}' | python -m json.tool

# 6. Export Data
echo -e "\n=== 6. Exporting Data as JSON ==="
curl -s -H "Authorization: Bearer $API_KEY" "http://localhost:8000/api/export/customers?format=json" | python -m json.tool

# 7. Stream Data
echo -e "\n=== 7. Streaming Data ==="
curl -s -H "Authorization: Bearer $API_KEY" "http://localhost:8000/api/stream/customers?format=ndjson" | head -n 3

echo -e "\n=== ✅ All tests completed! ==="
```

---

## Run Python Tests

### Install Test Dependencies
```bash
pip install pytest pytest-asyncio httpx
```

### Run Tests
```bash
# Run all bonus feature tests
pytest tests/test_bonus_features.py -v

# Run specific test class
pytest tests/test_bonus_features.py::TestAuthentication -v

# Run with coverage
pytest tests/test_bonus_features.py --cov=app --cov-report=html
```

**Expected output:**
```
tests/test_bonus_features.py::TestAuthentication::test_generate_api_key PASSED
tests/test_bonus_features.py::TestAuthentication::test_list_api_keys PASSED
tests/test_bonus_features.py::TestAuthentication::test_validate_api_key PASSED
tests/test_bonus_features.py::TestCaching::test_cache_status PASSED
...
```

---

## Load Testing

### Using Apache Bench (ab)
```bash
# Install Apache Bench
# Windows: choco install apache-bench
# Mac: brew install httpd
# Linux: sudo apt-get install apache2-utils

# Simple load test
ab -n 100 -c 10 http://localhost:8000/health

# With API key
ab -n 100 -c 10 -H "Authorization: Bearer uk_yourkeyhere" \
  http://localhost:8000/data/customers
```

### Using wrk (Modern Load Testing)
```bash
# Install wrk
# Windows: choco install wrk
# Mac: brew install wrk
# Linux: https://github.com/wg/wrk

wrk -t4 -c100 -d30s http://localhost:8000/health
```

---

## Troubleshooting

### Issue: Can't Connect to Redis
```bash
# Check if Redis is running
docker ps | grep redis

# If not running, start it
docker run -d -p 6379:6379 redis:latest

# Test Redis connection
redis-cli ping
# Expected: PONG
```

### Issue: Port 8000 Already in Use
```bash
# Use different port
uvicorn app.main:app --port 8001

# Or kill process on port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux
lsof -i :8000
kill -9 <PID>
```

### Issue: Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Verify installation
python -c "import redis; import pandas; print('OK')"
```

### Issue: Module Not Found
```bash
# Make sure you're in the project directory
cd universal-data-connector

# Activate virtual environment
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

### Issue: Authentication Failed
```bash
# Generate new API key
curl -X POST "http://localhost:8000/api/auth/generate-key?name=NewKey"

# Verify key format (should start with uk_)
# Use exact key in Authorization header
```

---

## Monitoring & Debugging

### View Application Logs
```bash
# If running locally
# Logs will appear in the terminal

# If using Docker
docker-compose logs -f udc_api

# Filter logs
docker-compose logs udc_api | grep ERROR
```

### Enable Debug Mode
```bash
# Edit .env file
cat .env.example > .env
# Set DEBUG=True in .env

# Restart server
```

### Check API Documentation
```
http://localhost:8000/docs       # Swagger UI
http://localhost:8000/redoc      # ReDoc
http://localhost:8000/openapi.json  # OpenAPI schema
```

---

## Next Steps

1. ✅ Start the application (`docker-compose up --build`)
2. ✅ Generate an API key
3. ✅ Test a few endpoints
4. ✅ Try the Web UI
5. ✅ Export some data
6. ✅ Register a webhook
7. ✅ Run the test suite
8. ✅ Review the code

---

## Quick Command Reference

```bash
# Start application
docker-compose up --build

# Generate API key
curl -X POST "http://localhost:8000/api/auth/generate-key?name=key1"

# Fetch data
curl -H "Authorization: Bearer YOUR_KEY" http://localhost:8000/data/customers

# Export data
curl -H "Authorization: Bearer YOUR_KEY" \
  "http://localhost:8000/api/export/customers?format=csv" -o data.csv

# Stream data
curl -H "Authorization: Bearer YOUR_KEY" \
  http://localhost:8000/api/stream/customers?format=ndjson

# Register webhook
curl -X POST http://localhost:8000/api/webhooks/register \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/webhook","events":["data_updated"],"name":"test"}'

# Check cache
curl http://localhost:8000/api/cache/status

# Run tests
pytest tests/test_bonus_features.py -v
```

---

**You're all set! Start with:** `docker-compose up --build` 🚀
