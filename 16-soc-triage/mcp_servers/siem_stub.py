# mcp_servers/siem_stub.py — mock SIEM server.
# Run: pip install "mcp[cli]", then
#      python mcp_servers/siem_stub.py
from __future__ import annotations

import time

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("siem-stub")

ASSETS = {
    "jdoe-laptop": {
        "owner": "jdoe", "os": "Windows 11",
        "patched": True, "criticality": "standard",
    },
}

USERS = {
    "jdoe": {
        "dept": "Finance", "mfa_enrolled": True,
        "recent_travel": "none logged", "vip": False,
    },
}

# Illustrative alert history for correlation queries.
ALERT_LOG = [
    {"entity": "jdoe", "rule": "mfa-fatigue",
     "hours_ago": 1},
    {"entity": "jdoe", "rule": "new-device-login",
     "hours_ago": 3},
]

_DISABLED: set[str] = set()
_ISOLATED: set[str] = set()
_AUDIT: list[dict] = []


@mcp.tool()
def get_asset_info(host_id: str) -> str:
    """Return asset details for a host by its id.

    Use to check ownership, patch state, and how
    critical a host is before recommending a response.
    """
    a = ASSETS.get(host_id)
    if a is None:
        return f"No asset record for {host_id!r}."
    return (
        f"{host_id}: owner={a['owner']} "
        f"os={a['os']} patched={a['patched']} "
        f"criticality={a['criticality']}")


@mcp.tool()
def get_user_context(user_id: str) -> str:
    """Return account context for a user by their id.

    Use to check MFA enrollment, travel notes, and
    whether this account carries elevated privilege.
    """
    u = USERS.get(user_id)
    if u is None:
        return f"No user record for {user_id!r}."
    return (
        f"{user_id}: dept={u['dept']} "
        f"mfa_enrolled={u['mfa_enrolled']} "
        f"recent_travel={u['recent_travel']} "
        f"vip={u['vip']}")


@mcp.tool()
def query_related_alerts(
    entity: str, hours: int = 24,
) -> str:
    """List other alerts touching this user or host.

    Use to check whether an alert is an isolated
    event or part of a pattern before judging it.
    """
    hits = [
        a for a in ALERT_LOG
        if a["entity"] == entity
        and a["hours_ago"] <= hours
    ]
    if not hits:
        return ""
    return "\n".join(
        f"{h['rule']} ({h['hours_ago']}h ago)"
        for h in hits)


@mcp.tool()
def disable_account(user_id: str, ticket_id: str) -> str:
    """HUMAN-ONLY. Disables a user account.

    Never list this tool for a model to call. It is
    invoked directly by app code after a human has
    approved the action via the interrupt gate.
    """
    _DISABLED.add(user_id)
    _AUDIT.append({
        "action": "disable_account",
        "user_id": user_id, "ticket_id": ticket_id,
        "at": time.time(),
    })
    return f"Disabled {user_id} (ticket {ticket_id})."


@mcp.tool()
def isolate_host(host_id: str, ticket_id: str) -> str:
    """HUMAN-ONLY. Network-isolates a host.

    Same rule as disable_account: reachable only from
    app code that already has human approval in hand.
    """
    _ISOLATED.add(host_id)
    _AUDIT.append({
        "action": "isolate_host",
        "host_id": host_id, "ticket_id": ticket_id,
        "at": time.time(),
    })
    return f"Isolated {host_id} (ticket {ticket_id})."


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
