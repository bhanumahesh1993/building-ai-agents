# mcp_servers/intel_stub.py — mock threat-intel
# reputation server. Run: pip install "mcp[cli]",
# then python mcp_servers/intel_stub.py
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("intel-stub")

# Illustrative reputation data. Swap for a real feed —
# the MCP surface would not change.
REPUTATION = {
    "203.0.113.44": {
        "score": "high-risk",
        "tags": ["credential-stuffing-source",
                 "known-vpn-abuse"],
    },
}


@mcp.tool()
def check_reputation(indicator: str, kind: str) -> str:
    """Look up reputation for an IP, domain, or hash.

    Use to check whether a source IP or indicator
    from an alert has a known-bad history.

    Args:
        indicator: the value to check, e.g. an IP.
        kind: "ip", "domain", or "hash".
    """
    r = REPUTATION.get(indicator)
    if r is None:
        return f"{indicator}: no reputation data ({kind})."
    tags = ", ".join(r["tags"])
    return f"{indicator}: score={r['score']} tags={tags}"


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
