# tests/test_bias_check.py
"""Bias-check logic, fully deterministic: the bias-auditor
LLM is faked so these tests prove the recheck-cap wiring in
panel.nodes.bias_check, not the model's judgment."""
from __future__ import annotations

from panel.nodes import bias_check as bias_check_mod


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeBiasLLM:
    """Returns a fixed flags JSON blob regardless of prompt."""
    def __init__(self, content: str):
        self._content = content

    def invoke(self, prompt):
        return _FakeResponse(self._content)


ANCHORING_ON_LEADER = (
    '{"flags": [{"kind": "anchoring", "target": "lupus", '
    '"note": "leader was first proposed, objections unresolved"}]}'
)

NO_FLAGS = '{"flags": []}'


def _state(**over):
    base = {
        "hypotheses": [
            {"name": "lupus", "rationale": "r",
             "confidence": 0.8, "status": "active"},
            {"name": "lyme disease", "rationale": "r",
             "confidence": 0.3, "status": "active"},
        ],
        "arguments": [
            {"hypothesis": "lupus", "stance": "support",
             "text": "t", "round": 0},
        ],
        "round": 1,
        "bias_flags": [],
        "bias_rechecks": 0,
    }
    base.update(over)
    return base


def test_anchoring_on_leader_forces_one_recheck_round(monkeypatch):
    monkeypatch.setattr(
        bias_check_mod, "_get_llm",
        lambda: _FakeBiasLLM(ANCHORING_ON_LEADER))

    out = bias_check_mod.bias_check_node(_state())

    assert out["force_recheck"] is True
    assert out["bias_rechecks"] == 1
    assert len(out["bias_flags"]) == 1
    assert out["bias_flags"][0]["kind"] == "anchoring"
    # A forced recheck must reactivate every hypothesis so
    # the fan-out can re-run the debate, not just the leader.
    assert all(h["status"] == "active" for h in out["hypotheses"])


def test_recheck_never_fires_a_second_time(monkeypatch):
    """Even if the auditor flags anchoring again, the panel
    has already spent its one bounded recheck -- it must
    proceed, not loop forever chasing a possible bias."""
    monkeypatch.setattr(
        bias_check_mod, "_get_llm",
        lambda: _FakeBiasLLM(ANCHORING_ON_LEADER))

    state = _state(bias_rechecks=1)
    out = bias_check_mod.bias_check_node(state)

    assert out["force_recheck"] is False
    assert out["bias_rechecks"] == 1


def test_no_flags_means_no_recheck(monkeypatch):
    monkeypatch.setattr(
        bias_check_mod, "_get_llm",
        lambda: _FakeBiasLLM(NO_FLAGS))

    out = bias_check_mod.bias_check_node(_state())

    assert out["force_recheck"] is False
    assert out["bias_flags"] == []
    assert out["bias_rechecks"] == 0


def test_anchoring_flag_against_a_non_leader_does_not_recheck(
        monkeypatch):
    """Anchoring must be flagged against the current
    leader specifically -- a flag against a trailing
    hypothesis should not trigger the bounded recheck."""
    flags = (
        '{"flags": [{"kind": "anchoring", '
        '"target": "lyme disease", "note": "n"}]}'
    )
    monkeypatch.setattr(
        bias_check_mod, "_get_llm",
        lambda: _FakeBiasLLM(flags))

    out = bias_check_mod.bias_check_node(_state())

    assert out["force_recheck"] is False
    assert out["bias_rechecks"] == 0
