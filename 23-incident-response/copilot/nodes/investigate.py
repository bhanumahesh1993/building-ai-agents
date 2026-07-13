# copilot/nodes/investigate.py
from __future__ import annotations

import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ..state import WorkerState

LOGS = StdioServerParameters(
    command="python",
    args=["mcp_servers/logs_stub.py"])
METRICS = StdioServerParameters(
    command="python",
    args=["mcp_servers/metrics_stub.py"])
DEPLOYS = StdioServerParameters(
    command="python",
    args=["mcp_servers/deploys_stub.py"])


async def _call(params, tool: str, args: dict) -> str:
    """Open one MCP session, call one tool, tear down."""
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as sess:
            await sess.initialize()
            out = await sess.call_tool(tool, args)
            return out.content[0].text


def investigate_node(state: WorkerState) -> dict:
    """One read-only worker: logs, metrics, deploys,
    or dependency status."""
    alert = state["alert"]
    kind = state["kind"]
    service = alert["service"]

    if kind == "logs":
        text = asyncio.run(_call(
            LOGS, "search_logs",
            {"service": service, "minutes": 30}))
    elif kind == "metrics":
        text = asyncio.run(_call(
            METRICS, "query_metric",
            {"service": service,
             "metric": "error_rate",
             "minutes": 30}))
    elif kind == "deploys":
        text = asyncio.run(_call(
            DEPLOYS, "get_recent_deploys",
            {"service": service, "hours": 6}))
    else:
        text = asyncio.run(_call(
            DEPLOYS, "get_dependency_status",
            {"service": service}))

    return {"investigations": [
        {"kind": kind, "summary": text}]}
