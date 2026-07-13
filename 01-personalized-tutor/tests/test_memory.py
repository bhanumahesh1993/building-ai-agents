# tests/test_memory.py
from __future__ import annotations

import tutor.memory as memory
from tutor.models import (
    DiagnosticResult, LessonPlan, LessonTopic, TurnFeedback,
)


def test_init_db_creates_tables(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(memory, "DB_PATH", str(db_path))
    memory.init_db()
    assert db_path.exists()


def test_save_and_recall_weak_areas(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(memory, "DB_PATH", str(db_path))
    memory.init_db()

    result = DiagnosticResult(
        level="beginner",
        topic_scores={"limits": 0.3},
        weak_areas=["limit of a rational function at a hole"],
        rationale="struggled with holes",
    )
    memory.save_diagnostic("student-1", "calculus", result)

    areas = memory.recent_weak_areas("student-1", "calculus")
    assert areas == ["limit of a rational function at a hole"]


def test_recent_weak_areas_dedupes_across_sessions(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(memory, "DB_PATH", str(db_path))
    memory.init_db()

    first = DiagnosticResult(
        level="beginner", topic_scores={"limits": 0.3},
        weak_areas=["holes"], rationale="r1",
    )
    second = DiagnosticResult(
        level="intermediate", topic_scores={"limits": 0.5},
        weak_areas=["holes", "chain rule"], rationale="r2",
    )
    memory.save_diagnostic("student-1", "calculus", first)
    memory.save_diagnostic("student-1", "calculus", second)

    areas = memory.recent_weak_areas("student-1", "calculus")
    assert areas == ["holes", "chain rule"]


def test_save_plan_roundtrip(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(memory, "DB_PATH", str(db_path))
    memory.init_db()

    plan = LessonPlan(
        topics=[LessonTopic(
            name="limits", objective="find limits",
            difficulty="easy",
        )],
        est_minutes=20,
    )
    memory.save_plan("student-1", "calculus", plan)

    with memory._conn() as conn:
        rows = conn.execute("SELECT * FROM plans").fetchall()
    assert len(rows) == 1
    assert rows[0]["subject"] == "calculus"


def test_record_turn_persists_feedback(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(memory, "DB_PATH", str(db_path))
    memory.init_db()

    feedback = TurnFeedback(
        correct=False, misconception="sign error",
        next_difficulty="easier", hint="check the sign",
    )
    memory.record_turn(
        "student-1", "calculus", "limits", "medium",
        "what is lim...", "wrong answer", feedback,
    )

    with memory._conn() as conn:
        rows = conn.execute("SELECT * FROM turns").fetchall()
    assert len(rows) == 1
    assert rows[0]["correct"] == 0
    assert rows[0]["misconception"] == "sign error"
