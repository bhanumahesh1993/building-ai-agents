# tutor/memory.py
from __future__ import annotations

import json
import os
import sqlite3
import time

from .models import DiagnosticResult, LessonPlan, TurnFeedback

DB_PATH = os.getenv("TUTOR_DB_PATH", "tutor.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS diagnostics (
    student_id TEXT, subject TEXT, level TEXT,
    weak_areas TEXT, rationale TEXT, created_at REAL
);
CREATE TABLE IF NOT EXISTS plans (
    student_id TEXT, subject TEXT, topics TEXT,
    created_at REAL
);
CREATE TABLE IF NOT EXISTS turns (
    student_id TEXT, subject TEXT, topic TEXT,
    difficulty TEXT, question TEXT, answer TEXT,
    correct INTEGER, misconception TEXT, created_at REAL
);
"""


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the three tables if this is a fresh install."""
    with _conn() as conn:
        conn.executescript(SCHEMA)


def save_diagnostic(
    student_id: str, subject: str, result: DiagnosticResult,
) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO diagnostics VALUES (?, ?, ?, ?, ?, ?)",
            (student_id, subject, result.level,
             json.dumps(result.weak_areas), result.rationale,
             time.time()),
        )


def save_plan(
    student_id: str, subject: str, plan: LessonPlan,
) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO plans VALUES (?, ?, ?, ?)",
            (student_id, subject,
             json.dumps([t.model_dump() for t in plan.topics]),
             time.time()),
        )


def record_turn(
    student_id: str, subject: str, topic: str, difficulty: str,
    question: str, answer: str, feedback: TurnFeedback,
) -> None:
    with _conn() as conn:
        conn.execute(
            "INSERT INTO turns VALUES "
            "(?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (student_id, subject, topic, difficulty, question,
             answer, int(feedback.correct), feedback.misconception,
             time.time()),
        )


def recent_weak_areas(
    student_id: str, subject: str, limit: int = 5,
) -> list[str]:
    """Weak areas from past sessions, most recent first."""
    with _conn() as conn:
        rows = conn.execute(
            "SELECT weak_areas FROM diagnostics WHERE "
            "student_id = ? AND subject = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (student_id, subject, limit),
        ).fetchall()
    areas: list[str] = []
    for row in rows:
        for a in json.loads(row["weak_areas"]):
            if a not in areas:
                areas.append(a)
    return areas
