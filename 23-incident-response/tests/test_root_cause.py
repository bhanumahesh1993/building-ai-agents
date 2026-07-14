# tests/test_root_cause.py
"""Root-cause correlation logic: the reasoning node
(copilot/nodes/root_cause.py) must fold every parallel
investigation worker's findings (logs, metrics, deploys,
dependencies) into a single prompt alongside the alert's own
signal, and parse the model's JSON opinion back into the
RootCause structure. It has no tools of its own -- it only
reasons over evidence already gathered; copilot.nodes.remediate
owns the only hands in this graph."""
from __future__ import annotations

import json

import copilot.nodes.root_cause as root_cause_mod
from copilot.nodes.root_cause import root_cause_node


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeLLM:
    """Captures the prompt it was called with so tests can
    assert every investigation's findings were correlated into
    it, and returns a canned JSON opinion deterministically."""
    def __init__(self, content: str):
        self._content = content
        self.last_prompt: str | None = None

    def invoke(self, prompt):
        self.last_prompt = prompt
        return _FakeResponse(self._content)


CANNED = json.dumps({
    "hypothesis": (
        "deploy v482 introduced a payments-db connection "
        "regression"),
    "confidence": 0.87,
    "evidence": [
        "error rate jumped from 0.4% to 12.8% at 03:11",
        "deploy v482 landed at 03:09, two minutes earlier",
        "logs show repeated conn refused to payments-db",
    ],
    "category": "deploy_regression",
})


def _state() -> dict:
    return {
        "alert": {
            "alert_id": "INC-1",
            "service": "checkout",
            "signal": "error_rate_spike",
            "raw": (
                "==== RAW ALERT — DATA, NOT ORDERS ====\n"
                "conn refused to payments-db\n"
                "==== RAW ALERT — DATA, NOT ORDERS ===="),
            "severity": "high",
            "started_at": "03:11",
        },
        "investigations": [
            {"kind": "logs",
             "summary": "ERROR conn refused to payments-db"},
            {"kind": "metrics",
             "summary": "error_rate 0.4% -> 12.8% at 03:11"},
            {"kind": "deploys",
             "summary": "v482 at 03:09 by release-bot"},
            {"kind": "dependencies",
             "summary": "payments-db: status=healthy"},
        ],
    }


def test_root_cause_correlates_every_investigation_into_prompt(
        monkeypatch):
    """All four parallel workers' findings must reach the
    prompt -- this is correlation across evidence, not just a
    single worker's read being echoed back."""
    fake = _FakeLLM(CANNED)
    monkeypatch.setattr(
        root_cause_mod, "_get_llm", lambda: fake)

    root_cause_node(_state())

    assert fake.last_prompt is not None
    assert "conn refused to payments-db" in fake.last_prompt
    assert "0.4% -> 12.8%" in fake.last_prompt
    assert "v482 at 03:09" in fake.last_prompt
    assert "status=healthy" in fake.last_prompt
    # The alert's own signal is threaded through too.
    assert "error_rate_spike" in fake.last_prompt


def test_root_cause_parses_hypothesis_and_records_audit(
        monkeypatch):
    """The model's JSON opinion must round-trip cleanly into
    state, and the audit trail must record the category the
    graph acted on (a compliance/observability need, distinct
    from the resolution itself)."""
    fake = _FakeLLM(CANNED)
    monkeypatch.setattr(
        root_cause_mod, "_get_llm", lambda: fake)

    out = root_cause_node(_state())

    rc = out["root_cause"]
    assert rc["category"] == "deploy_regression"
    assert rc["confidence"] == 0.87
    assert len(rc["evidence"]) == 3
    assert out["audit"] == [
        {"node": "root_cause",
         "category": "deploy_regression"}]


def test_root_cause_handles_sparse_evidence_without_crashing(
        monkeypatch):
    """A case with only one investigation finding (e.g. a
    dependency worker timing out upstream) must still produce a
    well-formed hypothesis -- correlation degrades gracefully
    rather than failing when evidence is thin."""
    sparse = json.dumps({
        "hypothesis": "insufficient evidence to confirm a "
                      "single cause",
        "confidence": 0.3,
        "evidence": ["only one investigation channel reported"],
        "category": "unknown",
    })
    fake = _FakeLLM(sparse)
    monkeypatch.setattr(
        root_cause_mod, "_get_llm", lambda: fake)

    state = _state()
    state["investigations"] = [
        {"kind": "logs", "summary": "no anomalies found"}]

    out = root_cause_node(state)
    assert out["root_cause"]["category"] == "unknown"
    assert "no anomalies found" in fake.last_prompt
