# a2a_client.py
from __future__ import annotations

import uuid

import httpx

from shared.schemas import ReorderRequest


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
