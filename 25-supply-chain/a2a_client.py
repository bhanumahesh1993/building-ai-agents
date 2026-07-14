# a2a_client.py
from __future__ import annotations

import uuid

import httpx
from pydantic import ValidationError

from shared.schemas import PurchaseOrder, ReorderRequest


class UntrustedRemoteOutputError(ValueError):
    """A peer agent's task result failed validation.

    A completed A2A task from another organization's agent is
    untrusted input -- exactly like a response from any other
    third party over the network -- until it validates against
    our own schema. Never index into a remote artifact's fields
    directly; always go through extract_purchase_order()."""


def discover(base_url: str) -> dict:
    """Fetch a peer's public Agent Card."""
    url = f"{base_url}/.well-known/agent-card.json"
    return httpx.get(url).json()


def can_fulfill(card: dict, skill_id: str) -> bool:
    """Check the peer advertises the skill we need."""
    return any(
        s["id"] == skill_id
        for s in card.get("skills", []))


def delegate(card: dict, req: ReorderRequest) -> dict:
    """Send a reorder as an A2A task."""
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {"message": {
            "role": "user",
            "messageId": str(uuid.uuid4()),
            "parts": [
                {"kind": "text",
                 "text": f"Reorder {req.quantity} "
                         f"of {req.sku}"},
                {"kind": "data",
                 "data": req.model_dump()},
            ],
        }},
    }
    resp = httpx.post(card["url"], json=payload)
    return resp.json()["result"]


def confirm(card: str, task_id: str,
            approved: bool) -> dict:
    """Send buyer sign-off as a follow-up message."""
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "taskId": task_id,
            "message": {
                "role": "user",
                "messageId": str(uuid.uuid4()),
                "parts": [{"kind": "data",
                           "data": {
                               "approved": approved}}],
            },
        },
    }
    resp = httpx.post(card, json=payload)
    return resp.json()["result"]


def extract_purchase_order(task: dict) -> PurchaseOrder:
    """Validate a remote peer's completed-task artifact before
    trusting a single field of it.

    ProcureIQ is a separate, independently-owned agent -- its
    output crosses a trust boundary the same way any external
    API response would. A malformed or malicious artifact
    (wrong types, negative quantities, missing fields, extra
    injected keys) must be rejected here, not consumed by
    downstream code that assumes it is well-formed.
    """
    try:
        data = task["artifacts"][0]["parts"][0]["data"]
    except (KeyError, IndexError, TypeError) as exc:
        raise UntrustedRemoteOutputError(
            f"malformed task artifact: {exc}") from exc
    try:
        return PurchaseOrder.model_validate(data)
    except ValidationError as exc:
        raise UntrustedRemoteOutputError(
            f"artifact failed schema validation: {exc}") from exc
