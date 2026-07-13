# tests/test_synthesize.py
from __future__ import annotations

import importlib.util
import json
import os

import anyio
import pytest

from research.synthesize import (
    REQUIRED_KEYS, _parse_synthesis_response,
)

HAS_SDK = importlib.util.find_spec("claude_agent_sdk") is not None
HAS_KEY = bool(os.environ.get("ANTHROPIC_API_KEY"))
requires_live_api = pytest.mark.skipif(
    not (HAS_SDK and HAS_KEY),
    reason="requires claude-agent-sdk installed and "
    "ANTHROPIC_API_KEY set for a live model call",
)

VALID_RESPONSE = json.dumps({
    "issue_id": "noncompete_enforceability",
    "for": "The restraint is reasonable in scope and "
    "duration and protects a legitimate interest.",
    "for_cites": [{"case_id": "case_001",
                   "claim": "one-year restraints are "
                   "reasonable"}],
    "against": "The restraint is broader than necessary "
    "to protect any legitimate business interest.",
    "against_cites": [{"case_id": "case_002",
                       "claim": "overbroad restraints "
                       "are unenforceable"}],
    "weight": "favors enforceability",
})


def test_valid_response_round_trips():
    parsed = _parse_synthesis_response(VALID_RESPONSE)
    assert set(REQUIRED_KEYS) <= set(parsed)
    assert parsed["for"] and parsed["against"]


def test_missing_against_side_is_rejected():
    """Argument-balance: both sides are structurally
    required, not optional."""
    bad = json.loads(VALID_RESPONSE)
    del bad["against"]
    with pytest.raises(ValueError):
        _parse_synthesis_response(json.dumps(bad))


def test_one_sided_argument_is_rejected():
    """A model that gives up on one side must not
    silently pass through as balanced."""
    bad = json.loads(VALID_RESPONSE)
    bad["against"] = ""
    with pytest.raises(ValueError):
        _parse_synthesis_response(json.dumps(bad))


def test_missing_citation_list_is_rejected():
    bad = json.loads(VALID_RESPONSE)
    del bad["for_cites"]
    with pytest.raises(ValueError):
        _parse_synthesis_response(json.dumps(bad))


def test_missing_weight_is_rejected():
    bad = json.loads(VALID_RESPONSE)
    del bad["weight"]
    with pytest.raises(ValueError):
        _parse_synthesis_response(json.dumps(bad))


@requires_live_api
def test_synthesize_issue_live():
    """End-to-end argument synthesis through the real
    Claude Agent SDK. Skipped unless claude-agent-sdk is
    installed and ANTHROPIC_API_KEY is set."""
    from research.synthesize import synthesize_issue

    finding = {
        "issue_id": "noncompete_enforceability",
        "summary": "Some cases upheld similar one-year "
        "restraints as reasonable; others struck down "
        "broader restraints as overbroad.",
    }
    result = anyio.run(synthesize_issue, finding)
    assert result["for"] and result["against"]
