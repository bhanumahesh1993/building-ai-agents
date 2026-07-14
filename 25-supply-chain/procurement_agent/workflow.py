# procurement_agent/workflow.py
from __future__ import annotations

import json
import os
import uuid

from google.adk.agents import LlmAgent, SequentialAgent

from procurement_agent.mcp_tools import (
    get_quotes, record_order,
)

APP_NAME = "procurement-workflow"

MODEL = os.getenv(
    "SUPPLIER_MODEL", "gemini-2.5-flash")

SELECT_PROMPT = (
    "Call get_quotes for the requested SKU. Drop "
    "any vendor whose lead_time_days exceeds the "
    "buyer's max_lead_days. Return the surviving "
    "candidates as JSON."
)

COMPARE_PROMPT = (
    "Given the surviving candidates, pick the one "
    "with the lowest unit_price. Explain the trade"
    "-off against any faster but pricier option in "
    "one sentence. Return the winner as JSON."
)

DRAFT_PROMPT = (
    "Draft a purchase order for the winning quote: "
    "sku, quantity, unit_price, total, supplier, "
    "lead_time_days. Compute total precisely. "
    "Return JSON only, no prose."
)

supplier_selection = LlmAgent(
    name="supplier_selection", model=MODEL,
    instruction=SELECT_PROMPT, tools=[get_quotes])

quote_comparison = LlmAgent(
    name="quote_comparison", model=MODEL,
    instruction=COMPARE_PROMPT)

po_drafting = LlmAgent(
    name="po_drafting", model=MODEL,
    instruction=DRAFT_PROMPT, tools=[record_order])

procurement_workflow = SequentialAgent(
    name="procurement_workflow",
    sub_agents=[
        supplier_selection,
        quote_comparison,
        po_drafting,
    ],
)


def next_po_number() -> str:
    return f"PO-{uuid.uuid4().hex[:6].upper()}"


async def run_procurement_workflow(
    sku: str, quantity: int, max_lead_days: int,
) -> dict:
    """Run the three-step ADK sequence (select -> compare ->
    draft) to completion and return the drafted quote as a dict.

    Uses ADK's Runner/session API directly (the SequentialAgent
    itself has no synchronous `.run(dict) -> str` shortcut) --
    the same pattern as lit_review.workflow._run_agent in
    ../12-literature-review."""
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    runner = InMemoryRunner(
        agent=procurement_workflow, app_name=APP_NAME)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id="buyer")
    message = types.Content(
        role="user",
        parts=[types.Part(text=json.dumps({
            "sku": sku, "quantity": quantity,
            "max_lead_days": max_lead_days,
        }))],
    )
    final_text: str | None = None
    async for event in runner.run_async(
        user_id="buyer", session_id=session.id,
        new_message=message,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_text = part.text
    if final_text is None:
        raise RuntimeError(
            "procurement workflow produced no output")
    return json.loads(final_text)
