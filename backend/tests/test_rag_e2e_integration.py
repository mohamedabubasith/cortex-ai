"""
End-to-end RAG integration: KB row → ingest (Unstructured + Haystack + Ollama + Qdrant) → DB status → search → cleanup.

Requires live services and a real app database user. Do **not** commit secrets; pass via environment.

Run (example):

  export RUN_RAG_E2E=1
  export DATABASE_URL='postgresql+asyncpg://USER:PASS@HOST:5432/chat_db'
  export UNSTRUCTURED_API_URL='http://unstructured-host/'
  export UNSTRUCTURED_API_KEY='your-key'   # if required
  export OLLAMA_BASE_URL='https://ollama.example/'
  export OLLAMA_MODEL='paraphrase-multilingual:latest'
  export QDRANT_URL='http://qdrant-host:80'   # include port if not 6333
  export QDRANT_COLLECTION='Rag'   # must match your Qdrant collection
  export QDRANT_API_KEY='...'   # if Qdrant is secured
  export INTEGRATION_USER_EMAIL='you@example.com'
  export INTEGRATION_USER_PASSWORD='your-password'

  cd backend && uv run pytest tests/test_rag_e2e_integration.py -v -s

Optional HTTP variant (server must already be running):

  export RUN_RAG_HTTP_E2E=1
  export LIVE_API_BASE_URL='http://localhost:8000'
  # Optional if the user belongs to multiple tenants:
  # export INTEGRATION_TENANT_ID='<uuid>'
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import time
import uuid

import httpx
import pytest

pytestmark = pytest.mark.integration


def _require_env(*names: str) -> dict[str, str]:
    missing = [n for n in names if not os.environ.get(n)]
    if missing:
        pytest.skip(f"Set environment variables: {', '.join(missing)}")
    return {n: os.environ[n] for n in names}


@pytest.mark.asyncio
async def test_rag_kb_ingest_status_and_search_db_path():
    """
    1) Resolve tenant + user from Postgres
    2) Create a KB record + temp document
    3) Run KBService.process_kb (same logic as background worker; uses a live DB session)
    4) Poll DB status until completed (or timeout)
    5) Search via rag_service
    6) Delete KB + vectors + file
    """
    if os.environ.get("RUN_RAG_E2E") != "1":
        pytest.skip("Set RUN_RAG_E2E=1 to enable this test")
    _require_env("INTEGRATION_USER_EMAIL", "INTEGRATION_USER_PASSWORD")

    from sqlalchemy import select

    from app.core.config import settings
    from app.core.database import AsyncSessionLocal
    from app.models import models
    from app.repositories.kb_repository import KBRepository
    from app.services.auth_service import AuthService
    from app.services.kb_service import KBService
    from app.services.rag_service import rag_service

    marker = f"RAG_E2E_MARKER_{uuid.uuid4().hex[:8]}"
    email = os.environ["INTEGRATION_USER_EMAIL"]
    password = os.environ["INTEGRATION_USER_PASSWORD"]

    async with AsyncSessionLocal() as session:
        auth = AuthService(session)
        user = await auth.authenticate_user(email, password)
        if not user:
            pytest.fail("INTEGRATION_USER_EMAIL / INTEGRATION_USER_PASSWORD authentication failed")

        mres = await session.execute(
            select(models.TenantMember).where(models.TenantMember.user_id == user.id).limit(1)
        )
        member = mres.scalars().first()
        if not member:
            pytest.fail("No tenant membership for integration user; ensure user has a default tenant.")
        tenant_id = member.tenant_id

        kb_repo = KBRepository(session)
        kb_svc = KBService(kb_repo)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".txt", delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(
                f"Integration test document.\n"
                f"Unique marker: {marker}\n"
                f"Extra context about renewable energy and battery storage for semantic retrieval.\n"
            )
            file_path = tmp.name

        kb = None
        try:
            kb = await kb_repo.create(
                user_id=user.id,
                filename=f"e2e_{marker}.txt",
                file_path=file_path,
                file_type=".txt",
                file_size=os.path.getsize(file_path),
                chunk_size=512,
                chunk_overlap=64,
                embedding_model=settings.OLLAMA_MODEL,
                status="queued",
                tenant_id=tenant_id,
                parsing_strategy="fast",
            )

            await kb_svc.process_kb(
                kb.id,
                file_path,
                user.id,
                tenant_id,
                512,
                64,
                None,
                settings.OLLAMA_MODEL,
                user_email=user.email,
                enable_graph=False,
            )

            deadline = time.monotonic() + 420.0
            final_status = "unknown"
            while time.monotonic() < deadline:
                st = await kb_svc.get_status(kb.id, user.id, tenant_id, user_email=user.email)
                final_status = (st or {}).get("status", "")
                if final_status == "completed":
                    break
                if final_status == "failed":
                    pytest.fail("KB ingestion failed (status=failed). Check backend logs and remote services.")
                await asyncio.sleep(2.0)

            assert final_status == "completed", f"Timed out waiting for completed status, last={final_status!r}"

            results = await rag_service.search(
                f"What is the unique marker about {marker}?",
                {"kb_id": kb.id},
                llm_config=None,
                embedding_model=kb.embedding_model,
                k=5,
            )
            assert isinstance(results, list)
            assert len(results) >= 1, "Search returned no hits"
            joined = " ".join(r.get("content", "") for r in results)
            assert marker in joined, f"Marker not found in retrieval payload: {joined[:500]!r}"

        finally:
            if kb is not None:
                try:
                    await kb_svc.delete(kb.id, user.id, tenant_id, user_email=user.email)
                except Exception:
                    pass
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except OSError:
                pass


@pytest.mark.asyncio
async def test_rag_http_upload_status_query_live_api():
    """
    Calls a **running** API (LIVE_API_BASE_URL): upload → poll /status → /query.

    Set RUN_RAG_HTTP_E2E=1 and LIVE_API_BASE_URL (e.g. http://127.0.0.1:8000).
    Uses INTEGRATION_USER_EMAIL / INTEGRATION_USER_PASSWORD.
    Optional INTEGRATION_TENANT_ID as X-Tenant-ID when the user has multiple tenants.
    """
    if os.environ.get("RUN_RAG_HTTP_E2E") != "1":
        pytest.skip("Set RUN_RAG_HTTP_E2E=1 to enable HTTP live API test")

    env = _require_env(
        "LIVE_API_BASE_URL",
        "INTEGRATION_USER_EMAIL",
        "INTEGRATION_USER_PASSWORD",
    )
    base = env["LIVE_API_BASE_URL"].rstrip("/")
    email = env["INTEGRATION_USER_EMAIL"]
    password = env["INTEGRATION_USER_PASSWORD"]

    marker = f"HTTP_RAG_{uuid.uuid4().hex[:8]}"
    content = f"HTTP integration KB doc.\nUnique marker: {marker}\nSolar panels and wind turbines.\n"

    async with httpx.AsyncClient(base_url=base, timeout=120.0) as client:
        # Login
        tok = await client.post(
            "/api/v1/auth/token",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert tok.status_code == 200, tok.text
        token = tok.json()["access_token"]

        # Omit X-Tenant-ID when the user has a single tenant — get_current_tenant falls back to first membership.
        headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
        tid = os.environ.get("INTEGRATION_TENANT_ID")
        if tid:
            headers["X-Tenant-ID"] = tid

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
            tmp.write(content)
            path = tmp.name

        kb_id = None
        try:
            with open(path, "rb") as f:
                up = await client.post(
                    "/api/v1/kb/upload",
                    headers=headers,
                    files={"file": (f"http_e2e_{marker}.txt", f, "text/plain")},
                    data={
                        "chunk_size": "512",
                        "chunk_overlap": "64",
                        "parsing_strategy": "fast",
                        "enable_graph": "false",
                    },
                )
            assert up.status_code == 200, up.text
            kb_id = up.json()["id"]

            deadline = time.monotonic() + 420.0
            status_val = ""
            while time.monotonic() < deadline:
                st = await client.get(f"/api/v1/kb/{kb_id}/status", headers=headers)
                assert st.status_code == 200, st.text
                status_val = st.json().get("status", "")
                if status_val == "completed":
                    break
                if status_val == "failed":
                    pytest.fail("Remote API reported failed ingestion status")
                await asyncio.sleep(2.0)

            assert status_val == "completed", f"status poll timeout, last={status_val!r}"

            q = await client.post(
                f"/api/v1/kb/{kb_id}/query",
                headers=headers,
                json={"query": f"What is the unique marker {marker}?"},
            )
            assert q.status_code == 200, q.text
            body = q.json()
            assert body.get("success") is True
            rows = body.get("data") or []
            assert len(rows) >= 1
            blob = " ".join(str(r.get("content", "")) for r in rows)
            assert marker in blob

        finally:
            if kb_id:
                try:
                    await client.delete(f"/api/v1/kb/{kb_id}", headers=headers)
                except Exception:
                    pass
            try:
                os.unlink(path)
            except OSError:
                pass
