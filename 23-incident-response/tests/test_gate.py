# tests/test_gate.py
"""Bounded autonomy is a structural property of this graph, not
a prompt instruction: read-only investigation (logs, metrics,
deploys, dependency-status lookups) always runs on its own, but
any state-changing remediation (rollback_deploy,
restart_service, scale_service) must pause at langgraph's
interrupt() and wait for a human decision before
copilot.nodes.remediate ever calls the deploys stub's mutating
tools. These tests prove that structurally, using the real
graph, not only a hand-rolled stand-in."""
from __future__ import annotations

import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt

from copilot import runbooks as runbooks_mod
from copilot.graph import build_graph
from copilot.state import IncidentState
from copilot.nodes import root_cause as root_cause_mod
from copilot.nodes import investigate as investigate_mod
from copilot.nodes import remediate as remediate_mod


# --- minimal hand-rolled stand-in: the gate primitive itself ----

def _fake_root_cause(state: IncidentState) -> dict:
    return {"root_cause": {
        "hypothesis": "h", "confidence": 0.9,
        "evidence": ["e"],
        "category": "deploy_regression"}}


def _fake_remediate(state: IncidentState) -> dict:
    decision = interrupt(
        {"action": "rollback_deploy"})
    if not decision.get("approved", False):
        return {"resolution": "escalated"}
    return {"resolution": "remediated"}


def _build():
    g = StateGraph(IncidentState)
    g.add_node("root_cause", _fake_root_cause)
    g.add_node("remediate", _fake_remediate)
    g.add_edge(START, "root_cause")
    g.add_edge("root_cause", "remediate")
    g.add_edge("remediate", END)
    return g.compile(checkpointer=InMemorySaver())


def test_declined_approval_never_remediates():
    """A human decline must never reach 'remediated'."""
    graph = _build()
    cfg = {"configurable": {"thread_id": "t1"}}
    graph.invoke({}, config=cfg)
    out = graph.invoke(
        Command(resume={"approved": False}),
        config=cfg)
    assert out["resolution"] == "escalated"


# --- static checks: the reasoning node can never act on its own --

def test_root_cause_holds_no_destructive_names():
    """Static check: the reasoning step's own
    source never names a destructive action."""
    src = open(root_cause_mod.__file__).read()
    assert "rollback_deploy" not in src
    assert "restart_service" not in src
    assert "scale_service" not in src


def test_root_cause_module_has_no_tool_access():
    """Static check: the root-cause node has no MCP client, no
    interrupt call, and no way to reach a mutating tool -- it
    can only emit an opinion for copilot.nodes.remediate to act
    on. Bounded autonomy requires the reasoning step itself to
    be incapable of taking action, not merely told not to."""
    src = open(root_cause_mod.__file__).read()
    assert "mcp" not in src.lower()
    assert "interrupt" not in src
    assert "stdio_client" not in src


# --- full-graph tests with faked LLM, MCP, and RAG retrieval ----

class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeRootCauseLLM:
    """Returns a canned root-cause opinion for a fixed prompt --
    no network, fully deterministic."""
    def __init__(self, content: str):
        self._content = content

    def invoke(self, prompt):
        return _FakeResponse(self._content)


async def _fake_mcp_call(params, tool: str, args: dict) -> str:
    """Stand-in for the real stdio MCP round trip so tests never
    spawn the stub server subprocesses."""
    if tool == "search_logs":
        return "ERROR conn refused to payments-db:5432"
    if tool == "query_metric":
        return "error_rate: 0.4% baseline -> 12.8% now"
    if tool == "get_recent_deploys":
        return "v482 at 03:09 by release-bot"
    if tool == "get_dependency_status":
        return "payments-db: status=healthy p50=4ms"
    if tool == "rollback_deploy":
        return (f"Rolled back {args['service']} to "
                f"{args['deploy_id']} (ticket "
                f"{args['ticket_id']}).")
    if tool == "restart_service":
        return (f"Restarted {args['service']} "
                f"(ticket {args['ticket_id']}).")
    if tool == "scale_service":
        return (f"Scaled {args['service']} to "
                f"{args['replicas']} replicas (ticket "
                f"{args['ticket_id']}).")
    return ""


