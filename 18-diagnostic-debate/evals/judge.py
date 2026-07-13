# evals/judge.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

JUDGE_MODEL = os.getenv(
    "JUDGE_MODEL", "claude-opus-4-5")

_llm = ChatAnthropic(model=JUDGE_MODEL, temperature=0)

REASONING_RUBRIC = """Grade this debate transcript as a
RESEARCH artifact, not a clinical one. Score 1-5 on:
- evidence_use: did arguments cite actual findings, not
  vague plausibility?
- engagement: did challenges get real responses, not
  restated confidence?
- appropriate_hedging: did confidence stay proportionate
  to the evidence, without false certainty?
Return ONLY JSON: {{"evidence_use": n, "engagement": n,
"appropriate_hedging": n, "notes": "..."}}

Transcript:
{transcript}"""


def grade_reasoning(transcript: str) -> dict:
    prompt = REASONING_RUBRIC.format(
        transcript=transcript)
    return json.loads(_llm.invoke(prompt).content)
