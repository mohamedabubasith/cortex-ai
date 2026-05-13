"""Lightweight KB unit tests (Haystack filter mapping)."""

import uuid

import pytest

from app.services.rag_service import RAGService


def test_filter_single_kb_id():
    kid = str(uuid.uuid4())
    flt = RAGService._legacy_filter_to_haystack({"kb_id": kid})
    assert flt["operator"] == "AND"
    assert flt["conditions"][0]["value"] == kid


def test_filter_kb_id_in_operator():
    ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    flt = RAGService._legacy_filter_to_haystack({"kb_id": {"$in": ids}})
    assert flt["operator"] == "OR"
    vals = {c["value"] for c in flt["conditions"]}
    assert vals == set(ids)
