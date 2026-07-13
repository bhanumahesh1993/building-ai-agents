# aml/guardrails.py
from __future__ import annotations

import re

from agents import (
    GuardrailFunctionOutput,
    input_guardrail,
    output_guardrail,
)

_IMPERATIVE = re.compile(
    r"\b(ignore (all|previous) instructions|"
    r"disregard the (above|prior)|"
    r"you must (now |immediately )?"
    r"(approve|file|close))\b",
    re.IGNORECASE,
)

_FILED_CLAIM = re.compile(
    r"\b(has been filed|submitted to fincen|"
    r"sar (was |is )?filed|filing complete)\b",
    re.IGNORECASE,
)


def sanitize_memo(text: str) -> str:
    """Neutralize instruction-shaped memo text before it
    reaches a prompt. This is the tool-response
    checkpoint, done in code -- the SDK's own guardrails
    only wrap an agent's overall input and output, not
    each tool call in between, so this layer has to be
    built by hand."""
    if _IMPERATIVE.search(text):
        return (
            "[REDACTED -- memo contained instruction-"
            "shaped text, treated as evidence of "
            "tampering, not as a command] "
            + text[:80])
    return text


@input_guardrail
async def case_intake_guardrail(ctx, agent, case_input):
    """Trip if a case payload is malformed or absurdly
    large, before any model spends a token on it."""
    text = str(case_input)
    too_large = len(text) > 50_000
    return GuardrailFunctionOutput(
        output_info={"too_large": too_large},
        tripwire_triggered=too_large,
    )


@output_guardrail
async def explainability_guardrail(ctx, agent, output):
    """Trip if a SAR draft cites no evidence. Regulators
    do not accept an unexplained score, and this system
    should not produce one either."""
    text = str(output)
    has_citations = bool(
        re.search(r"\btxn_[a-z0-9_]+\b", text))
    return GuardrailFunctionOutput(
        output_info={"has_citations": has_citations},
        tripwire_triggered=not has_citations,
    )


@output_guardrail
async def no_filing_claim_guardrail(ctx, agent, output):
    """Trip if a draft ever claims to have been filed.
    Nothing in this codebase can file a SAR -- if the
    text says otherwise, the text is simply wrong."""
    claimed = bool(_FILED_CLAIM.search(str(output)))
    return GuardrailFunctionOutput(
        output_info={"claimed_filed": claimed},
        tripwire_triggered=claimed,
    )


def redact_pii(text: str) -> str:
    """Mask SSNs and account numbers before case data
    leaves the process boundary for tracing. The audit
    log inside the system keeps real values; anything
    exported to a third-party dashboard does not."""
    text = re.sub(
        r"\b\d{3}-\d{2}-\d{4}\b", "***-**-****", text)
    text = re.sub(
        r"\b\d{10,17}\b",
        lambda m: "*" * len(m.group()), text)
    return text
