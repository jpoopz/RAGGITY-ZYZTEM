# Components (purpose + main entrypoints)

- `rag_api.py` (FastAPI entry): app creation, routes, logging middleware, error handling.
- `modules/*` and `core/*`: feature modules (RAG engine, logging, settings, diagnostics).
- `ui/*`: CustomTkinter components (main window, RAG Chat, CLO Tool window, settings persistence).
- `scripts/*`: developer utilities and repo context tools.
- `docs/*`: architecture, agent memory, and context index.
