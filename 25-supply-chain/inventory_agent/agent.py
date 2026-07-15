# inventory_agent/agent.py
from __future__ import annotations

import os

from a2a.types import AgentCard
from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
)
from mcp import StdioServerParameters

MODEL = os.getenv("BUYER_MODEL", "gemini-2.5-flash")

# Public A2A Agent Card — the contract Northwind exposes to any
# peer org that wants to delegate a reorder. Structure follows
# the a2a-sdk AgentCard schema (validated in tests/test_agent_card.py).
# NOTE: this is the pinned a2a-sdk 0.3.x (pre-1.0) card shape —
# root-level `url` + `protocolVersion`. A2A v1.0 moves these into a
# `supportedInterfaces[]` array (see the book chapter); this repo
# tracks the installed 0.3.x SDK, so it keeps the 0.x shape here.
AGENT_CARD = {
    "protocolVersion": "1.0",
    "name": "Inventory Agent",
    "description": "Tracks stock; requests reorders.",
    "url": "https://northwind.example.com/a2a",
    "version": "1.4.0",
    "capabilities": {"streaming": False},
    "defaultInputModes": ["text"],
    "defaultOutputModes": ["text"],
    "securitySchemes": {
        "bearer": {"type": "http", "scheme": "bearer"},
    },
    "security": [{"bearer": []}],
    "skills": [{
        "id": "report_stock_status",
        "name": "Report stock status",
        "description": "Current on-hand qty for a SKU.",
        "tags": ["inventory", "supply-chain"],
        "examples": ["What's on hand for GASKET-9?"],
    }],
}

_stock_tools: MCPToolset | None = None
_inventory_agent: LlmAgent | None = None
_app = None


def _get_stock_tools() -> MCPToolset:
    """Lazily wire the stdio MCP toolset. Building this at import
    time would fork a subprocess as a side effect of `import
    inventory_agent.agent` -- defer it to first real use instead."""
    global _stock_tools
    if _stock_tools is None:
        _stock_tools = MCPToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="python",
                    args=["-m", "inventory_agent.mcp_server"],
                ),
            ),
        )
    return _stock_tools


def _get_agent() -> LlmAgent:
    """Lazily build the ADK agent so import needs no model key."""
    global _inventory_agent
    if _inventory_agent is None:
        _inventory_agent = LlmAgent(
            name="inventory_agent",
            model=MODEL,
            description="Watches stock and flags reorders.",
            instruction=(
                "You track stock for Northwind Distribution. "
                "Use your tools to check on-hand quantity "
                "against the reorder line. Never invent a "
                "quantity you did not read from a tool."
            ),
            tools=[_get_stock_tools()],
        )
    return _inventory_agent


def _get_app():
    """Lazily build the A2A Starlette app. Only touched when
    something actually asks for `app` (e.g. uvicorn in run.py),
    never as a side effect of importing this module."""
    global _app
    if _app is None:
        _app = to_a2a(
            _get_agent(), port=8000,
            agent_card=AgentCard(**AGENT_CARD),
        )
    return _app


def __getattr__(name: str):
    # PEP 562: makes `app` a lazy module attribute. `import
    # inventory_agent.agent` alone builds nothing; only
    # `inventory_agent.agent.app` (or `from ... import app`,
    # which run.py's __import__(..., fromlist=["app"]).app does)
    # triggers construction.
    if name == "app":
        return _get_app()
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}")
