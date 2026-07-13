# grading/rubric.py
from __future__ import annotations

from typing import TypedDict


class Criterion(TypedDict):
    name: str
    description: str
    max_points: int


RUBRIC: list[Criterion] = [
    {"name": "Thesis & Argument",
     "description": "States a clear, arguable position "
                     "and sustains it throughout.",
     "max_points": 4},
    {"name": "Use of Evidence",
     "description": "Cites specific facts or events "
                     "that actually support the thesis.",
     "max_points": 4},
    {"name": "Historical Accuracy",
     "description": "Dates, names, and events are "
                     "correct and not overstated.",
     "max_points": 4},
    {"name": "Organization",
     "description": "Paragraphs build logically toward "
                     "the conclusion.",
     "max_points": 4},
    {"name": "Writing Mechanics",
     "description": "Grammar, spelling, and sentence "
                     "clarity do not obstruct the "
                     "argument.",
     "max_points": 4},
]

TOTAL_POINTS = sum(c["max_points"] for c in RUBRIC)


def rubric_block(rubric: list[Criterion] = RUBRIC) -> str:
    """Render the rubric as a numbered prompt block."""
    lines = [
        f"- {c['name']} (0-{c['max_points']}): "
        f"{c['description']}"
        for c in rubric
    ]
    return "\n".join(lines)
