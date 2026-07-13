# triage/nodes/enrich.py
from __future__ import annotations

import asyncio

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ..state import WorkerState

SIEM = StdioServerParameters(
    command="python",
    args=["mcp_servers/siem_stub.py"])
INTEL = StdioServerParameters(
    command="python",
    args=["mcp_servers/intel_stub.py"])


async def _call(params, tool: str, args: dict) -> str:
    """Open one MCP session, call one tool, tear down."""
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as sess:
            await sess.initialize()
            out = await sess.call_tool(tool, args)
            return out.content[0].text


def enrich_node(state: WorkerState) -> dict:
    """One read-only worker: asset, user, or intel."""
    alert = state["alert"]
    kind = state["kind"]
    ent = alert["entities"]

    if kind == "asset":
        text = asyncio.run(_call(
            SIEM, "get_asset_info",
            {"host_id": ent.get("host", "")}))
    elif kind == "user":
        text = asyncio.run(_call(
            SIEM, "get_user_context",
            {"user_id": ent.get("user", "")}))
    else:
        text = asyncio.run(_call(
            INTEL, "check_reputation",
            {"indicator": ent.get("src_ip", ""),
             "kind": "ip"}))

    return {"enrichment": [
        {"kind": kind, "summary": text}]}
