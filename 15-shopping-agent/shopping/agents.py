# shopping/agents.py
from __future__ import annotations

import os

from agents import Agent, handoff

from .guardrails import no_claim_guardrail
from .guardrails import spend_cap_guardrail
from .tools import add_to_cart, create_pending_order
from .tools import get_cart, get_product
from .tools import price_cart, search_products

LEAD_MODEL = os.getenv("LEAD_MODEL", "gpt-5.1")
WORKER_MODEL = os.getenv("WORKER_MODEL", "gpt-5.1-mini")

CART_INSTRUCTIONS = """You assemble and price the cart.
Add the shopper's chosen product with add_to_cart, then
call price_cart for a server-computed total - never
state a total you computed yourself. Finish by calling
create_pending_order and show the shopper the exact
itemized total and the pending order id. State plainly
that nothing has been charged and a separate human
confirmation step is required. Never say a purchase is
complete, an order is confirmed, or a card was charged -
you are not able to do any of those things."""

cart_gate = Agent(
    name="Cart & Checkout Gate",
    instructions=CART_INSTRUCTIONS,
    tools=[
        add_to_cart, get_cart,
        price_cart, create_pending_order,
    ],
    output_guardrails=[no_claim_guardrail],
    model=LEAD_MODEL,
)

COMPARE_INSTRUCTIONS = """You compare 2-4 candidates the
search step found. Call get_product on each for full
details. Weigh price, rating, and fit against the
shopper's stated constraints. Write pros and cons per
candidate, then one clear recommendation with a short
rationale. When the shopper picks (or you recommend) a
product, hand off to the Cart & Checkout Gate."""

compare_worker = Agent(
    name="Comparator",
    instructions=COMPARE_INSTRUCTIONS,
    tools=[get_product],
    handoffs=[handoff(cart_gate)],
    model=LEAD_MODEL,
)

SEARCH_INSTRUCTIONS = """You find 2-4 candidate products
matching the shopper's constraints using search_products.
Do not recommend or compare - that is the next agent's
job. Once you have candidates, hand off to the
Comparator with the candidate ids."""

search_worker = Agent(
    name="Product Search",
    instructions=SEARCH_INSTRUCTIONS,
    tools=[search_products, get_product],
    handoffs=[handoff(compare_worker)],
    model=WORKER_MODEL,
)

CONCIERGE_INSTRUCTIONS = """You are the shopping
concierge. Read the shopper's message and extract what
they want: category, must-haves, and budget. Always
carry forward the session_id given in the first message
verbatim on every downstream tool call. Once the intent
is clear, hand off to Product Search."""

concierge = Agent(
    name="Concierge",
    instructions=CONCIERGE_INSTRUCTIONS,
    handoffs=[handoff(search_worker)],
    input_guardrails=[spend_cap_guardrail],
    model=LEAD_MODEL,
)
