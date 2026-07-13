# tutor/agents.py
from __future__ import annotations

import os

from pydantic_ai import Agent

from .models import (
    DiagnosticResult, LessonPlan, TurnFeedback, TutorTurn,
)

MODEL = os.getenv("TUTOR_MODEL", "anthropic:claude-haiku-4-5")

diagnostic_agent = Agent(MODEL, output_type=DiagnosticResult)
planner_agent = Agent(MODEL, output_type=LessonPlan)
tutor_agent = Agent(MODEL, output_type=TutorTurn)
evaluator_agent = Agent(MODEL, output_type=TurnFeedback)
