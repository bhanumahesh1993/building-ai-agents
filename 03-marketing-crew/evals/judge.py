# evals/judge.py
from __future__ import annotations

import json
import os

from crewai import LLM

JUDGE_MODEL = os.getenv(
    "JUDGE_MODEL", "anthropic/claude-opus-4-5")
_llm = LLM(model=JUDGE_MODEL, temperature=0)

RUBRIC = """Grade this campaign kit against the
brief. Score each axis 1-5 (5 best). JSON only.

- voice_match: does the copy sound like the brand
  guide, not generic marketing?
- claims_discipline: does every claim trace back to
  the brief's key_facts, nothing invented?
- cta_clarity: is there one clear next action?

Brief:
{brief}

Blog post:
{blog}

JSON: {{"voice_match": n, "claims_discipline": n,
"cta_clarity": n, "notes": "..."}}"""


def grade(brief: dict, blog_body: str) -> dict:
    prompt = RUBRIC.format(
        brief=json.dumps(brief), blog=blog_body)
    return json.loads(_llm.call(prompt))
