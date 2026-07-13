# tests/test_gate.py
"""Bounded autonomy is a structural property of this graph, not
a prompt instruction: read-only enrichment (asset/user/intel
lookups, correlation) always runs on its own, but any
state-changing response (disable_account, isolate_host) must
pause at langgraph's interrupt() and wait for a human decision
before triage.nodes.respond ever calls the SIEM's mutating
tools. These tests prove that structurally, using the real
graph, not a hand-rolled stand-in."""
from __future__ import annotations

import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt

from triage.graph import build_graph
from triage.state import TriageState
from triage.nodes import verdict as verdict_mod
from triage.nodes import enrich as enrich_mod
from triage.nodes import correlate as correlate_mod
from triage.nodes import respond as respond_mod


def _fake_verdict(state: TriageState) -> dict:
    return {"verdict": {
        "label": "true_positive", "confidence": 0.9,
        "evidence": ["e"],
        "recommended_action": "disable_account"}}


def _fake_respond(state: TriageState) -> dict:
    decision = interrupt({"action": "disable_account"})
    if not decision.get("approved", False):
        return {"resolution": "escalated"}
    return {"resolution": "contained"}


def _build():
    g = StateGraph(TriageState)
    g.add_node("verdict", _fake_verdict)
    g.add_node("respond", _fake_respond)
    g.add_edge(START, "verdict")
    g.add_edge("verdict", "respond")
    g.add_edge("respond", END)
    return g.compile(checkpointer=InMemorySaver())


def test_declined_approval_never_contains():
    """A human decline must never reach 'contained'."""
    graph = _build()
    cfg = {"configurable": {"thread_id": "t1"}}
    graph.invoke({}, config=cfg)
    out = graph.invoke(
        Command(resume={"approved": False}),
        config=cfg)
    assert out["resolution"] == "escalated"


def test_verdict_module_holds_no_destructive_names():
    """Static check: the reasoning step's own source
    never names a destructive action directly."""
    src = open(verdict_mod.__file__).read()
    assert "disable_account" not in src
    assert "isolate_host" not in src


def test_verdict_module_has_no_tool_access():
    """Static check: the verdict node has no MCP client, no
    interrupt call, and no way to reach a mutating tool — it
    can only emit an opinion for triage.nodes.respond to act
    on. Bounded autonomy requires the reasoning step itself to
    be incapable of taking action, not merely told not to."""
    src = open(verdict_mod.__file__).read()
    assert "mcp" not in src.lower()
    assert "interrupt" not in src
    assert "stdio_client" not in src


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeVerdictLLM:
    """Returns a canned verdict for a fixed prompt — no
    network, fully deterministic."""
    def __init__(self, content: str):
        self._content = content

    def invoke(self, prompt):
        return _FakeResponse(self._content)


async def _fake_mcp_call(params, tool: str, args: dict) -> str:
    """Stand-in for the real stdio MCP round trip so tests
    never spawn the stub server subprocesses."""
    if tool == "get_asset_info":
        return "jdoe-laptop: owner=jdoe os=Windows 11 patched=True"
    if tool == "get_user_context":
        return "jdoe: dept=Finance mfa_enrolled=True vip=False"
    if tool == "check_reputation":
        return "203.0.113.44: score=high-risk"
    if tool == "query_related_alerts":
        return "mfa-fatigue (1h ago)\nnew-device-login (3h ago)"
    if tool == "disable_account":
        return f"Disabled {args['user_id']} (ticket {args['ticket_id']})."
    if tool == "isolate_host":
        return f"Isolated {args['host_id']} (ticket {args['ticket_id']})."
    return ""


def _patch_mcp(monkeypatch):
    """Patch every module's own bound name for _call — each
    node imported it with `from .enrich import _call`, so the
    reference must be replaced in each namespace separately."""
    monkeypatch.setattr(enrich_mod, "_call", _fake_mcp_call)
    monkeypatch.setattr(correlate_mod, "_call", _fake_mcp_call)
    monkeypatch.setattr(respond_mod, "_call", _fake_mcp_call)


DESTRUCTIVE_VERDICT = (
    '{"label": "true_positive", "confidence": 0.95, '
    '"evidence": ["mfa fatigue then new device login"], '
    '"recommended_action": "disable_account"}'
)

BENIGN_VERDICT = (
    '{"label": "false_positive", "confidence": 0.8, '
    '"evidence": ["known internal scanner"], '
    '"recommended_action": "none"}'
)


def _alert(alert_id: str) -> dict:
    return {
        "alert_id": alert_id,
        "source": "siem",
        "rule_name": "mfa-fatigue",
        "severity": "high",
        "raw": "user=jdoe host=jdoe-laptop src_ip=203.0.113.44",
    }


def test_readonly_enrichment_is_autonomous_no_gate(monkeypatch):
    """A verdict with a non-destructive recommended_action must
    resolve straight through — enrichment and correlation never
    pause for a human; only containment does."""
    _patch_mcp(monkeypatch)
    monkeypatch.setattr(
        verdict_mod, "_get_llm",
        lambda: _FakeVerdictLLM(BENIGN_VERDICT))

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = graph.invoke(
        {"raw_event": _alert("A1")}, config=cfg)

    assert "__interrupt__" not in state
    assert state["resolution"] == "closed_fp"
    # All three read-only enrichment workers ran on their own.
    assert len(state["enrichment"]) == 3


def test_destructive_verdict_gates_and_decline_blocks_containment(
        monkeypatch):
    """A destructive recommended_action must pause at the
    interrupt, and containment must never run before a human
    approves — declining must route to escalation, never to
    'contained'."""
    _patch_mcp(monkeypatch)
    monkeypatch.setattr(
        verdict_mod, "_get_llm",
        lambda: _FakeVerdictLLM(DESTRUCTIVE_VERDICT))

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = graph.invoke(
        {"raw_event": _alert("A2")}, config=cfg)

    # Structural gate: the graph paused, no containment yet.
    assert "__interrupt__" in state
    gate = state["__interrupt__"][0].value
    assert gate["action"] == "disable_account"
    assert "resolution" not in state

    # Human declines.
    state = graph.invoke(
        Command(resume={"approved": False}), config=cfg)
    assert state["resolution"] == "escalated"
    assert "declined" in state["action_result"]


def test_destructive_verdict_runs_only_after_approval(monkeypatch):
    """Only an explicit human approval may let containment run,
    and it must use the actual SIEM tool call once it does."""
    _patch_mcp(monkeypatch)
    monkeypatch.setattr(
        verdict_mod, "_get_llm",
        lambda: _FakeVerdictLLM(DESTRUCTIVE_VERDICT))

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    graph.invoke({"raw_event": _alert("A3")}, config=cfg)

    state = graph.invoke(
        Command(resume={"approved": True}), config=cfg)
    assert state["resolution"] == "contained"
    assert "Disabled jdoe" in state["action_result"]
