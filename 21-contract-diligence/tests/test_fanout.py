# tests/test_fanout.py — the real parallel risk-flag
# Send fan-out, and the playbook-grounding fan-out that
# only escalates medium/high flags. Both are pure
# functions of state, so they're testable with no model
# and no graph execution at all.
from __future__ import annotations

from langgraph.types import Send

from contracts.graph import GROUND_ABOVE, fan_out_playbook, fan_out_risk


def _clause(cid, ctype, text="t"):
    return {"clause_id": cid, "contract_id": "c1",
            "clause_type": ctype, "heading": "H", "text": text}


def test_fan_out_risk_sends_one_worker_per_clause_type():
    """One specialist Send per distinct clause type, batched
    over every clause of that type -- not one Send per clause."""
    state = {"clauses": [
        _clause("a", "indemnification"),
        _clause("b", "indemnification"),
        _clause("c", "termination"),
    ]}

    sends = fan_out_risk(state)

    assert all(isinstance(s, Send) for s in sends)
    assert all(s.node == "risk" for s in sends)
    by_type = {s.arg["clause_type"]: s.arg["clauses"]
               for s in sends}
    assert set(by_type) == {"indemnification", "termination"}
    assert len(by_type["indemnification"]) == 2
    assert len(by_type["termination"]) == 1


def test_fan_out_risk_is_empty_when_there_are_no_clauses():
    assert fan_out_risk({"clauses": []}) == []


def test_fan_out_playbook_falls_through_to_redline_with_nothing_to_ground():
    """No medium/high flags -> no grounding calls at all,
    routed straight to redline."""
    state = {
        "clauses": [_clause("a", "termination")],
        "flags": [{
            "clause_id": "a", "clause_type": "termination",
            "severity": "low", "quote": "q", "rationale": "r",
        }],
        "jurisdiction": "Delaware",
    }

    result = fan_out_playbook(state)

    assert result == ["redline"]


def test_fan_out_playbook_only_grounds_medium_and_high_severity():
    clauses = [
        _clause("a", "termination"),
        _clause("b", "liability_cap"),
        _clause("d", "confidentiality"),
    ]
    flags = [
        {"clause_id": "a", "clause_type": "termination",
         "severity": "low", "quote": "q0", "rationale": "r0"},
        {"clause_id": "b", "clause_type": "liability_cap",
         "severity": "high", "quote": "q1", "rationale": "r1"},
        {"clause_id": "d", "clause_type": "confidentiality",
         "severity": "medium", "quote": "q2", "rationale": "r2"},
    ]
    state = {"clauses": clauses, "flags": flags,
             "jurisdiction": "Delaware"}

    sends = fan_out_playbook(state)

    assert GROUND_ABOVE == ("medium", "high")
    assert len(sends) == 2
    assert all(s.node == "playbook" for s in sends)
    grounded_ids = {s.arg["flag"]["clause_id"] for s in sends}
    assert grounded_ids == {"b", "d"}
    for s in sends:
        assert s.arg["jurisdiction"] == "Delaware"
        assert s.arg["clause"]["clause_id"] == s.arg["flag"]["clause_id"]
