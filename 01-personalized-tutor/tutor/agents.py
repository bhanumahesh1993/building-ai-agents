# tutor/agents.py
from __future__ import annotations

import os

from pydantic_ai import Agent

from .models import (
    DiagnosticResult, LessonPlan, TurnFeedback, TutorTurn,
)

MODEL = os.getenv("TUTOR_MODEL", "anthropic:claude-haiku-4-5")

_diagnostic_agent: Agent | None = None
_planner_agent: Agent | None = None
_tutor_agent: Agent | None = None
_evaluator_agent: Agent | None = None


def get_diagnostic_agent() -> Agent:
    """Lazily build so the module imports without a key present."""
    global _diagnostic_agent
    if _diagnostic_agent is None:
        _diagnostic_agent = Agent(MODEL, output_type=DiagnosticResult)
    return _diagnostic_agent


def get_planner_agent() -> Agent:
    """Lazily build so the module imports without a key present."""
    global _planner_agent
    if _planner_agent is None:
        _planner_agent = Agent(MODEL, output_type=LessonPlan)
    return _planner_agent


def get_tutor_agent() -> Agent:
    """Lazily build so the module imports without a key present."""
    global _tutor_agent
    if _tutor_agent is None:
        _tutor_agent = Agent(MODEL, output_type=TutorTurn)
    return _tutor_agent


def get_evaluator_agent() -> Agent:
    """Lazily build so the module imports without a key present."""
    global _evaluator_agent
    if _evaluator_agent is None:
        _evaluator_agent = Agent(MODEL, output_type=TurnFeedback)
    return _evaluator_agent
