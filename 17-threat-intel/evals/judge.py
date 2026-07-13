# evals/judge.py
from __future__ import annotations

import json
import os

from crewai import LLM

JUDGE_MODEL = os.getenv(
    "JUDGE_MODEL", "anthropic/claude-opus-4-5")
_llm = LLM(model=JUDGE_MODEL, temperature=0)

RUBRIC = """Grade this threat brief. Score each axis
1-5 (5 best). JSON only.

- citation_accuracy: does every claim trace to a CVE ID
  actually present in the ranked list below?
- hedge_discipline: does the brief avoid upgrading
  'reported' or 'possible' exploitation to 'confirmed'
  language the ranked list itself did not use?
- coverage: does the brief surface the actual top-
  ranked items, not bury them under lower-priority ones?

Ranked list:
{ranked_list}

Brief:
{brief}

JSON: {{"citation_accuracy": n, "hedge_discipline": n,
"coverage": n, "notes": "..."}}"""


def grade(ranked_list: str, brief: str) -> dict:
    prompt = RUBRIC.format(
        ranked_list=ranked_list, brief=brief)
    return json.loads(_llm.call(prompt))
