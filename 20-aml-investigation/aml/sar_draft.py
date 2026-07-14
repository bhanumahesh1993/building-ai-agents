# aml/sar_draft.py
from __future__ import annotations

import os

from agents import Agent

from .guardrails import (
    explainability_guardrail,
    no_filing_claim_guardrail,
)

DRAFT_MODEL = os.getenv("DRAFT_MODEL", "gpt-5.1")

SAR_INSTRUCTIONS = """You draft a Suspicious Activity
Report narrative from an investigation's narrative and
typology matches. Follow this shape: (1) subject and
account, (2) the pattern observed, in plain language,
(3) a timeline citing transaction ids, (4) which
typology it resembles and why, (5) an explicit evidence
list citing every transaction id used above.

Begin with the line "DRAFT -- NOT FILED. Prepared for
compliance officer review." Never write, imply, or hint
that this report has been, or could be, submitted by
you. You have no ability to file anything. Use hedged,
factual language ("the transactions are consistent
with...") -- never assert that a crime occurred. A
human compliance officer makes that judgment, not you."""

# The Agent (and the OpenAI client it builds under the hood) is
# constructed lazily behind get_sar_drafter() so importing this
# module -- or aml.app -- never requires OPENAI_API_KEY or any
# other env var to be set.
_sar_drafter: Agent | None = None


def get_sar_drafter() -> Agent:
    """Lazily build so the module imports without a key present."""
    global _sar_drafter
    if _sar_drafter is None:
        _sar_drafter = Agent(
            name="SAR Drafter",
            instructions=SAR_INSTRUCTIONS,
            output_guardrails=[
                explainability_guardrail,
                no_filing_claim_guardrail,
            ],
            model=DRAFT_MODEL,
        )
    return _sar_drafter
