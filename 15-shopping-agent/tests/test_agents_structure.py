# tests/test_agents_structure.py — comparison-faithfulness is,
# like the payment gate, enforced structurally rather than by
# prompt: the Comparator's only tool is get_product, so every
# pro/con it writes must trace back to a real, freshly-fetched
# product field - it has no other tool that could supply (or
# let it invent) a spec. These tests pin that structure.
from __future__ import annotations

from shopping.agents import (
    get_cart_gate, get_compare_worker,
    get_concierge, get_search_worker,
)
from shopping.guardrails import no_claim_guardrail, spend_cap_guardrail
from shopping.tools import get_product


def test_comparator_is_grounded_only_in_get_product():
    """The Comparator cannot fabricate specs: get_product -
    which returns real catalog fields - is its only tool."""
    worker = get_compare_worker()
    assert [t.name for t in worker.tools] == ["get_product"]
    assert worker.tools[0] is get_product


def test_comparator_instructions_require_a_tool_call_per_candidate():
    instructions = get_compare_worker().instructions
    assert "get_product" in instructions
    assert "pros and cons" in instructions


def test_search_worker_cannot_compare_or_price():
    """Search only has search/lookup tools - no pricing or cart
    tool exists to let it shortcut past the Comparator."""
    worker = get_search_worker()
    names = {t.name for t in worker.tools}
    assert names == {"search_products", "get_product"}
    assert "Do not recommend or compare" in worker.instructions


def test_agent_chain_hands_off_in_documented_order():
    concierge = get_concierge()
    search = get_search_worker()
    compare = get_compare_worker()

    concierge_targets = {h.agent_name for h in concierge.handoffs}
    assert concierge_targets == {"Product Search"}

    search_targets = {h.agent_name for h in search.handoffs}
    assert search_targets == {"Comparator"}

    compare_targets = {h.agent_name for h in compare.handoffs}
    assert compare_targets == {"Cart & Checkout Gate"}


def test_concierge_has_the_spend_cap_input_guardrail():
    concierge = get_concierge()
    assert spend_cap_guardrail in concierge.input_guardrails


def test_cart_gate_has_the_no_claim_output_guardrail():
    gate = get_cart_gate()
    assert no_claim_guardrail in gate.output_guardrails
