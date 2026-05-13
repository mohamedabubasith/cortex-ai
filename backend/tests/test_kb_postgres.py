"""
Placeholder module for future PostgreSQL-backed KB API tests.

Haystack ingestion is covered by integration tests when RUN_KB_INTEGRATION=1
(see tests/test_rag_langchain.py). PostgreSQL-specific API tests belong in a
dedicated suite with auth fixtures aligned to /api/v1/kb routes.
"""

import pytest


@pytest.mark.skip(reason="Replaced by Haystack pipeline; add PG-backed API tests separately if needed.")
def test_kb_postgres_placeholder():
    assert True
