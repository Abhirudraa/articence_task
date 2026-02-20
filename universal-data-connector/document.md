# Universal Data Connector — Documentation

This document supplements the repository README with clear setup instructions, API usage, OpenAPI/function-calling notes, testing and mock-data guidance, and example usage scenarios optimized for voice + LLM integration.

---

## 1. Overview

This project exposes a FastAPI application that provides unified access to CRM, Support, and Analytics data sources, plus an intelligent `ask` endpoint that routes natural language queries to built-in functions or an LLM fallback.

- Main app entry: [app/main.py](app/main.py)
- Routers: [app/routers/data.py](app/routers/data.py)
- Models: [app/models/common.py](app/models/common.py)
- Services: [app/services](app/services)
- Utilities (logging, mock data): [app/utils](app/utils)

The app is optimized for voice assistant responses (short, contextual replies) and includes an LLM service abstraction that supports a Gemini integration and a Mock fallback: [app/services/llm_service.py](app/services/llm_service.py)

---

## 2. Quick Setup

Prerequisites: Python 3.11+ recommended, pip, and a virtualenv.

1. Create and activate a virtual environment:

```bash
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# or cmd: .\.venv\Scripts\activate.bat
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Environment variables

Copy `.env.example` to `.env` and adjust settings. Key settings used by the app:

- `GEMINI_API_KEY` — API key for Google Gemini (if you want real LLM calls).
- `GEMINI_MODEL` — model name used by `GeminiService` (see `app/services/llm_service.py`).
- `ENABLE_LLM` — toggle LLM usage in `QueryExecutor`.

Note: the codebase previously referenced `OPENAI_API_KEY` in some user-facing messages. The implemented LLM integration expects `GEMINI_API_KEY`. Update any docs or messages to match your chosen provider.

4. Run the app locally:

```bash
uvicorn app.main:app --reload --port 8000
```

The interactive API docs are available at `http://localhost:8000/docs` (Swagger) and `http://localhost:8000/redoc`.

---

## 3. OpenAPI & Function Calling

- The app exposes OpenAPI at `/openapi.json` ([app/main.py](app/main.py#L1-L120)).
- A custom `custom_openapi` function adds example function-calling metadata under `info.x-examples` to guide LLM function calls.

To fetch the schema programmatically:

```bash
curl http://localhost:8000/openapi.json -o openapi.json
```

Use `/docs` to inspect request/response models generated from Pydantic models in [app/models/common.py](app/models/common.py).

---

## 4. Endpoints (high-level)

- `GET /` — root info. See `app/main.py` root handler.
- `GET /health`, `/health/readiness`, `/health/liveness` — health checks. See [app/routers/health.py](app/routers/health.py).
- `GET /data/customers` — customer list, supports `status` and `limit` query params. See [app/routers/data.py](app/routers/data.py#L1-L80).
- `GET /data/support-tickets` — support tickets, supports `status`, `priority`, `limit`.
- `GET /data/analytics` — analytics metrics, supports `metric` and `limit`.
- `POST /data/ask` — natural language `ask` endpoint. Request model: `QueryRequest` in [app/models/common.py](app/models/common.py#L1-L200). Response: `QueryResponse`.

Each endpoint returns a `DataResponse` object structure created from `Metadata` and `data` (see [app/models/common.py](app/models/common.py)).

---

## 5. Example Usage (curl)

Get active customers (JSON response optimized for voice):

```bash
curl "http://localhost:8000/data/customers?status=active&limit=5"
```

Ask a natural language question via the intelligent endpoint:

```bash
curl -X POST http://localhost:8000/data/ask \
  -H "Content-Type: application/json" \
  -d '{"query":"Show me active customers","use_llm_if_needed":true}'
```

The `POST /data/ask` endpoint attempts to parse the query and use built-in connectors/functions first; it falls back to the LLM when analysis determines complexity or data relationships require LLM reasoning.

---

## 6. LLM Integration & Function Calling Notes

- The LLM abstraction is at `app/services/llm_service.py`. It exposes two classes: `GeminiService` and `MockLLMService` and a helper `get_openai_service()` that returns an instance depending on environment.
- The `QueryExecutor` uses `get_openai_service()` when `ENABLE_LLM` is true to route complex queries to the LLM. See [app/services/query_executor.py](app/services/query_executor.py#L1-L120).

Recommendations:

- If you plan to use real LLM calls, set `GEMINI_API_KEY` in `.env` and `ENABLE_LLM=true`.
- Align documentation and user-facing messages: replace any `OPENAI_API_KEY` references with `GEMINI_API_KEY` (or add both if you support multiple providers).
- For testing or CI, keep `GEMINI_API_KEY` empty so the mock service is used automatically.

---

## 7. Voice Optimization & Business Rules

- Voice optimizations are implemented in `app/services/voice_optimizer.py`. It summarizes large result sets and limits verbosity for voice assistants.
- Business rules for pagination, status filtering, and prioritization live in `app/services/business_rules.py`.

If you want more aggressive voice brevity, tweak `VOICE_SUMMARY_THRESHOLD` and `MAX_RESULTS` in your environment/config (
[app/config.py](app/config.py)
).

---

## 8. Mock Data & Tests

- Mock data generators: `app/utils/mock_data.py` with `generate_customers`, `generate_support_tickets`, and `generate_analytics` and `save_mock_data()` to create JSON files under `data/`.

Generate sample data locally before running certain manual checks:

```bash
python -c "from app.utils.mock_data import save_mock_data; save_mock_data()"
```

- Tests are in `tests/` and use `pytest` + FastAPI `TestClient`.
Run the test suite locally:

```bash
pytest -q
```

Notes:

- The tests expect the app to be importable and the connectors to find data under `data/` or the mock generator to provide data. If tests fail due to missing files, run `save_mock_data()` first.

---

## 9. Recommended Small Code/Docs Fixes (actionable)

1. Unify LLM env variable naming and messages: update `app/services/query_executor.py` user message that references `OPENAI_API_KEY` to reference `GEMINI_API_KEY` (or both), and update `.env.example` and README accordingly.
   - See: [app/services/query_executor.py](app/services/query_executor.py#L1-L120) and [app/services/llm_service.py](app/services/llm_service.py#L1-L40).

2. Add a short note in the top-level README about LLM costs, mock mode, and how to enable the Gemini key for production.

3. (Optional) Add a small `CONTRIBUTING.md` with preferred code style/PR requirements and how to run tests locally.

---

## 10. Troubleshooting

- If the app logs show LLM initialization errors, the application will fall back to the Mock LLM. Ensure `GEMINI_API_KEY` is valid for real usage.
- If API responses return fewer items than expected, check `MAX_RESULTS` and `VOICE_SUMMARY_THRESHOLD` in your config and the connectors in `app/connectors/*` for their `fetch()` logic.

---

## 11. Example: How to update the env var message (quick patch suggestion)

Edit the message in `app/services/query_executor.py` that currently instructs to set `OPENAI_API_KEY` and replace it with `GEMINI_API_KEY` in the instructions and README.

Example snippet to change in `app/services/query_executor.py`:

```python
    "message": "Complex query detected but LLM is not configured. Please set GEMINI_API_KEY in .env",
```

---

## 12. Next Steps I can help with

- Apply the env-var/documentation patch and update `.env.example` / `README.md`.
- Run the test suite here and fix any failing tests.
- Add a short `CONTRIBUTING.md` and expand `README.md` if you want.

---

File created: [document.md](document.md)
