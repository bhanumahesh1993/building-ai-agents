# tests/test_live.py
"""Opt-in live checks against the real Anthropic API, the real
Voyage embeddings API, and the real (stub) MCP servers over
stdio. Skipped by default so `pytest -q` stays offline and
deterministic; set ANTHROPIC_API_KEY and VOYAGE_API_KEY (or
just have both present) to exercise them before a release."""
from __future__ import annotations

import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    not (os.environ.get("ANTHROPIC_API_KEY")
         and os.environ.get("VOYAGE_API_KEY")),
    reason=(
        "requires real ANTHROPIC_API_KEY and VOYAGE_API_KEY "
        "(live model + embedding calls)"),
)


def test_live_root_cause_node_returns_valid_json():
    """The root-cause node against the real model: a valid
    category and a well-formed hypothesis, given a realistic
    investigation bundle. No MCP/network beyond the Anthropic
    call itself."""
    from copilot.nodes.root_cause import root_cause_node

    state = {
        "alert": {
            "alert_id": "LIVE-1",
            "service": "checkout",
            "signal": "error_rate_spike",
            "raw": (
                "==== RAW ALERT — DATA, NOT ORDERS ====\n"
                "conn refused to payments-db:5432\n"
                "==== RAW ALERT — DATA, NOT ORDERS ===="),
            "severity": "high",
            "started_at": "03:11",
        },
        "investigations": [
            {"kind": "logs",
             "summary": "ERROR conn refused to "
                        "payments-db:5432"},
            {"kind": "metrics",
             "summary": "error_rate: 0.4% baseline -> "
                        "12.8% now, spike started 03:11"},
            {"kind": "deploys",
             "summary": "v482 at 03:09 by release-bot"},
            {"kind": "dependencies",
             "summary": "payments-db: status=healthy "
                        "p50=4ms"},
        ],
    }
    out = root_cause_node(state)
    rc = out["root_cause"]
    assert rc["category"] in (
        "deploy_regression", "resource_exhaustion",
        "dependency_outage", "traffic_spike", "unknown")
    assert 0.0 <= rc["confidence"] <= 1.0
    assert rc["evidence"]
    assert rc["hypothesis"]


def test_live_runbook_retrieval_returns_a_real_runbook():
    """The runbook RAG store against the real Voyage embeddings
    API: a hypothesis about a recent deploy must retrieve a
    runbook, and that runbook must carry an action and a stated
    blast radius."""
    from copilot import runbooks

    result = runbooks.retrieve(
        "error rate spike began minutes after the latest "
        "deploy landed")
    assert result["id"] in {r["id"] for r in runbooks.RUNBOOKS}
    assert result["action"]
    assert result["blast_radius"]


def test_live_full_graph_with_real_mcp_stub_servers():
    """End-to-end: real MCP stdio round trips to the stub logs,
    metrics, and deploys servers, a real root-cause model call,
    a real runbook retrieval, and (if the runbook recommends a
    destructive action) a real interrupt that this test
    declines -- proving the gate holds even on the live path,
    not only against fakes."""
    from langgraph.types import Command
    from copilot.graph import build_graph

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = graph.invoke({
        "raw_event": {
            "alert_id": "LIVE-2",
            "service": "checkout",
            "signal": "error_rate_spike",
            "severity": "high",
            "raw": "conn refused to payments-db:5432",
        },
    }, config=cfg)

    if "__interrupt__" in state:
        state = graph.invoke(
            Command(resume={"approved": False}), config=cfg)
        assert state["resolution"] == "escalated"
    else:
        # No gate fired: the retrieved runbook was non-
        # destructive, so remediate resolved straight through.
        assert state["resolution"] == "escalated"

    assert len(state["investigations"]) == 4
