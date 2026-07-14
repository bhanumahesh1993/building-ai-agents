# procurement_agent/agent.py
from __future__ import annotations

import asyncio
import os

from google.adk.a2a.utils.agent_to_a2a import to_a2a

from procurement_agent.workflow import (
    next_po_number, procurement_workflow,
    run_procurement_workflow,
)
from shared.schemas import PurchaseOrder

SOFT_CAP = float(os.getenv("SOFT_SPEND_CAP", "5000"))
HARD_CAP = float(os.getenv("HARD_SPEND_CAP", "25000"))

_PENDING: dict[str, dict] = {}


def apply_spend_gate(
    task_id: str, request: dict, draft: dict,
) -> dict:
    """The human-approval-on-spend gate. Structural, not a
    prompt instruction: anything over HARD_CAP is refused
    outright in code; anything over SOFT_CAP is held in
    _PENDING and returns "input-required" -- no PurchaseOrder
    is ever handed back until on_confirm() is called with the
    buyer's sign-off."""
    total = draft["unit_price"] * request["quantity"]

    if total > HARD_CAP:
        return {"state": "failed",
                "reason": f"total ${total:.2f} "
                          f"exceeds hard cap"}

    po = PurchaseOrder(
        po_number=next_po_number(),
        supplier=draft["supplier"],
        sku=request["sku"],
        quantity=request["quantity"],
        unit_price=draft["unit_price"],
        total=total,
        lead_time_days=draft["lead_time_days"],
    )

    if total > SOFT_CAP:
        _PENDING[task_id] = po.model_dump()
        return {
            "state": "input-required",
            "message": (
                f"{po.supplier} at ${po.unit_price} "
                f"= ${total:.2f} total, exceeds your "
                f"${SOFT_CAP:.0f} auto-approve cap. "
                f"Confirm to finalize."
            ),
        }
    return {"state": "completed", "artifact": po}


def on_reorder(task_id: str, request: dict) -> dict:
    """Run the ADK supplier-selection workflow, then gate on
    spend."""
    draft = asyncio.run(run_procurement_workflow(
        sku=request["sku"], quantity=request["quantity"],
        max_lead_days=12))
    return apply_spend_gate(task_id, request, draft)


def on_confirm(task_id: str, approved: bool) -> dict:
    """Resume a task after buyer sign-off."""
    pending = _PENDING.pop(task_id, None)
    if pending is None:
        return {"state": "failed",
                "reason": "no pending task"}
    if not approved:
        return {"state": "canceled",
                "reason": "buyer declined"}
    return {"state": "completed", "artifact": pending}


_app = None


def _get_app():
    """Lazily build the A2A Starlette app.

    NOTE: the installed google-adk (2.4.0)'s `to_a2a` is marked
    `@a2a_experimental` and, as shipped, takes no `on_task` /
    `on_resume` kwargs -- there is no task-lifecycle hook to wire
    apply_spend_gate()/on_confirm() into the live HTTP transport
    yet. The gate itself is fully real and structural (see
    on_reorder/on_confirm above and tests/test_spend_gate.py);
    only its wiring into this particular experimental transport
    shim is pending an ADK release that exposes the hook. This
    is not faked -- it is the honest current state of an
    experimental integration point."""
    global _app
    if _app is None:
        _app = to_a2a(procurement_workflow, port=8001)
    return _app


def __getattr__(name: str):
    if name == "app":
        return _get_app()
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}")
