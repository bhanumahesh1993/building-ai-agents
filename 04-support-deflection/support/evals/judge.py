# support/evals/judge.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

JUDGE_MODEL = os.getenv(
    "JUDGE_MODEL", "claude-opus-4-5")

_llm: ChatAnthropic | None = None


def _get_llm() -> ChatAnthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _llm
    if _llm is None:
        _llm = ChatAnthropic(model=JUDGE_MODEL, temperature=0)
    return _llm


RUBRIC = """Grade whether this support answer is
faithful to its cited sources. Score 1-5 (5 best).

- faithfulness: is every claim traceable to one of
  the cited KB passages, with nothing invented?
- helpfulness: does it actually resolve the request?

Return JSON only.

Customer message: {message}
Answer: {answer}
Cited passages: {citations}

JSON: {{"faithfulness": n, "helpfulness": n,
"notes": "..."}}"""


def grade(message: str, answer: str,
          citations: list[str]) -> dict:
    prompt = RUBRIC.format(
        message=message, answer=answer,
        citations="\n".join(citations))
    return json.loads(_get_llm().invoke(prompt).content)
