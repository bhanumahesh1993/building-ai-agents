# tests/test_gate.py
"""The escalation review is a structural human-in-the-loop
gate (langgraph's interrupt), not a prompt instruction. These
tests prove the gate actually blocks: no ticket may be filed
until a human resumes the graph with a reviewed summary."""
from __future__ import annotations

import uuid

from langgraph.types import Command

from support.graph import build_graph
from support.nodes import classify as classify_mod
from support.nodes import escalate as escalate_mod


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeLLM:
    def __init__(self, content: str):
        self._content = content

    def invoke(self, prompt):
        return _FakeResponse(self._content)


def test_gate_blocks_ticket_creation_until_human_resumes(monkeypatch):
    # category "abuse" routes straight from classify to escalate,
    # skipping retrieve/answer entirely (no DB or embeddings).
    monkeypatch.setattr(
        classify_mod, "_llm",
        _FakeLLM('{"category": "abuse", "confidence": 1.0}'))

    monkeypatch.setattr(
        escalate_mod, "_llm",
        _FakeLLM(
            '{"issue": "spam message", "attempted": "none", '
            '"sentiment": "neutral", "urgency": "low", '
            '"queue": "product"}'))

    created: list[dict] = []

    async def _fake_create_ticket(payload: dict) -> str:
        created.append(payload)
        return "NW-9999"

    monkeypatch.setattr(
        escalate_mod, "_create_ticket", _fake_create_ticket)

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}

    state = graph.invoke(
        {"customer_id": "c1", "message": "buy cheap watches now!!!"},
        config=cfg)

    # Structural gate: the graph paused for human review and no
    # ticket has been created yet.
    assert "__interrupt__" in state
    assert created == []
    assert "resolution" not in state

    pending = state["__interrupt__"][0].value
    summary = pending["summary"]
    assert summary["queue"] == "product"

    # Human reviews (here, approves as-is) and resumes.
    state = graph.invoke(
        Command(resume={"summary": summary}), config=cfg)

    # Only after resume does the ticket get filed.
    assert state["resolution"] == "escalated"
    assert state["ticket_id"] == "NW-9999"
    assert len(created) == 1
    assert created[0]["queue"] == "product"


def test_human_edit_during_review_is_what_gets_filed(monkeypatch):
    """The gate must use the human-reviewed summary, not silently
    re-run or fall back to the model's original draft, once a
    human has actually supplied edits."""
    monkeypatch.setattr(
        classify_mod, "_llm",
        _FakeLLM('{"category": "feature_request", "confidence": 1.0}'))

    monkeypatch.setattr(
        escalate_mod, "_llm",
        _FakeLLM(
            '{"issue": "wants dark mode", "attempted": "none", '
            '"sentiment": "neutral", "urgency": "low", '
            '"queue": "product"}'))

    created: list[dict] = []

    async def _fake_create_ticket(payload: dict) -> str:
        created.append(payload)
        return "NW-1234"

    monkeypatch.setattr(
        escalate_mod, "_create_ticket", _fake_create_ticket)

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}

    graph.invoke(
        {"customer_id": "c2", "message": "please add dark mode"},
        config=cfg)

    edited_summary = {
        "issue": "wants dark mode (VIP account)",
        "attempted": "none",
        "sentiment": "positive",
        "urgency": "high",
        "queue": "product",
    }
    state = graph.invoke(
        Command(resume={"summary": edited_summary}), config=cfg)

    assert state["escalation"] == edited_summary
    assert created[0]["priority"] == "high"
    assert created[0]["summary"] == "wants dark mode (VIP account)"
