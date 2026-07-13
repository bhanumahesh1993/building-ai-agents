# mcp_servers/metrics_stub.py — mock metrics-query
# server. Run: pip install "mcp[cli]", then
#      python mcp_servers/metrics_stub.py
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("metrics-stub")

# Illustrative time series summaries. Swap for a real
# TSDB (Prometheus, Datadog) - the MCP surface would
# not change.
METRICS = {
    ("checkout", "error_rate"): (
        "error_rate: 0.4% baseline -> 12.8% now, "
        "spike started 03:11, still elevated"),
}


@mcp.tool()
def query_metric(
        service: str, metric: str,
        minutes: int = 30) -> str:
    """Return a summary of one metric for a service.

    Use to see how far a metric has moved from its
    baseline and when the change began.
    """
    val = METRICS.get((service, metric))
    if val is None:
        return f"No {metric!r} data for {service!r}."
    return val


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
