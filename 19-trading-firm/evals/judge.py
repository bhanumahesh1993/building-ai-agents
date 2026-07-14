# evals/judge.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "claude-opus-4-5")

_llm: ChatAnthropic | None = None


def _get_llm() -> ChatAnthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _llm
    if _llm is None:
        _llm = ChatAnthropic(
            model=JUDGE_MODEL, temperature=0)
    return _llm

RUBRIC = """Grade this paper-trading decision cycle. This is
a RESEARCH system — grade the REASONING, never whether a
market later agreed with it. Score each axis 1-5.

- reasoning_soundness: is the rationale grounded in the
  analyst views and debate, not generic?
- disconfirming_evidence: did the trader/manager engage the
  strongest opposing argument instead of ignoring it?
- debate_balance: did both sides land a specific point?

Debate: {debate}
Proposal: {proposal}
Risk verdict: {risk}
Decision: {decision}

JSON only: {{"reasoning_soundness": n,
"disconfirming_evidence": n, "debate_balance": n,
"notes": "..."}}"""


def grade(state: dict) -> dict:
    prompt = RUBRIC.format(
        debate=state["debate"], proposal=state["proposal"],
        risk=state["risk"], decision=state["decision"])
    return json.loads(_get_llm().invoke(prompt).content)
