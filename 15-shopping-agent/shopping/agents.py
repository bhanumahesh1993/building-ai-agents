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

COMPARE_INSTRUCTIONS = """You compare 2-4 candidates the
search step found. Call get_product on each for full
details. Weigh price, rating, and fit against the
shopper's stated constraints. Write pros and cons per
candidate, then one clear recommendation with a short
rationale. When the shopper picks (or you recommend) a
product, hand off to the Cart & Checkout Gate."""

SEARCH_INSTRUCTIONS = """You find 2-4 candidate products
matching the shopper's constraints using search_products.
Do not recommend or compare - that is the next agent's
job. Once you have candidates, hand off to the
Comparator with the candidate ids."""

CONCIERGE_INSTRUCTIONS = """You are the shopping
concierge. Read the shopper's message and extract what
they want: category, must-haves, and budget. Always
carry forward the session_id given in the first message
verbatim on every downstream tool call. Once the intent
is clear, hand off to Product Search."""

# Agents (and the OpenAI client they build under the hood) are
# constructed lazily behind get_*() helpers so importing this
# module - or shopping.app - never requires OPENAI_API_KEY or
# any other env var to be set. Built in dependency order:
# cart_gate first (leaf), then compare_worker, search_worker,
# concierge (each hands off to the previous one).
_cart_gate: Agent | None = None
_compare_worker: Agent | None = None
_search_worker: Agent | None = None
_concierge: Agent | None = None


def get_cart_gate() -> Agent:
    """Lazily build so the module imports without a key present.

    NOTE for reviewers of the payment-authorization gate: this
    agent's tools list is intentionally
    [add_to_cart, get_cart, price_cart, create_pending_order]
    only. There is no spend/confirm tool here or anywhere else
    in this module - see shopping/tools.py, which never wraps
    catalog_server.confirm_order with @function_tool. The stop
    is an absence of capability, not a prompt instruction.
    """
    global _cart_gate
    if _cart_gate is None:
        _cart_gate = Agent(
            name="Cart & Checkout Gate",
            instructions=CART_INSTRUCTIONS,
            tools=[
                add_to_cart, get_cart,
                price_cart, create_pending_order,
            ],
            output_guardrails=[no_claim_guardrail],
            model=LEAD_MODEL,
        )
    return _cart_gate


def get_compare_worker() -> Agent:
    """Lazily build so the module imports without a key present."""
    global _compare_worker
    if _compare_worker is None:
        _compare_worker = Agent(
            name="Comparator",
            instructions=COMPARE_INSTRUCTIONS,
            tools=[get_product],
            handoffs=[handoff(get_cart_gate())],
            model=LEAD_MODEL,
        )
    return _compare_worker


def get_search_worker() -> Agent:
    """Lazily build so the module imports without a key present."""
    global _search_worker
    if _search_worker is None:
        _search_worker = Agent(
            name="Product Search",
            instructions=SEARCH_INSTRUCTIONS,
            tools=[search_products, get_product],
            handoffs=[handoff(get_compare_worker())],
            model=WORKER_MODEL,
        )
    return _search_worker


def get_concierge() -> Agent:
    """Lazily build so the module imports without a key present."""
    global _concierge
    if _concierge is None:
        _concierge = Agent(
            name="Concierge",
            instructions=CONCIERGE_INSTRUCTIONS,
            handoffs=[handoff(get_search_worker())],
            input_guardrails=[spend_cap_guardrail],
            model=LEAD_MODEL,
        )
    return _concierge


def all_agents() -> list[Agent]:
    """All four agents in the chain, for gate audits/tests."""
    return [
        get_concierge(), get_search_worker(),
        get_compare_worker(), get_cart_gate(),
    ]
