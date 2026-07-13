# grading/nodes/score.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..rubric import RUBRIC, rubric_block
from ..state import EssayWorkerState

SCORE_MODEL = os.getenv(
    "SCORE_MODEL", "claude-opus-4-5")

_llm = ChatAnthropic(model=SCORE_MODEL, temperature=0)

SCORE_SYSTEM = """You are a rubric scorer. Score ONE
student essay against the rubric below. For every
criterion, quote the exact sentence from the essay
that earned or lost the points — never invent or
paraphrase a quote. If nothing in the essay addresses
a criterion, award 0 and say so plainly.

Grade this essay alone. Do not compare it to other
essays, and do not soften a score to be kind — that
is a later step's job, not yours.

Prompt: {prompt}

Rubric:
{rubric}

Essay:
{essay}

Return ONLY JSON:
{{"scores": [
  {{"criterion": "name", "points": n,
    "max_points": n, "evidence": "quoted text"}}
]}}"""


def _score_one(prompt: str, essay: str) -> dict:
    """Score one essay text; used by the node and
    by the calibration eval, so both paths agree."""
    text = SCORE_SYSTEM.format(
        prompt=prompt,
        rubric=rubric_block(RUBRIC),
        essay=essay,
    )
    resp = _llm.invoke(text)
    return json.loads(resp.content)


def score_node(state: EssayWorkerState) -> dict:
    """One worker: score one essay, evidence required."""
    sub = state["submission"]
    result = _score_one(state["prompt"], sub["text"])
    scores = result["scores"]
    graded = {
        "essay_id": sub["essay_id"],
        "student_id": sub["student_id"],
        "text": sub["text"],
        "scores": scores,
        "total": sum(s["points"] for s in scores),
        "feedback": "",
        "similarity_flag": False,
        "similarity_notes": "",
        "status": "scored",
    }
    return {"graded": [graded]}
