# evals/judge.py
from __future__ import annotations

import os

from pydantic import BaseModel
from pydantic_ai import Agent

JUDGE_MODEL = os.getenv("JUDGE_MODEL", "anthropic:claude-sonnet-4-5")


class SocraticScore(BaseModel):
    asks_before_tells: int
    targets_misconception: int
    stays_on_topic: int
    notes: str


_judge: Agent | None = None


def _get_judge() -> Agent:
    """Lazily build so the module imports without a key present."""
    global _judge
    if _judge is None:
        _judge = Agent(JUDGE_MODEL, output_type=SocraticScore)
    return _judge

RUBRIC = """Grade one tutoring exchange on three 1-5
axes (5 best):

- asks_before_tells: does the tutor's question avoid
  stating the fact or answer outright?
- targets_misconception: after a wrong answer, does the
  next question address that specific error rather than
  repeating the same question?
- stays_on_topic: does the exchange stay within
  {subject} and refuse to just hand over the answer?

Subject: {subject}
Prior student answer: {prior_answer}
Tutor's question: {tutor_question}"""


async def grade(
    subject: str, prior_answer: str, tutor_question: str,
) -> SocraticScore:
    prompt = RUBRIC.format(
        subject=subject, prior_answer=prior_answer,
        tutor_question=tutor_question,
    )
    result = await _get_judge().run(prompt)
    return result.output
