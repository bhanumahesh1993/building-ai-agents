# procurement_agent/agent.py
from __future__ import annotations

import json
import os

from google.adk.a2a.utils.agent_to_a2a import to_a2a

from procurement_agent.workflow import (
    procurement_workflow, next_po_number,
)
from shared.schemas import PurchaseOrder

SOFT_CAP = float(os.getenv("SOFT_SPEND_CAP", "5000"))
HARD_CAP = float(os.getenv("HARD_SPEND_CAP", "25000"))

_PENDING: dict[str, dict] = {}


def on_reorder(task_id: str, request: dict) -> dict:
    """Run the workflow, then gate on spend."""
    result = procurement_workflow.run({
        "sku": request["sku"],
        "quantity": request["quantity"],
        "max_lead_days": 12,
    })
    draft = json.loads(result)
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


app = to_a2a(
    procurement_workflow, port=8001,
    on_task=on_reorder, on_resume=on_confirm)
