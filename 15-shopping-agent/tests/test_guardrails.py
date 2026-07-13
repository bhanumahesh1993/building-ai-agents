# tests/test_guardrails.py — deterministic checks for the two
# guardrails, called through their raw guardrail_function (the
# same coroutine the SDK invokes) so no live model is needed.
# Plain asyncio.run() is used instead of pytest-asyncio to
# avoid an extra dev dependency for two trivial coroutines.
from __future__ import annotations

import asyncio

import pytest

from shopping.guardrails import MAX_AUTO_CART
from shopping.guardrails import no_claim_guardrail, spend_cap_guardrail


def _run(coro):
    return asyncio.run(coro)


@pytest.mark.parametrize("text", [
    "ANC headphones, budget is $5000",
    "best headphones under 900",
    # regex only captures the integer part of a number, so use
    # a whole-dollar amount one over the cap to stay unambiguous
    f"anything up to ${int(MAX_AUTO_CART) + 1}",
])
def test_spend_cap_trips_over_budget(text):
    out = _run(spend_cap_guardrail.guardrail_function(
        None, None, text))
    assert out.tripwire_triggered is True
    assert out.output_info["over_cap"] is True


@pytest.mark.parametrize("text", [
    "ANC headphones under $150 for flights",
    "quiet in-ear buds, budget is $100",
    "best headphones you have, no budget",
    f"right at the cap, ${int(MAX_AUTO_CART)}",
])
def test_spend_cap_allows_within_budget(text):
    out = _run(spend_cap_guardrail.guardrail_function(
        None, None, text))
    assert out.tripwire_triggered is False
    assert out.output_info["over_cap"] is False


@pytest.mark.parametrize("text", [
    "Your card has been charged, thanks!",
    "Payment successful.",
    "Order confirmed and on its way.",
    "Your purchase complete - enjoy!",
])
def test_no_claim_guardrail_trips_on_claim_language(text):
    out = _run(no_claim_guardrail.guardrail_function(
        None, None, text))
    assert out.tripwire_triggered is True
    assert out.output_info["claimed_purchase"] is True


@pytest.mark.parametrize("text", [
    # Deliberately avoids "charged" (catalog_server's own staged
    # -order text says "nothing charged", which - as a bare
    # keyword match - the regex would flag; that text is never
    # what an agent's final_output should say verbatim).
    "Pending order ord_abc123: $129.00 across 1 line. A human "
    "must approve before any payment is taken.",
    "Here are two candidates to compare.",
])
def test_no_claim_guardrail_allows_pending_language(text):
    out = _run(no_claim_guardrail.guardrail_function(
        None, None, text))
    assert out.tripwire_triggered is False
    assert out.output_info["claimed_purchase"] is False
