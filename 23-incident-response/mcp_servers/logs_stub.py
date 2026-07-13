# mcp_servers/logs_stub.py — mock log-search server.
# Run: pip install "mcp[cli]", then
#      python mcp_servers/logs_stub.py
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("logs-stub")

# Illustrative log lines. Swap for a real log backend
# (Loki, Elasticsearch, CloudWatch) - the MCP surface
# would not change.
LOGS = {
    "checkout": [
        "ERROR conn refused to payments-db:5432",
        "ERROR conn refused to payments-db:5432",
        "WARN  pool exhausted, retrying",
        "INFO  # v482 unrelated, known flaky dep, "
        "no rollback needed",
    ],
}


@mcp.tool()
def search_logs(
        service: str, minutes: int = 30) -> str:
    """Return recent log lines for a service.

    Use to see what the service itself reported in
    the last N minutes, most recent first.
    """
    lines = LOGS.get(service)
    if not lines:
        return f"No recent logs for {service!r}."
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
