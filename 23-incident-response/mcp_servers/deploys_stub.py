# mcp_servers/deploys_stub.py — mock deploy/CD
# server. Run: pip install "mcp[cli]", then
#      python mcp_servers/deploys_stub.py
from __future__ import annotations

import time

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("deploys-stub")

DEPLOYS = {
    "checkout": [
        {"id": "v482", "at": "03:09",
         "by": "release-bot"},
        {"id": "v481", "at": "yesterday 14:02",
         "by": "release-bot"},
    ],
}

DEPENDENCIES = {
    "checkout": {
        "payments-db": {
            "status": "healthy", "p50_ms": 4},
    },
}

_ROLLED_BACK: dict[str, str] = {}
_RESTARTED: set[str] = set()
_SCALED: dict[str, int] = {}
_AUDIT: list[dict] = []


@mcp.tool()
def get_recent_deploys(
        service: str, hours: int = 6) -> str:
    """List deploys for a service in the last N hours.

    Use to check whether a deploy landed shortly
    before an incident started.
    """
    deploys = DEPLOYS.get(service, [])
    if not deploys:
        return f"No recent deploys for {service!r}."
    return "\n".join(
        f"{d['id']} at {d['at']} by {d['by']}"
        for d in deploys)


@mcp.tool()
def get_dependency_status(service: str) -> str:
    """Return health of a service's dependencies.

    Use to check whether a downstream dependency is
    degraded before blaming it for an incident.
    """
    deps = DEPENDENCIES.get(service, {})
    if not deps:
        return f"No dependency data for {service!r}."
    return "\n".join(
        f"{name}: status={d['status']} "
        f"p50={d['p50_ms']}ms"
        for name, d in deps.items())


@mcp.tool()
def rollback_deploy(
        service: str, deploy_id: str,
        ticket_id: str) -> str:
    """HUMAN-ONLY. Rolls a service back to a prior
    deploy id.

    Never list this tool for a model to call. It is
    invoked directly by app code after a human has
    approved the action via the interrupt gate.
    """
    _ROLLED_BACK[service] = deploy_id
    _AUDIT.append({
        "action": "rollback_deploy",
        "service": service, "deploy_id": deploy_id,
        "ticket_id": ticket_id, "at": time.time(),
    })
    return (f"Rolled back {service} to "
            f"{deploy_id} (ticket {ticket_id}).")


@mcp.tool()
def restart_service(
        service: str, ticket_id: str) -> str:
    """HUMAN-ONLY. Restarts a service's instances.

    Same rule as rollback_deploy: reachable only from
    app code that already has human approval in hand.
    """
    _RESTARTED.add(service)
    _AUDIT.append({
        "action": "restart_service",
        "service": service, "ticket_id": ticket_id,
        "at": time.time(),
    })
    return f"Restarted {service} (ticket {ticket_id})."


@mcp.tool()
def scale_service(
        service: str, replicas: int,
        ticket_id: str) -> str:
    """HUMAN-ONLY. Scales a service to N replicas.

    Same rule as rollback_deploy: reachable only from
    app code that already has human approval in hand.
    """
    _SCALED[service] = replicas
    _AUDIT.append({
        "action": "scale_service",
        "service": service, "replicas": replicas,
        "ticket_id": ticket_id, "at": time.time(),
    })
    return (f"Scaled {service} to {replicas} "
            f"replicas (ticket {ticket_id}).")


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
