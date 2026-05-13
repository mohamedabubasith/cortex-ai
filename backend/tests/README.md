# Backend tests

## Knowledge base (Haystack / Qdrant)

`tests/test_kb_automated.py` contains **unit tests** for Haystack-style metadata filters (`meta.kb_id` mapping from legacy `{ "kb_id": "..." }` and `{ "kb_id": { "$in": [...] } }` shapes).

```bash
cd backend
uv run pytest tests/test_kb_automated.py -v
```

### Integration (optional)

**Full KB E2E** (Postgres row + `process_kb` + status poll + search + cleanup):

```bash
cd backend
export RUN_RAG_E2E=1
export DATABASE_URL='postgresql+asyncpg://USER:PASS@HOST:5432/chat_db'
export UNSTRUCTURED_API_URL='https://your-unstructured-host/'
export UNSTRUCTURED_API_KEY='...'   # if your Unstructured instance requires it
export OLLAMA_BASE_URL='https://your-ollama-host/'
export OLLAMA_MODEL='paraphrase-multilingual:latest'
export QDRANT_URL='https://your-qdrant-host/'
export QDRANT_COLLECTION='Rag'
export QDRANT_API_KEY='...'   # if your Qdrant instance requires it
export INTEGRATION_USER_EMAIL='existing-user@your-app'
export INTEGRATION_USER_PASSWORD='...'

uv run pytest tests/test_rag_e2e_integration.py::test_rag_kb_ingest_status_and_search_db_path -v -s
```

**HTTP E2E** against a running API (upload → `/status` → `/query`):

```bash
export RUN_RAG_HTTP_E2E=1
export LIVE_API_BASE_URL='http://127.0.0.1:8000'
# same INTEGRATION_USER_* (and optional INTEGRATION_TENANT_ID)
uv run pytest tests/test_rag_e2e_integration.py::test_rag_http_upload_status_query_live_api -v -s
```

**RAG full pipeline** (file on disk → parse → chunk → embed → Qdrant index → search → cleanup; **no Postgres**, same `rag_service.process_document` as worker core):

```bash
cd backend
export RUN_RAG_FULL_PIPELINE=1
export QDRANT_URL='http://your-qdrant-host:80'
export QDRANT_API_KEY='...'            # if required
export QDRANT_COLLECTION='haystack_kb' # must be Haystack-owned (not a legacy Qdrant-only collection)
export UNSTRUCTURED_API_KEY='...'      # if required
uv run pytest tests/test_rag_pipeline_integration.py -v -s
```

**RAG quick script** (shorter path; same services):

```bash
cd backend
uv run python tests/verify_rag.py
```

## Other suites

Run the full backend test tree:

```bash
cd backend
uv run pytest tests/ -v
```

Some tests may require database or network access depending on your configuration.
