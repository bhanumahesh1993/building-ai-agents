# tests/test_dedup.py
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

from crew import tools


def _fake_embedding_response(vec: list[float]) -> MagicMock:
    resp = MagicMock()
    resp.data = [MagicMock(embedding=vec)]
    return resp


def _fake_connection(row) -> MagicMock:
    """A context-manager-compatible stand-in for
    psycopg.connect(...) whose .execute(...).fetchone()
    returns a fixed row."""
    conn = MagicMock()
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = False
    conn.execute.return_value.fetchone.return_value = row
    return conn


def test_dedup_check_flags_known_duplicate_pair(monkeypatch):
    """Deterministic: with a mocked embedder and a mocked
    pgvector lookup reporting similarity above threshold,
    the reissued advisory must be flagged as a duplicate
    of the original - the exact pair evals/dedup_check_eval.py
    exercises against a live embedder and database."""
    fake_client = MagicMock()
    fake_client.embeddings.create.return_value = (
        _fake_embedding_response([0.1] * 1536))
    monkeypatch.setattr(tools, "_openai", fake_client)

    fake_conn = _fake_connection(("CVE-2026-1042", 0.97))

    with patch.object(tools.psycopg, "connect",
                      return_value=fake_conn), \
         patch.object(tools, "register_vector"):
        result = tools.dedup_check.func(
            "CVE-2026-1042-R",
            "Reissued advisory: auth bypass in the VPN "
            "gateway admin portal via session cookie.")

    assert result["cve_id"] == "CVE-2026-1042-R"
    assert result["is_duplicate"] is True
    assert result["duplicate_of"] == "CVE-2026-1042"
    assert result["similarity"] == 0.97


def test_dedup_check_below_threshold_is_not_duplicate(
        monkeypatch):
    """A near-but-not-similar-enough match must not be
    flagged - the threshold guard, not just the presence
    of a prior row, decides duplication."""
    fake_client = MagicMock()
    fake_client.embeddings.create.return_value = (
        _fake_embedding_response([0.1] * 1536))
    monkeypatch.setattr(tools, "_openai", fake_client)

    fake_conn = _fake_connection(("CVE-2026-1001", 0.40))

    with patch.object(tools.psycopg, "connect",
                      return_value=fake_conn), \
         patch.object(tools, "register_vector"):
        result = tools.dedup_check.func(
            "CVE-2026-1077",
            "Privilege escalation via a crafted extension "
            "load path.")

    assert result["is_duplicate"] is False
    assert result["duplicate_of"] is None
    assert result["similarity"] == 0.40


def test_dedup_check_no_prior_rows_is_not_duplicate(
        monkeypatch):
    """An empty advisories table (no prior row at all)
    must resolve to not-a-duplicate, not raise."""
    fake_client = MagicMock()
    fake_client.embeddings.create.return_value = (
        _fake_embedding_response([0.1] * 1536))
    monkeypatch.setattr(tools, "_openai", fake_client)

    fake_conn = _fake_connection(None)

    with patch.object(tools.psycopg, "connect",
                      return_value=fake_conn), \
         patch.object(tools, "register_vector"):
        result = tools.dedup_check.func(
            "CVE-2026-1001", "Heap overflow in libimage.")

    assert result["is_duplicate"] is False
    assert result["duplicate_of"] is None
    assert result["similarity"] == 0.0


@pytest.mark.skipif(
    not (os.getenv("OPENAI_API_KEY")
         and os.getenv("DATABASE_URL")),
    reason="requires a live OpenAI key and a reachable "
           "pgvector database")
def test_dedup_check_live_duplicate_pair():
    """Integration check against the real embedder and a
    live pgvector database - mirrors what
    evals/dedup_check_eval.py runs. Skipped unless both
    OPENAI_API_KEY and DATABASE_URL are set."""
    from evals.dedup_check_eval import dedup_accuracy
    result = dedup_accuracy()
    assert result["accuracy"] == 1.0
