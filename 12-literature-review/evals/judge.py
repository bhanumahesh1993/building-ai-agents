# evals/judge.py
from __future__ import annotations

import json
import os

from google import genai

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "gemini-2.5-pro")
_client = genai.Client()

FAITHFULNESS_RUBRIC = """Grade this cluster summary
against its source abstracts. Score 1-5: does every
claim in the summary trace back to something an
abstract actually says? Return ONLY JSON:
{"faithfulness": n, "unsupported_claims": ["..."]}.

Abstracts:
{abstracts}

Summary:
{summary}"""


def grade_faithfulness(abstracts: str, summary: str) -> dict:
    prompt = FAITHFULNESS_RUBRIC.format(
        abstracts=abstracts, summary=summary)
    resp = _client.models.generate_content(
        model=JUDGE_MODEL, contents=prompt)
    return json.loads(resp.text)