def _patch_mcp(monkeypatch):
    """Patch every module's own bound name for _call -- each
    node imported it with `from .investigate import _call`, so
    the reference must be replaced in each namespace
    separately."""
    monkeypatch.setattr(
        investigate_mod, "_call", _fake_mcp_call)
    monkeypatch.setattr(
        remediate_mod, "_call", _fake_mcp_call)


NOTIFY_ONLY_ROOT_CAUSE = (
    '{"hypothesis": "payments-db dependency is degraded", '
    '"confidence": 0.8, '
    '"evidence": ["dependency status shows elevated errors"], '
    '"category": "dependency_outage"}'
)

DEPLOY_REGRESSION_ROOT_CAUSE = (
    '{"hypothesis": "deploy v482 introduced a payments-db '
    'connection regression", "confidence": 0.9, '
    '"evidence": ["error spike began minutes after v482"], '
    '"category": "deploy_regression"}'
)


def _alert(alert_id: str) -> dict:
    return {
        "alert_id": alert_id,
        "service": "checkout",
        "signal": "error_rate_spike",
        "severity": "high",
        "raw": "conn refused to payments-db",
    }


def test_readonly_remediation_is_autonomous_no_gate(
        monkeypatch):
    """A root cause whose runbook maps to a non-destructive
    action (rb-033, notify_only) must resolve straight
    through -- investigation and root-cause reasoning never
    pause for a human; only a destructive remediation does."""
    _patch_mcp(monkeypatch)
    monkeypatch.setattr(
        root_cause_mod, "_get_llm",
        lambda: _FakeRootCauseLLM(NOTIFY_ONLY_ROOT_CAUSE))
    monkeypatch.setattr(
        runbooks_mod, "retrieve",
        lambda query: runbooks_mod.RUNBOOKS[2])  # rb-033

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = graph.invoke(
        {"raw_event": _alert("A1")}, config=cfg)

    assert "__interrupt__" not in state
    assert state["resolution"] == "escalated"
    assert state["remediation"]["action"] == "notify_only"
    # All four read-only investigation workers ran on their own.
    assert len(state["investigations"]) == 4


def test_destructive_remediation_gates_and_decline_blocks_it(
        monkeypatch):
    """A root cause whose runbook maps to a destructive action
    (rb-014, rollback_deploy) must pause at the interrupt, and
    remediation must never run before a human approves --
    declining must route to escalation, never to
    'remediated'."""
    _patch_mcp(monkeypatch)
    monkeypatch.setattr(
        root_cause_mod, "_get_llm",
        lambda: _FakeRootCauseLLM(
            DEPLOY_REGRESSION_ROOT_CAUSE))
    monkeypatch.setattr(
        runbooks_mod, "retrieve",
        lambda query: runbooks_mod.RUNBOOKS[0])  # rb-014

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = graph.invoke(
        {"raw_event": _alert("A2")}, config=cfg)

    # Structural gate: the graph paused, no remediation yet.
    assert "__interrupt__" in state
    gate = state["__interrupt__"][0].value
    assert gate["remediation"]["action"] == "rollback_deploy"
    assert "resolution" not in state

    # Human declines.
    state = graph.invoke(
        Command(resume={"approved": False}), config=cfg)
    assert state["resolution"] == "escalated"
    assert "declined" in state["action_result"]


def test_destructive_remediation_runs_only_after_approval(
        monkeypatch):
    """Only an explicit human approval may let remediation run,
    and it must use the actual deploys-stub tool call once it
    does."""
    _patch_mcp(monkeypatch)
    monkeypatch.setattr(
        root_cause_mod, "_get_llm",
        lambda: _FakeRootCauseLLM(
            DEPLOY_REGRESSION_ROOT_CAUSE))
    monkeypatch.setattr(
        runbooks_mod, "retrieve",
        lambda query: runbooks_mod.RUNBOOKS[0])  # rb-014

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    graph.invoke({"raw_event": _alert("A3")}, config=cfg)

    state = graph.invoke(
        Command(resume={
            "approved": True, "deploy_id": "v481"}),
        config=cfg)
    assert state["resolution"] == "remediated"
    assert "Rolled back checkout to v481" in \
        state["action_result"]
