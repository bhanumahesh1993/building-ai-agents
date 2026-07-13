# tests/test_citations.py
from __future__ import annotations

import anyio

from research import citations


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
