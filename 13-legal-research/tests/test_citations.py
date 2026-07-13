# tests/test_citations.py
from __future__ import annotations

import importlib.util
import json
import os

import anyio
import pytest

from research import citations

HAS_SDK = importlib.util.find_spec("claude_agent_sdk") is not None
HAS_KEY = bool(os.environ.get("ANTHROPIC_API_KEY"))
requires_live_api = pytest.mark.skipif(
    not (HAS_SDK and HAS_KEY),
    reason="requires claude-agent-sdk installed and "
    "ANTHROPIC_API_KEY set for a live model call",
)


def test_missing_case_is_always_stripped(monkeypatch):
    monkeypatch.setattr(
        citations, "case_exists", lambda cid: None)

    async def _run():
        return await citations.verify_citations(
            [{"case_id": "fake_001",
              "claim": "anything at all"}])

    result = anyio.run(_run)
    assert result[0]["status"] == "stripped"
    assert "not found" in result[0]["reason"]


def test_real_case_reaches_tier_two(monkeypatch):
    monkeypatch.setattr(
        citations, "case_exists",
        lambda cid: {"case_id": cid,
                      "case_name": "Bellweather v. Okafor",
                      "citation": "1 N.Y.3d 1"})
    monkeypatch.setattr(
        citations, "case_full_text",
        lambda cid: "the restraint was reasonable")

    async def _fake_tier2(claim, case_id):
        return "reasonable" in (
            citations.case_full_text(case_id))

    monkeypatch.setattr(
        citations, "_tier2_supports", _fake_tier2)

    async def _run():
        return await citations.verify_citations(
            [{"case_id": "real_001",
              "claim": "the restraint was reasonable"}])

    result = anyio.run(_run)
    assert result[0]["status"] == "verified"


def test_real_case_that_does_not_support_claim_is_flagged(
        monkeypatch):
    """Verify-or-strip, tier 2: a real case that does not
    actually back the claim must be flagged, never passed
    through as verified -- this is the legal-safety
    guarantee the whole module exists to enforce."""
    monkeypatch.setattr(
        citations, "case_exists",
        lambda cid: {"case_id": cid,
                      "case_name": "Bellweather v. Okafor",
                      "citation": "1 N.Y.3d 1"})
    monkeypatch.setattr(
        citations, "case_full_text",
        lambda cid: "the court declined to address "
        "the scope of the restraint at all")

    async def _fake_tier2(claim, case_id):
        return "reasonable" in (
            citations.case_full_text(case_id))

    monkeypatch.setattr(
        citations, "_tier2_supports", _fake_tier2)

    async def _run():
        return await citations.verify_citations(
            [{"case_id": "real_002",
              "claim": "the restraint was reasonable"}])

    result = anyio.run(_run)
    assert result[0]["status"] == "flagged"
    assert "does not clearly support" in result[0]["reason"]


def test_parse_judge_response_reads_supported_flag():
    """Pure parsing logic for the tier-2 judge reply --
    no SDK, no network, no credentials required."""
    assert citations._parse_judge_response(
        json.dumps({"supported": True, "reason": "ok"})
    ) is True
    assert citations._parse_judge_response(
        json.dumps({"supported": False, "reason": "no"})
    ) is False


@requires_live_api
def test_tier2_supports_live(monkeypatch):
    """End-to-end tier-2 check through the real Claude
    Agent SDK (no corpus database required -- the case
    text is stubbed so this test only needs a key, not a
    live corpus; the full pipeline additionally needs
    CASE_DB_URL). Skipped unless claude-agent-sdk is
    installed and ANTHROPIC_API_KEY is set."""
    monkeypatch.setattr(
        citations, "case_full_text",
        lambda cid: "the sky is blue on a clear day")
    result = anyio.run(
        citations._tier2_supports,
        "the sky is blue",
        "irrelevant_case_id",
    )
    assert isinstance(result, bool)
