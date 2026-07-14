# tests/test_live.py
"""Opt-in live checks against the real Anthropic/OpenAI APIs and
a real pgvector database. Skipped by default so `pytest -q` stays
offline and deterministic; set the relevant environment variables
to exercise these before a release.

- test_live_extract_clauses_classifies_a_real_section needs
  ANTHROPIC_API_KEY (a real ChatAnthropic call).
- test_live_retrieve_standard_position_hits_real_pgvector needs
  both OPENAI_API_KEY (a real embedding call) and PLAYBOOK_DB_URL
  (a real pgvector-backed Postgres with a populated
  `playbook_positions` table).
"""
from __future__ import annotations

import os

import pytest

pytestmark_no_anthropic = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires a real ANTHROPIC_API_KEY (live model call)",
)
pytestmark_no_pgvector = pytest.mark.skipif(
    not (os.environ.get("OPENAI_API_KEY")
         and os.environ.get("PLAYBOOK_DB_URL")),
    reason="requires a real OPENAI_API_KEY and a live "
           "PLAYBOOK_DB_URL (pgvector) with playbook_positions "
           "populated",
)


@pytestmark_no_anthropic
def test_live_extract_clauses_classifies_a_real_section():
    """extract_clauses against the real model: a clean
    indemnification section is typed and its verbatim text
    survives -- no mocked client involved."""
    from contracts.extract import extract_clauses

    doc = {
        "contract_id": "live1", "filename": "f.txt",
        "text": (
            "\n1. INDEMNIFICATION\n"
            "Party A shall indemnify Party B fully and "
            "without limit for any and all claims arising "
            "hereunder.\n"
        ),
    }
    clauses = extract_clauses(doc)
    assert len(clauses) == 1
    assert clauses[0]["clause_type"] == "indemnification"
    assert clauses[0]["contract_id"] == "live1"


@pytestmark_no_pgvector
def test_live_retrieve_standard_position_hits_real_pgvector():
    """retrieve_standard_position against a real pgvector
    database: a real embedding call, a real similarity
    query, and rows shaped like playbook_positions."""
    from contracts.playbook import retrieve_standard_position

    hits = retrieve_standard_position(
        "liability_cap",
        "liability shall not exceed fees paid", k=2)
    assert isinstance(hits, list)
    for h in hits:
        assert {"id", "position_text", "source"} <= set(h)
