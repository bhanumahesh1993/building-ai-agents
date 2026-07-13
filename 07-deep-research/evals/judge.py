# evals/judge.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

JUDGE_MODEL = os.getenv(
    "JUDGE_MODEL", "claude-opus-4-5")

_llm = ChatAnthropic(model=JUDGE_MODEL, temperature=0)

RUBRIC = """Grade this research report. Score each
axis 1-5 (5 best). Return JSON only.

- coverage: are the key sub-questions answered?
- citation_accuracy: does every claim map to a
  listed source, with no invented URLs?
- coherence: does it read as one clear argument?

Question:
{question}

Report:
{report}

JSON: {{"coverage": n, "citation_accuracy": n,
"coherence": n, "notes": "..."}}"""


def grade(question: str, report: str) -> dict:
    prompt = RUBRIC.format(
        question=question, report=report)
    return json.loads(_llm.invoke(prompt).content)
