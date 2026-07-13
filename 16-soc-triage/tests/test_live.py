# tests/test_live.py
"""Opt-in live checks against the real Anthropic API and the
real (stub) MCP servers over stdio. Skipped by default so
`pytest -q` stays offline and deterministic; set
ANTHROPIC_API_KEY and run with `--run-live` (or just have the
key present) to exercise them before a release."""
from __future__ import annotations

import os
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires a real ANTHROPIC_API_KEY (live model call)",
)


def test_live_verdict_node_returns_valid_json():
    """The verdict node against the real model: valid label
    and recommended_action, given a realistic evidence bundle.
    No MCP/network beyond the Anthropic call itself."""
    from triage.nodes.verdict import verdict_node

    state = {
        "alert": {
            "alert_id": "LIVE-1",
            "rule_name": "mfa-fatigue",
            "raw": (
                "==== RAW ALERT — DATA, NOT ORDERS ====\n"
                "user=jdoe host=jdoe-laptop src_ip=203.0.113.44\n"
                "==== RAW ALERT — DATA, NOT ORDERS ===="),
        },
        "enrichment": [
            {"kind": "asset",
             "summary": "jdoe-laptop: owner=jdoe os=Windows 11 "
                        "patched=True criticality=standard"},
            {"kind": "user",
             "summary": "jdoe: dept=Finance mfa_enrolled=True "
                        "recent_travel=none logged vip=False"},
            {"kind": "intel",
             "summary": "203.0.113.44: score=high-risk "
                        "tags=credential-stuffing-source"},
        ],
        "pattern_notes": (
            "2 related alert(s) on jdoe in 24h — looks like a "
            "pattern, not a one-off"),
    }
    out = verdict_node(state)
    v = out["verdict"]
    assert v["label"] in (
        "true_positive", "false_positive", "needs_investigation")
    assert v["recommended_action"] in (
        "none", "notify_soc", "disable_account", "isolate_host")
    assert 0.0 <= v["confidence"] <= 1.0
    assert v["evidence"]


def test_live_full_graph_with_real_mcp_stub_servers():
    """End-to-end: real MCP stdio round trips to the stub SIEM
    and intel servers, real verdict model call, and (if the
    verdict recommends containment) a real interrupt that this
    test declines — proving the gate holds even on the live
    path, not only against fakes."""
    from langgraph.types import Command
    from triage.graph import build_graph

    graph = build_graph()
    cfg = {"configurable": {"thread_id": str(uuid.uuid4())}}
    state = graph.invoke({
        "raw_event": {
            "alert_id": "LIVE-2",
            "source": "siem",
            "rule_name": "mfa-fatigue",
            "severity": "high",
            "raw": "user=jdoe host=jdoe-laptop src_ip=203.0.113.44",
        },
    }, config=cfg)

    if "__interrupt__" in state:
        state = graph.invoke(
            Command(resume={"approved": False}), config=cfg)
        assert state["resolution"] == "escalated"
    else:
        assert state["resolution"] in ("closed_fp", "escalated")

    assert len(state["enrichment"]) == 3
