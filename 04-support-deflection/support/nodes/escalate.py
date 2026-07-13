# support/nodes/escalate.py
from __future__ import annotations

import asyncio
import json
import os

from langchain_anthropic import ChatAnthropic
from langgraph.types import interrupt
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ..state import TicketState

ESCALATE_MODEL = os.getenv(
    "ESCALATE_MODEL", "claude-sonnet-4-5")

_llm = ChatAnthropic(
    model=ESCALATE_MODEL, temperature=0)

SUMMARY_SYSTEM = """Summarize this ticket for a human
agent taking over. Be factual and brief.

Return ONLY JSON:
{{"issue": "...", "attempted": "...",
  "sentiment": "frustrated|neutral|positive",
  "urgency": "low|normal|high",
  "queue": "billing|technical|account|product"}}

Category: {category}
Message: {message}
KB sections tried: {tried}"""

TICKET_PARAMS = StdioServerParameters(
    command="python", args=["ticket_server.py"])


async def _create_ticket(payload: dict) -> str:
    """Call the MCP ticketing server's create_ticket."""
    async with stdio_client(TICKET_PARAMS) as (r, w):
        async with ClientSession(r, w) as sess:
            await sess.initialize()
            result = await sess.call_tool(
                "create_ticket", payload)
            return result.content[0].text


def escalate_node(state: TicketState) -> dict:
    """Summarize, pause for human review, file a ticket."""
    tried = ", ".join(
        h["section"] for h in state.get("kb_hits", []))
    prompt = SUMMARY_SYSTEM.format(
        category=state.get("category", "unknown"),
        message=state["message"],
        tried=tried or "none",
    )
    resp = _llm.invoke(prompt)
    draft = json.loads(resp.content)

    # Human-in-the-loop: a support lead reviews the
    # draft summary before it becomes a real ticket.
    reviewed = interrupt({
        "message": state["message"],
        "summary": draft,
    })
    summary = reviewed.get("summary", draft)

    ticket_id = asyncio.run(_create_ticket({
        "customer_id": state.get("customer_id", ""),
        "category": state.get("category", "unknown"),
        "priority": summary["urgency"],
        "queue": summary["queue"],
        "summary": summary["issue"],
        "context": summary["attempted"],
    }))
    return {
        "escalation": summary,
        "resolution": "escalated",
        "ticket_id": ticket_id,
        "events": [
            {"node": "escalate", "ticket": ticket_id}],
    }
