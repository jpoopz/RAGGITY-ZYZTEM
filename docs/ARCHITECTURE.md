# Architecture (high-level map)

- Backend: FastAPI (uvicorn). Key routes include `/health/full`, `/query_stream` (SSE), `/health/clo`.
- UI: Desktop UI (CustomTkinter) and optional web components (RAG Chat, Settings with 'Test Port Now').
- Config: `.env` via `python-dotenv`; `APP_ENV`, `LOG_LEVEL`, `DEBUG` guardrails.
- Observability: Logger middleware; one-line request logs.
- Release/CI: GitHub Actions; deps pinned with lock file when available.
