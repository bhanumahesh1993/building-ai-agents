# tests/test_workflow.py — gap-to-hypothesis pipeline structure.
#
# Every ADK agent call goes through workflow._run_agent, so we fake
# that one seam (keyed on agent.name) and the corpus/search seam.
# This exercises the real data-flow logic in run_review() -- cluster
# fan-out, contradiction->debate wiring, gap->hypothesis assembly,
# and the citation/hedge guardrails -- with zero network calls and
# zero API keys, while still constructing real google-adk Agent
# objects (which is cheap and keyless; see lit_review/agents.py).
from __future__ import annotations

import asyncio
import importlib.util
import json

import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("google.adk") is None,
    reason="google-adk is not installed/importable",
)

import lit_review.workflow as workflow  # noqa: E402


def _fake_search_corpus(queries, k=10):
    return [
        {"id": "2501.00001", "title": "Paper A",
         "abstract": "...", "cluster_id": 0, "dist": 0.1},
        {"id": "2501.00002", "title": "Paper B",
         "abstract": "...", "cluster_id": 0, "dist": 0.2},
    ]


async def _fake_run_agent(agent, message):
    name = agent.name
    if name == "query_planner":
        return {"queries": json.dumps({"queries": ["q1", "q2"]})}
    if name == "summarize_fanout":
        return {"summary_0": "Cluster 0 discusses [2501.00001]."}
    if name == "contradiction_scout":
        return {"contradictions": json.dumps({"contradictions": [
            {"paper_a": "2501.00001", "claim_a": "X causes Y",
             "paper_b": "2501.00002", "claim_b": "X does not cause Y",
             "question": "Does X cause Y?"},
        ]})}
    if name == "debate_loop":
        return {"verdict": json.dumps({
            "resolved": True,
            "verdict": "Difference in population, not a true conflict.",
            "confidence": 0.7,
        })}
    if name == "gaps_to_hypotheses":
        return {
            "gaps": json.dumps({"gaps": [
                {"topic": "long-term effects", "why": "flagged as "
                 "future work", "evidence": ["2501.00001"]},
            ]}),
            # The bracketed [id] here is the mechanical citation the
            # regex-based guard in tools.validate_citations checks for
            # -- the "citations" list is separate model-output structure.
            "hypotheses": json.dumps({"hypotheses": [
                {"question": "Might X have long-term effects on Y?",
                 "rationale": "This may suggest a lasting effect, as "
                 "hinted by [2501.00001], and warrants investigation.",
                 "citations": ["2501.00001"],
                 "test": "a longitudinal cohort study"},
            ]}),
        }
    raise AssertionError(f"unexpected agent in fake harness: {name}")


def test_run_review_assembles_gap_to_hypothesis_structure(monkeypatch):
    monkeypatch.setattr(
        workflow, "get_known_ids",
        lambda: {"2501.00001", "2501.00002"})
    monkeypatch.setattr(workflow, "search_corpus", _fake_search_corpus)
    monkeypatch.setattr(workflow, "_run_agent", _fake_run_agent)

    result = asyncio.run(workflow.run_review("does X cause Y"))

    assert result["topic"] == "does X cause Y"
    assert set(result["summaries"].keys()) == {"summary_0"}

    assert len(result["contradictions"]) == 1
    verdict = result["contradictions"][0]
    assert verdict["resolved"] is True
    assert verdict["dispute"]["paper_a"] == "2501.00001"
    assert verdict["dispute"]["paper_b"] == "2501.00002"

    assert len(result["gaps"]) == 1
    assert result["gaps"][0]["topic"] == "long-term effects"

    assert len(result["hypotheses"]) == 1
    hyp = result["hypotheses"][0]
    assert hyp["citations"] == ["2501.00001"]
    assert "test" in hyp and "question" in hyp

    # Guardrails run in code after the model, on the raw hypotheses
    # JSON -- confirm both fired and read the same grounded citation.
    assert result["citation_guard"]["clean"] is True
    assert result["citation_guard"]["cited"] == ["2501.00001"]
    assert result["hedge_guard"]["hedged"] is True
    assert result["hedge_guard"]["ok"] is True


def test_run_review_flags_ungrounded_hypothesis_citation(monkeypatch):
    """If a hypothesis cites an ID outside the corpus allow-list,
    the citation guard must catch it -- this is the grounding
    contract the whole gap->hypothesis step exists to enforce."""
    monkeypatch.setattr(
        workflow, "get_known_ids", lambda: {"2501.00001"})
    monkeypatch.setattr(workflow, "search_corpus", _fake_search_corpus)

    async def run_agent_with_bad_citation(agent, message):
        base = await _fake_run_agent(agent, message)
        if agent.name == "gaps_to_hypotheses":
            base["hypotheses"] = json.dumps({"hypotheses": [
                {"question": "Could Z explain this too?",
                 "rationale": "This may suggest a confound, per "
                 "[9999.99999], and warrants investigation.",
                 "citations": ["9999.99999"],
                 "test": "a replication study"},
            ]})
        return base

    monkeypatch.setattr(
        workflow, "_run_agent", run_agent_with_bad_citation)

    result = asyncio.run(workflow.run_review("does X cause Y"))

    assert result["citation_guard"]["clean"] is False
    assert result["citation_guard"]["hallucinated"] == ["9999.99999"]
