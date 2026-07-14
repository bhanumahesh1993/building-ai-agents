# tests/test_risk_workers.py — the citation guardrail:
# every risk flag must quote clause text verbatim, or it
# is dropped rather than trusted. No model call needed for
# the guardrail itself; the node-level test monkeypatches
# the LLM to prove the guardrail is actually wired in.
from __future__ import annotations

import contracts.risk_workers as risk_mod


class _FakeResp:
    def __init__(self, content: str):
        self.content = content


class _FakeLLM:
    def __init__(self, content: str):
        self._content = content

    def invoke(self, prompt):
        return _FakeResp(self._content)


CLAUSES = [{
    "clause_id": "x1", "contract_id": "c1",
    "clause_type": "termination", "heading": "H",
    "text": "Either party may terminate for convenience "
            "upon 10 days notice.",
}]


def test_verify_quotes_keeps_verbatim_and_drops_fabricated():
    flags = [
        {"clause_id": "x1", "severity": "high",
         "quote": "terminate for convenience upon 10 "
                  "days notice",
         "rationale": "notice period too short"},
        {"clause_id": "x1", "severity": "high",
         "quote": "this text does not appear anywhere",
         "rationale": "fabricated"},
    ]

    out = risk_mod._verify_quotes(flags, CLAUSES)

    assert len(out) == 1
    assert out[0]["rationale"] == "notice period too short"


def test_verify_quotes_is_whitespace_and_case_insensitive():
    """A verbatim quote survives minor whitespace/case
    differences from re-wrapped model output."""
    flags = [{
        "clause_id": "x1", "severity": "medium",
        "quote": "  TERMINATE for convenience\nupon 10 days "
                 "notice  ",
        "rationale": "r",
    }]

    out = risk_mod._verify_quotes(flags, CLAUSES)

    assert len(out) == 1


def test_risk_node_only_emits_flags_grounded_in_clause_text(
        monkeypatch):
    """End to end through risk_node: the guardrail must
    actually be wired into the node, not just exist as a
    helper -- a fabricated quote from the model must never
    reach the returned flags."""
    canned = (
        '{"flags": ['
        '{"clause_id": "x1", "severity": "high", '
        '"quote": "terminate for convenience upon 10 days '
        'notice", "rationale": "notice period too short"}, '
        '{"clause_id": "x1", "severity": "high", '
        '"quote": "fabricated clause not present", '
        '"rationale": "bad"}'
        ']}'
    )
    monkeypatch.setattr(
        risk_mod, "_get_llm", lambda: _FakeLLM(canned))

    out = risk_mod.risk_node(
        {"clause_type": "termination", "clauses": CLAUSES})

    assert len(out["flags"]) == 1
    flag = out["flags"][0]
    assert flag["quote"] in CLAUSES[0]["text"]
    assert flag["clause_type"] == "termination"


def test_risk_node_does_not_decide_enforceability_or_give_legal_advice():
    """Static guard: the specialist's own system prompt must
    keep telling the model to flag-and-explain, never to
    reach a legal conclusion -- a human decides."""
    normalized = " ".join(risk_mod.RISK_SYSTEM.split()).lower()
    assert "do not decide enforceability" in normalized
    assert "do not give legal advice" in normalized
    assert "only flag and explain what a human should look at" \
        in normalized
