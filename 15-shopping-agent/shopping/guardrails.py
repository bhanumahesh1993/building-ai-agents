# shopping/guardrails.py
from __future__ import annotations

import os
import re

from agents import (
    GuardrailFunctionOutput,
    input_guardrail,
    output_guardrail,
)

MAX_AUTO_CART = float(os.getenv("MAX_AUTO_CART", "750"))

_CLAIM_WORDS = re.compile(
    r"\b(charged|payment (was )?successful|"
    r"order confirmed|purchase complete)\b",
    re.IGNORECASE,
)


@input_guardrail
async def spend_cap_guardrail(ctx, agent, user_input):
    """Trip if the shopper's stated budget is too high
    for autonomous cart assembly - route to a human."""
    text = str(user_input)
    nums = re.findall(r"\$?(\d{2,6})(?:\.\d+)?", text)
    over_cap = any(
        float(n) > MAX_AUTO_CART for n in nums)
    return GuardrailFunctionOutput(
        output_info={
            "over_cap": over_cap, "cap": MAX_AUTO_CART},
        tripwire_triggered=over_cap,
    )


@output_guardrail
async def no_claim_guardrail(ctx, agent, output):
    """Trip if the agent ever claims a purchase is
    done. It may only stage a pending order."""
    claimed = bool(_CLAIM_WORDS.search(str(output)))
    return GuardrailFunctionOutput(
        output_info={"claimed_purchase": claimed},
        tripwire_triggered=claimed,
    )
