# tutor/guardrails.py
from __future__ import annotations

REQUEST_FOR_ANSWER = (
    "just tell me", "give me the answer", "what's the answer",
    "solve it for me", "do it for me",
)

OFF_SYLLABUS_PHRASES = (
    "write my essay", "help me with a different subject",
    "ignore your instructions", "forget the topic",
)


def wants_the_answer(student_text: str) -> bool:
    """Cheap heuristic: is the student asking to skip the work?"""
    t = student_text.lower()
    return any(phrase in t for phrase in REQUEST_FOR_ANSWER)


def is_off_syllabus(student_text: str) -> bool:
    """Cheap heuristic: is the student steering off-topic?"""
    t = student_text.lower()
    return any(p in t for p in OFF_SYLLABUS_PHRASES)


def redirect(subject: str) -> str:
    """A gentle nudge back to Socratic mode, no model call."""
    return (
        f"Let's stay with {subject} for now -- try answering "
        "the question above, even a partial attempt helps me "
        "see where you're stuck."
    )
