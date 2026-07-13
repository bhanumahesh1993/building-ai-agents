# copilot/nodes/remediate.py
from __future__ import annotations

import asyncio

from langgraph.types import interrupt

from .. import runbooks
from ..state import IncidentState
from .investigate import DEPLOYS, _call

DESTRUCTIVE = {
    "rollback_deploy", "restart_service",
    "scale_service"}


def remediate_node(state: IncidentState) -> dict:
    """Retrieve a runbook; auto-resolve read-only
    outcomes; always pause for a human before any
    state-changing remediation."""
    rc = state["root_cause"]
    rb = runbooks.retrieve(rc["hypothesis"])
    remediation = {
        "runbook_id": rb["id"],
        "steps": rb["steps"],
        "action": rb["action"],
        "blast_radius": rb["blast_radius"],
    }
    alert_id = state["alert"]["alert_id"]

    if rb["action"] not in DESTRUCTIVE:
        return {
            "remediation": remediation,
            "resolution": "escalated",
            "action_result": (
                "no automated action "
                f"({rb['action']})"),
            "audit": [{"node": "remediate",
                        "action": rb["action"],
                        "auto": True}],
        }

    decision = interrupt({
        "alert_id": alert_id,
        "root_cause": rc,
        "remediation": remediation,
    })
    if not decision.get("approved", False):
        return {
            "remediation": remediation,
            "resolution": "escalated",
            "action_result": "remediation declined",
            "audit": [{"node": "remediate",
                        "action": rb["action"],
                        "approved": False}],
        }

    service = state["alert"]["service"]
    action = rb["action"]
    if action == "rollback_deploy":
        deploy_id = decision.get(
            "deploy_id", "previous")
        result = asyncio.run(_call(
            DEPLOYS, "rollback_deploy",
            {"service": service,
             "deploy_id": deploy_id,
             "ticket_id": alert_id}))
    elif action == "restart_service":
        result = asyncio.run(_call(
            DEPLOYS, "restart_service",
            {"service": service,
             "ticket_id": alert_id}))
    else:
        replicas = decision.get("replicas", 2)
        result = asyncio.run(_call(
            DEPLOYS, "scale_service",
            {"service": service,
             "replicas": replicas,
             "ticket_id": alert_id}))

    return {
        "remediation": remediation,
        "resolution": "remediated",
        "action_result": result,
        "audit": [{"node": "remediate",
                    "action": action,
                    "approved": True}],
    }
