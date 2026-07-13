# evals/judge.py
from __future__ import annotations

import os

from pydantic import BaseModel
from pydantic_ai import Agent

JUDGE_MODEL = os.getenv(
    "JUDGE_MODEL", "anthropic:claude-opus-4-5")


class HallucinationCheck(BaseModel):
    unsupported_count: int
    unsupported_examples: list[str]


judge = Agent(
    JUDGE_MODEL, output_type=HallucinationCheck)

RUBRIC = """You are a strict clinical-chart auditor.
Given the transcript and the FINAL (post-verification,
signed-quality) note claims below, count how many
claims are NOT actually supported by the transcript --
even ones the pipeline's own verifier already passed.
This is a check on the checker: find anything that
still slipped through.

Transcript:
{transcript}

Final claims:
{claims}"""


async def hallucination_rate(
        transcript: str, claims: list[str],
) -> HallucinationCheck:
    prompt = RUBRIC.format(
        transcript=transcript,
        claims="\n".join(f"- {c}" for c in claims))
    result = await judge.run(prompt)
    return result.output
