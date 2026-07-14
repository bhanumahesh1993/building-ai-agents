# tests/test_spend_gate.py -- the human-approval-on-spend gate.
#
# ProcureIQ's spend gate is structural, not a prompt instruction:
# apply_spend_gate() is plain code that runs after the ADK
# workflow, before a PurchaseOrder is ever handed back across the
# A2A boundary. These tests exercise that seam directly (never
# invoking a real model), the same way
# ../04-support-deflection/tests/test_gate.py exercises its
# LangGraph interrupt directly.
from __future__ import annotations

import importlib.util

import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("google.adk") is None
    or importlib.util.find_spec("a2a") is None,
    reason="google-adk / a2a-sdk not installed",
)

import procurement_agent.agent as agent_mod  # noqa: E402

DRAFT = {
    "supplier": "Fastenal Direct", "unit_price": 13.10,
    "lead_time_days": 5,
}


def _request(quantity: int) -> dict:
    return {
        "sku": "GASKET-9", "quantity": quantity,
        "spend_cap": 5000.0, "buyer_org": "northwind",
    }


def test_below_soft_cap_completes_immediately():
    """unit_price(13.10) * 100 = 1310 -- under both caps."""
    result = agent_mod.apply_spend_gate(
        "task-1", _request(100), DRAFT)
    assert result["state"] == "completed"
    po = result["artifact"]
    assert po.total == pytest.approx(1310.0)
    assert "task-1" not in agent_mod._PENDING


def test_between_soft_and_hard_cap_pauses_for_approval():
    """13.10 * 500 = 6550 -- over the $5000 soft cap, under the
    $25000 hard cap. Must pause, not complete."""
    result = agent_mod.apply_spend_gate(
        "task-2", _request(500), DRAFT)
    assert result["state"] == "input-required"
    assert "artifact" not in result
    assert "task-2" in agent_mod._PENDING
    assert agent_mod._PENDING["task-2"]["total"] == \
        pytest.approx(6550.0)


def test_over_hard_cap_fails_outright_no_pending():
    """13.10 * 2000 = 26200 -- over the $25000 hard cap. Refused
    in code; never even reaches the pending/approval state."""
    result = agent_mod.apply_spend_gate(
        "task-3", _request(2000), DRAFT)
    assert result["state"] == "failed"
    assert "exceeds hard cap" in result["reason"]
    assert "task-3" not in agent_mod._PENDING


def test_confirm_approved_completes_with_pending_artifact():
    agent_mod.apply_spend_gate("task-4", _request(500), DRAFT)
    assert "task-4" in agent_mod._PENDING

    result = agent_mod.on_confirm("task-4", True)
    assert result["state"] == "completed"
    assert result["artifact"]["total"] == pytest.approx(6550.0)
    # Pending entry is consumed -- can't be confirmed twice.
    assert "task-4" not in agent_mod._PENDING


def test_confirm_declined_cancels_without_ever_returning_a_po():
    agent_mod.apply_spend_gate("task-5", _request(500), DRAFT)

    result = agent_mod.on_confirm("task-5", False)
    assert result["state"] == "canceled"
    assert "artifact" not in result
    assert "task-5" not in agent_mod._PENDING


def test_confirm_unknown_task_fails():
    result = agent_mod.on_confirm("no-such-task", True)
    assert result["state"] == "failed"
    assert result["reason"] == "no pending task"


def test_on_reorder_runs_workflow_then_gates(monkeypatch):
    """Full on_reorder(): the ADK workflow call is faked (no
    model, no network) but the gate logic that follows is real."""
    async def fake_run_workflow(*, sku, quantity, max_lead_days):
        assert sku == "GASKET-9"
        assert max_lead_days == 12
        return dict(DRAFT)

    monkeypatch.setattr(
        agent_mod, "run_procurement_workflow",
        fake_run_workflow)

    result = agent_mod.on_reorder("task-6", _request(500))
    assert result["state"] == "input-required"
    assert "task-6" in agent_mod._PENDING


def test_on_reorder_asyncio_run_is_actually_awaited(monkeypatch):
    """Guards against a fake that silently returns a coroutine
    object instead of the awaited dict."""
    called = {}

    async def fake_run_workflow(**kwargs):
        called["ran"] = True
        return dict(DRAFT)

    monkeypatch.setattr(
        agent_mod, "run_procurement_workflow",
        fake_run_workflow)

    agent_mod.on_reorder("task-7", _request(1))
    assert called.get("ran") is True
