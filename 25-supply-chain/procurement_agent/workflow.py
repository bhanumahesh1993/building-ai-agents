# procurement_agent/workflow.py
from __future__ import annotations

import os
import uuid

from google.adk.agents import LlmAgent, SequentialAgent

from procurement_agent.mcp_tools import (
    get_quotes, record_order,
)

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
