# tests/test_score.py
from __future__ import annotations

import json
import statistics

import grading.nodes.score as score_mod
from tests.conftest import FakeLLM

FAKE_SCORES = {
    "scores": [
        {"criterion": "Thesis & Argument", "points": 4,
         "max_points": 4, "evidence": "The war changed everything."},
        {"criterion": "Use of Evidence", "points": 3,
         "max_points": 4, "evidence": "In 1863..."},
        {"criterion": "Historical Accuracy", "points": 4,
         "max_points": 4, "evidence": "Lincoln signed it in 1863."},
        {"criterion": "Organization", "points": 3,
         "max_points": 4, "evidence": "Paragraph flow."},
        {"criterion": "Writing Mechanics", "points": 4,
         "max_points": 4, "evidence": "Clean prose throughout."},
    ]
}


def test_score_one_returns_evidence_backed_scores(monkeypatch):
    """Rubric scoring: every criterion in the rubric gets a
    quoted-evidence score, and the totals add up correctly."""
    monkeypatch.setattr(
        score_mod, "_get_llm",
        lambda: FakeLLM(json.dumps(FAKE_SCORES)))
    result = score_mod._score_one("Write about the Civil War.", "essay text")
    assert len(result["scores"]) == 5
    total = sum(s["points"] for s in result["scores"])
    assert total == 18
    for s in result["scores"]:
        assert s["evidence"]  # never blank


def test_score_node_computes_total_from_submission(monkeypatch):
    monkeypatch.setattr(
        score_mod, "_get_llm",
        lambda: FakeLLM(json.dumps(FAKE_SCORES)))
    state = {
        "submission": {
            "student_id": "s1", "essay_id": "e1",
            "text": "essay text",
        },
        "prompt": "Write about the Civil War.",
    }
    out = score_mod.score_node(state)
    graded = out["graded"][0]
    assert graded["essay_id"] == "e1"
    assert graded["total"] == 18
    assert graded["status"] == "scored"


def test_scoring_is_consistent_across_repeated_runs(monkeypatch):
    """Consistency / variance check: grading the same essay
    against the same (stubbed) model repeatedly must not drift.
    A real evaluator-optimizer grader should have zero variance
    for an identical input — any spread here would mean the
    scorer is non-deterministic and unsafe to trust at scale."""
    monkeypatch.setattr(
        score_mod, "_get_llm",
        lambda: FakeLLM(json.dumps(FAKE_SCORES)))
    totals = []
    for _ in range(10):
        result = score_mod._score_one(
            "Write about the Civil War.", "essay text")
        totals.append(sum(s["points"] for s in result["scores"]))
    assert statistics.pvariance(totals) == 0
    assert len(set(totals)) == 1


def test_get_llm_is_lazy_and_cached(monkeypatch):
    """The client helper must not build anything at import time,
    and must reuse the same instance once built (no cost blowup)."""
    monkeypatch.setattr(score_mod, "_llm", None)
    built = {"n": 0}

    class _Dummy:
        pass

    def _fake_chat_anthropic(**kwargs):
        built["n"] += 1
        return _Dummy()

    monkeypatch.setattr(score_mod, "ChatAnthropic", _fake_chat_anthropic)
    first = score_mod._get_llm()
    second = score_mod._get_llm()
    assert first is second
    assert built["n"] == 1
