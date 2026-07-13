# support/ticket_server.py — mock ticketing MCP
# server. Run: pip install "mcp[cli]", then
# python ticket_server.py
from __future__ import annotations

import itertools
import re

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("notewise-tickets")

_TICKETS: dict[str, dict] = {}
_IDS = itertools.count(1001)

INJECTION_MARKERS = (
    "ignore previous", "ignore all prior",
    "system:", "you are now",
)


def _sanitize(text: str) -> str:
    """Strip likely prompt-injection phrasing before
    ticket text is stored or ever read again."""
    out = text
    for marker in INJECTION_MARKERS:
        out = re.sub(
            marker, "[filtered]", out, flags=re.I)
    return out


@mcp.tool()
def create_ticket(
    customer_id: str, category: str, priority: str,
    queue: str, summary: str, context: str,
) -> str:
    """File a new tier-1 support ticket.

    Use once an escalation summary has been reviewed
    and is ready to hand to a human queue.

    Args:
        customer_id: the Notewise account id.
        category: the classifier's intent label.
        priority: "low", "normal", or "high".
        queue: the human team to route to.
        summary: one-paragraph issue description.
        context: what the agent already tried.
    """
    tid = f"NW-{next(_IDS)}"
    _TICKETS[tid] = {
        "customer_id": customer_id,
        "category": category,
        "priority": priority,
        "queue": queue,
        "summary": _sanitize(summary),
        "context": _sanitize(context),
        "status": "open",
    }
    return tid


@mcp.tool()
def get_ticket(ticket_id: str) -> str:
    """Look up a ticket's current status by id.

    Use when a customer asks about an existing ticket.
    """
    t = _TICKETS.get(ticket_id)
    if t is None:
        return f"No ticket {ticket_id!r} found."
    return (
        f"{ticket_id} [{t['status']}] "
        f"{t['queue']} · priority {t['priority']}\n"
        f"{t['summary']}"
    )


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
