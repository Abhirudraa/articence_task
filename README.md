# Universal Data Connector

Production-ready **FastAPI** service that provides a unified, voice-optimized interface for querying CRM, Support, and Analytics data via LLM function calling.

---

## 🚀 Overview

Universal Data Connector enables AI assistants to access structured business data through a consistent API. It intelligently:

- Detects data types (tabular, time-series, hierarchical)
- Applies business rules (limit, prioritize, summarize)
- Optimizes responses for voice conversations
- Generates OpenAPI schemas for LLM function calling
- Includes caching, rate limiting, streaming, exports, and webhooks

Built with **Python 3.11+, FastAPI, and Pydantic v2**.

---

## ✨ Core Features

- ✅ Multiple connectors (CRM, Support, Analytics)
- ✅ Intelligent filtering & pagination (default max 10 items)
- ✅ Voice-optimized summaries
- ✅ Data freshness indicators
- ✅ Structured metadata responses
- ✅ Mock data included
- ✅ Docker-ready deployment

---

## 🧠 Voice Optimization Rules

- Limit results (default: 10)
- Prioritize recent/relevant data
- Summarize large datasets
- Include context metadata (e.g., "Showing 3 of 47 results")
- Add freshness indicators (e.g., "Data as of 2 hours ago")

---

## 📦 Bonus Features (Fully Implemented)

- 🔐 API key authentication
- ⚡ Redis caching (TTL support)
- 🚦 Rate limiting per API key
- 📡 Streaming responses (JSON / NDJSON)
- 📤 Data export (CSV, Excel, JSON)
- 🔔 Webhook support
- 🖥 Web UI testing dashboard (`/ui`)

---

## 🛠 Tech Stack

- FastAPI
- Pydantic v2
- Python 3.11+
- Redis (caching)
- Docker & Docker Compose

---

## ▶️ Run Locally

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
