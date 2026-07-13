# evals/judge.py
from __future__ import annotations

import json
import os

from openai import OpenAI

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gpt-5.1")
_client = OpenAI()

RUBRIC = """Grade this shopping proposal 1-5 on each
axis. Return JSON only.

- search_relevance: were the candidates a sane match
  for the request?
- comparison_faithfulness: does every pro/con trace to
  a real product field, with no invented specs?
- constraint_satisfaction: does the final pick respect
  the stated budget, if any?

Request: {request}
Proposal: {proposal}

JSON: {{"search_relevance": n,
"comparison_faithfulness": n,
"constraint_satisfaction": n, "notes": "..."}}"""


def grade(request: str, proposal: str) -> dict:
    prompt = RUBRIC.format(
        request=request, proposal=proposal)
    resp = _client.chat.completions.create(
        model=JUDGE_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(resp.choices[0].message.content)
