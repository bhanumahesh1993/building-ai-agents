# tests/test_steward.py
"""Cost-steward logic, fully deterministic: the steward LLM
is faked so these tests prove panel.nodes.steward's own
selection/reporting logic, not the model's commentary.
The steward must never order tests or touch the
differential's confidences -- it only reports and picks the
top 3 active hypotheses to hand to the clinician."""
from __future__ import annotations

from panel.nodes import steward as steward_mod


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeStewardLLM:
    def __init__(self, content: str):
        self._content = content

    def invoke(self, prompt):
        return _FakeResponse(self._content)


OVER_CAP_NOTE = (
    '{"note": "Spend exceeded the cap; the MRI added little '
    'discriminating value over the cheaper x-ray."}'
)


def _state(**over):
    base = {
        "orders": [
            {"test": "cbc", "rationale": "r", "cost_usd": 15},
            {"test": "mri_joint", "rationale": "r",
             "cost_usd": 900},
        ],
        "cost_total": 915.0,
        "cost_cap": 500.0,
        "hypotheses": [
            {"name": "lupus", "rationale": "r",
             "confidence": 0.8, "status": "active"},
            {"name": "lyme disease", "rationale": "r",
             "confidence": 0.3, "status": "active"},
            {"name": "gout", "rationale": "r",
             "confidence": 0.6, "status": "active"},
            {"name": "reactive arthritis", "rationale": "r",
             "confidence": 0.9, "status": "retired"},
            {"name": "viral arthritis", "rationale": "r",
             "confidence": 0.5, "status": "active"},
        ],
    }
    base.update(over)
    return base


def test_final_differential_is_top_three_active_by_confidence(
        monkeypatch):
    monkeypatch.setattr(
        steward_mod, "_get_llm",
        lambda: _FakeStewardLLM(OVER_CAP_NOTE))

    out = steward_mod.steward_node(_state())

    names = [h["name"] for h in out["final_differential"]]
    assert names == ["lupus", "gout", "viral arthritis"]
    assert len(out["final_differential"]) == 3
    # A retired hypothesis must never reach the final
    # differential even if its confidence was highest.
    assert "reactive arthritis" not in names


def test_steward_reports_cost_note_verbatim(monkeypatch):
    monkeypatch.setattr(
        steward_mod, "_get_llm",
        lambda: _FakeStewardLLM(OVER_CAP_NOTE))

    out = steward_mod.steward_node(_state())

    assert "exceeded the cap" in out["cost_note"]


def test_steward_never_orders_tests_or_edits_confidence(
        monkeypatch):
    """The steward's return value must only ever contain the
    final differential and its cost commentary -- never an
    'orders' key or a rewritten confidence, proving it cannot
    order tests or move the differential on its own."""
    monkeypatch.setattr(
        steward_mod, "_get_llm",
        lambda: _FakeStewardLLM(OVER_CAP_NOTE))

    state = _state()
    original_confidences = {
        h["name"]: h["confidence"] for h in state["hypotheses"]}
    out = steward_mod.steward_node(state)

    assert set(out.keys()) == {"final_differential", "cost_note"}
    for h in out["final_differential"]:
        assert h["confidence"] == original_confidences[h["name"]]


def test_fewer_than_three_active_hypotheses_returns_all_of_them(
        monkeypatch):
    monkeypatch.setattr(
        steward_mod, "_get_llm",
        lambda: _FakeStewardLLM(OVER_CAP_NOTE))

    state = _state(hypotheses=[
        {"name": "lupus", "rationale": "r",
         "confidence": 0.8, "status": "active"},
        {"name": "gout", "rationale": "r",
         "confidence": 0.9, "status": "retired"},
    ])
    out = steward_mod.steward_node(state)

    assert [h["name"] for h in out["final_differential"]] == \
        ["lupus"]
