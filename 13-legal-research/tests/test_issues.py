# tests/test_issues.py
from __future__ import annotations

import importlib.util
import json
import os

import anyio
import pytest

from research import issues
from research.issues import _parse_issues_response

HAS_SDK = importlib.util.find_spec("claude_agent_sdk") is not None
HAS_KEY = bool(os.environ.get("ANTHROPIC_API_KEY"))
requires_live_api = pytest.mark.skipif(
    not (HAS_SDK and HAS_KEY),
    reason="requires claude-agent-sdk installed and "
    "ANTHROPIC_API_KEY set for a live model call",
)

SAMPLE_RESPONSE = json.dumps({
    "issues": [
        {"id": "noncompete_enforceability",
         "question": "Is the non-compete enforceable "
         "under NY law?",
         "keywords": ["non-compete", "restraint of trade"]},
        {"id": "trade_secret_misappropriation",
         "question": "Did the engineer misappropriate "
         "trade secrets?",
         "keywords": ["trade secret", "misappropriation"]},
        {"id": "breach_of_contract",
         "question": "Was the employment contract "
         "breached?",
         "keywords": ["breach", "contract"]},
        {"id": "tortious_interference",
         "question": "Did the competitor tortiously "
         "interfere?",
         "keywords": ["tortious interference"]},
        {"id": "unjust_enrichment",
         "question": "Was the competitor unjustly "
         "enriched?",
         "keywords": ["unjust enrichment"]},
    ]
})


def test_decomposes_into_distinct_issues():
    """Each issue must be independently answerable and
    distinct -- no duplicates, no merging of questions."""
    result = _parse_issues_response(SAMPLE_RESPONSE, max_issues=4)
    ids = [i["id"] for i in result]
    assert len(ids) == len(set(ids))


def test_each_issue_has_required_shape():
    result = _parse_issues_response(SAMPLE_RESPONSE, max_issues=4)
    for issue in result:
        assert {"id", "question", "keywords"} <= set(issue)
        assert issue["question"].strip()
        assert isinstance(issue["keywords"], list)


def test_respects_max_issues_cap():
    """The model returned 5 issues; the fan-out contract
    caps it at MAX_ISSUES regardless."""
    result = _parse_issues_response(
        SAMPLE_RESPONSE, max_issues=issues.MAX_ISSUES)
    assert len(result) == issues.MAX_ISSUES == 4


def test_default_cap_matches_module_constant():
    result = _parse_issues_response(SAMPLE_RESPONSE)
    assert len(result) == issues.MAX_ISSUES


@requires_live_api
def test_spot_issues_live():
    """End-to-end decomposition through the real Claude
    Agent SDK. Skipped unless claude-agent-sdk is
    installed and ANTHROPIC_API_KEY is set."""
    result = anyio.run(
        issues.spot_issues,
        "An engineer signed a one-year non-compete when "
        "hired, then joined a direct competitor eight "
        "months later.",
        "NY",
    )
    assert result
    assert len(result) <= issues.MAX_ISSUES
