# tests/test_live.py
"""Opt-in live checks against the real Anthropic API.
Skipped by default so `pytest -q` stays offline and
deterministic; set ANTHROPIC_API_KEY to exercise these
before a release.

Reminder: even live, this is a research reproduction --
synthetic vignettes only, never a real patient."""
from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires a real ANTHROPIC_API_KEY (live model call)",
)

SYNTHETIC_VIGNETTE = (
    "==== SYNTHETIC RESEARCH VIGNETTE -- NOT A REAL PATIENT ====\n"
    "A 34-year-old presents with 3 weeks of migratory joint "
    "pain (wrists, knees), a malar rash worse in sunlight, and "
    "intermittent low-grade fever. No recent travel, no tick "
    "exposure reported.\n"
    "==== SYNTHETIC RESEARCH VIGNETTE -- NOT A REAL PATIENT ===="
)


def test_live_intake_extracts_findings_as_json():
    from panel.nodes.intake import intake_node

    out = intake_node({"vignette": SYNTHETIC_VIGNETTE})
    assert isinstance(out["findings"], list)
    assert len(out["findings"]) > 0
    assert out["round"] == 0


def test_live_analyze_produces_bounded_hypotheses():
    from panel.nodes.analyze import analyze_node

    findings = [
        "migratory joint pain in wrists and knees",
        "malar rash worse in sunlight",
        "intermittent low-grade fever",
    ]
    out = analyze_node({"findings": findings})
    hyps = out["hypotheses"]
    assert 1 <= len(hyps) <= 5
    for h in hyps:
        assert h["status"] == "active"
        assert 0.0 <= h["confidence"] <= 1.0


def test_live_full_graph_pauses_for_clinician_review():
    """End-to-end with the real model: the graph must always
    stop at the clinician_review interrupt, and the response
    on decline must never claim to be more than research
    output."""
    import uuid

    from langgraph.types import Command
    from panel.graph import build_graph

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = graph.invoke({
        "vignette": SYNTHETIC_VIGNETTE,
        "available_results": {},
        "max_rounds": 2,
        "cost_cap": 200.0,
    }, config=cfg)

    assert "__interrupt__" in state
    payload = state["__interrupt__"][0].value
    assert "not a diagnosis" in payload["notice"].lower()

    state = graph.invoke(
        Command(resume={"reviewed": True}), config=cfg)
    assert state["approved"] is True
    assert isinstance(state["final_differential"], list)
