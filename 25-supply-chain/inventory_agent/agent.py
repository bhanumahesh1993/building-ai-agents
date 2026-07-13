# inventory_agent/agent.py
from __future__ import annotations

import os

from google.adk.agents import LlmAgent
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StdioConnectionParams,
)

MODEL = os.getenv("BUYER_MODEL", "gemini-2.5-flash")

stock_tools = MCPToolset(
    connection_params=StdioConnectionParams(
        command="python",
        args=["-m", "inventory_agent.mcp_server"],
    ),
)

inventory_agent = LlmAgent(
    name="inventory_agent",
    model=MODEL,
    description="Watches stock and flags reorders.",
    instruction=(
        "You track stock for Northwind Distribution. "
        "Use your tools to check on-hand quantity "
        "against the reorder line. Never invent a "
        "quantity you did not read from a tool."
    ),
    tools=[stock_tools],
)

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

app = to_a2a(inventory_agent, port=8000, card=AGENT_CARD)
