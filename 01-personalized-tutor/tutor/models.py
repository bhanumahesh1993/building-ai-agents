# tutor/models.py
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Difficulty = Literal["easy", "medium", "hard"]


class DiagnosticResult(BaseModel):
    """Where the student stands after the short quiz."""
    level: Literal["beginner", "intermediate", "advanced"]
    topic_scores: dict[str, float] = Field(
        description="0-1 mastery score per topic probed")
    weak_areas: list[str] = Field(
        description="specific concepts, not whole subjects")
    rationale: str


class LessonTopic(BaseModel):
    """One stop on the student's study path."""
    name: str
    objective: str
    difficulty: Difficulty


class LessonPlan(BaseModel):
    """The planner's ordered sequence of topics."""
    topics: list[LessonTopic] = Field(min_length=1, max_length=6)
    est_minutes: int = Field(ge=5, le=90)


class TutorTurn(BaseModel):
    """One Socratic question -- never a lecture."""
    question: str
    topic: str
    difficulty: Difficulty


class TurnFeedback(BaseModel):
    """The evaluator's read on one student answer."""
    correct: bool
    misconception: str | None = None
    next_difficulty: Literal["easier", "same", "harder"]
    hint: str | None = None
