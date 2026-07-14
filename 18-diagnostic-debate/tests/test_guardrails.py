# tests/test_guardrails.py
"""This system produces RESEARCH output only -- never a
clinical action, never a treatment plan. That must be a
structural property of the graph, not merely a prompt
instruction: these tests prove it without touching a real
model or a real Anthropic key."""
from __future__ import annotations

import inspect

from panel.graph import build_graph, clinician_review_node
from panel.nodes import (
    analyze as analyze_mod,
    bias_check as bias_check_mod,
    debate as debate_mod,
    intake as intake_mod,
    order_tests as order_tests_mod,
    steward as steward_mod,
)

NODE_MODULES = (
    analyze_mod, bias_check_mod, debate_mod,
    intake_mod, order_tests_mod, steward_mod,
)

FORBIDDEN_TERMS = (
    "prescribe", "prescription", "dosage", "dose_mg",
    "administer", "treatment_plan", "start_medication",
)


def test_no_node_can_reach_end_except_clinician_review():
    """Structural check: 'clinician_review' -> END is the
    only edge into END, so no path through the panel can
    close a run without a human in the loop."""
    graph = build_graph()
    edges = graph.get_graph().edges
    into_end = [e for e in edges if e.target == "__end__"]
    assert len(into_end) == 1
    assert into_end[0].source == "clinician_review"


def test_no_node_module_names_a_treatment_action():
    """Static check: none of the reasoning/debate/steward
    modules contain treatment or prescribing language --
    this is a differential-diagnosis research tool, and it
    has no vocabulary for clinical action."""
    for mod in NODE_MODULES:
        src = open(mod.__file__).read().lower()
        for term in FORBIDDEN_TERMS:
            assert term not in src, (
                f"{mod.__name__} contains forbidden "
                f"clinical-action term {term!r}")


def test_only_clinician_review_calls_interrupt():
    """Static check: none of the reasoning nodes can pause
    for (or bypass) human review on their own -- only the
    dedicated clinician_review step holds the interrupt()
    that gates every run."""
    for mod in NODE_MODULES:
        src = open(mod.__file__).read()
        assert "interrupt(" not in src

    graph_src = inspect.getsource(clinician_review_node)
    assert "interrupt(" in graph_src


def test_clinician_review_carries_the_research_only_notice():
    """The payload a clinician sees at the gate must say,
    in plain language, that this is not a diagnosis or a
    treatment plan and must never be used on a real
    patient."""
    state = {
        "final_differential": [],
        "bias_flags": [],
        "cost_total": 0.0,
        "cost_note": "",
    }
    # interrupt() raises inside a real graph run; called
    # directly here we only need to inspect what payload
    # it was about to send, so patch it to capture instead.
    captured = {}

    def _fake_interrupt(payload):
        captured.update(payload)
        return {"reviewed": True}

    import panel.graph as graph_mod
    original = graph_mod.interrupt
    graph_mod.interrupt = _fake_interrupt
    try:
        graph_mod.clinician_review_node(state)
    finally:
        graph_mod.interrupt = original

    notice = captured["notice"].lower()
    assert "not a diagnosis" in notice
    assert "not a treatment plan" in notice
    assert "real patient" in notice


def test_app_review_response_repeats_the_notice():
    """Static check: the API's /review handler must echo
    the research-only notice back on every response, not
    just at the interrupt payload."""
    import panel.app as app_mod
    src = inspect.getsource(app_mod.review)
    assert "RESEARCH OUTPUT ONLY" in src
