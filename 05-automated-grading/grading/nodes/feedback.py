# grading/nodes/feedback.py
from __future__ import annotations

import os

from langchain_anthropic import ChatAnthropic

from ..state import FeedbackWorkerState

FEEDBACK_MODEL = os.getenv(
    "FEEDBACK_MODEL", "claude-sonnet-4-5")

_llm: ChatAnthropic | None = None


def _get_llm() -> ChatAnthropic:
    """Lazily build so the module imports without a key present."""
    global _llm
    if _llm is None:
        _llm = ChatAnthropic(
            model=FEEDBACK_MODEL, temperature=0.3)
    return _llm


FEEDBACK_SYSTEM = """You are writing feedback directly
to a student, using their rubric scores below. Write
3-5 sentences: one thing that worked, quoting their
own words; one thing to improve, quoting or pointing
to a specific spot; one concrete next step. Be warm
and specific. Never mention a number score. Never say
"the AI" or "the system" — write as their teacher's
assistant would.

Prompt: {prompt}

Scores (with evidence):
{scores}

Essay:
{essay}"""


def feedback_node(state: FeedbackWorkerState) -> dict:
    """One worker: turn one essay's scores into a note
    the student can act on."""
    g = state["graded"]
    prompt = FEEDBACK_SYSTEM.format(
        prompt=state["prompt"],
        scores=g["scores"],
        essay=g["text"],
    )
    resp = _get_llm().invoke(prompt)
    updated = {**g, "feedback": resp.content,
               "status": "drafted"}
    return {"graded": [updated]}
