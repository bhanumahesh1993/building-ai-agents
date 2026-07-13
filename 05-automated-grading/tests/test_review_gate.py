# tests/test_review_gate.py
from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command

from grading.nodes.review_gate import review_gate_node
from grading.state import BatchState

GRADED_ESSAY = {
    "essay_id": "e1", "student_id": "s1",
    "text": "essay text",
    "scores": [{"criterion": "Thesis & Argument", "points": 4,
                "max_points": 4, "evidence": "quote"}],
    "total": 4, "feedback": "Nice work.",
    "similarity_flag": False, "similarity_notes": "",
    "status": "screened",
}


def _build_gate_graph():
    """Minimal graph isolating just the human sign-off gate,
    so the HITL pause/resume contract is tested without needing
    real scoring/feedback/similarity model calls."""
    g = StateGraph(BatchState)
    g.add_node("review", review_gate_node)
    g.add_edge(START, "review")
    g.add_edge("review", END)
    return g.compile(checkpointer=InMemorySaver())


def test_review_gate_pauses_with_a_queue_for_the_human():
    graph = _build_gate_graph()
    cfg = {"configurable": {"thread_id": "gate-1"}}
    state = graph.invoke(
        {"graded": [GRADED_ESSAY], "loops": 0}, config=cfg)

    assert "__interrupt__" in state
    queue = state["__interrupt__"][0].value["queue"]
    assert len(queue) == 1
    assert queue[0]["essay_id"] == "e1"
    assert queue[0]["total"] == 4


def test_review_gate_only_queues_screened_essays():
    graph = _build_gate_graph()
    cfg = {"configurable": {"thread_id": "gate-2"}}
    not_yet_screened = {**GRADED_ESSAY, "essay_id": "e2",
                        "status": "scored"}
    state = graph.invoke(
        {"graded": [GRADED_ESSAY, not_yet_screened], "loops": 0},
        config=cfg)
    queue = state["__interrupt__"][0].value["queue"]
    assert [q["essay_id"] for q in queue] == ["e1"]


def test_review_gate_resume_approve_marks_essay_approved():
    graph = _build_gate_graph()
    cfg = {"configurable": {"thread_id": "gate-3"}}
    graph.invoke({"graded": [GRADED_ESSAY], "loops": 0}, config=cfg)

    state = graph.invoke(
        Command(resume={
            "approve": ["e1"], "return_for_rescore": [], "edits": {},
        }),
        config=cfg,
    )
    assert state["graded"][0]["status"] == "approved"
    assert state["loops"] == 1


def test_review_gate_resume_return_for_rescore():
    graph = _build_gate_graph()
    cfg = {"configurable": {"thread_id": "gate-4"}}
    graph.invoke({"graded": [GRADED_ESSAY], "loops": 0}, config=cfg)

    state = graph.invoke(
        Command(resume={
            "approve": [], "return_for_rescore": ["e1"], "edits": {},
        }),
        config=cfg,
    )
    assert state["graded"][0]["status"] == "returned"


def test_review_gate_resume_applies_teacher_edits():
    """A teacher can hand-adjust a score before it's released —
    the gate must apply the edit, not just approve/reject."""
    graph = _build_gate_graph()
    cfg = {"configurable": {"thread_id": "gate-5"}}
    graph.invoke({"graded": [GRADED_ESSAY], "loops": 0}, config=cfg)

    state = graph.invoke(
        Command(resume={
            "approve": ["e1"], "return_for_rescore": [],
            "edits": {"e1": {"total": 5}},
        }),
        config=cfg,
    )
    graded = state["graded"][0]
    assert graded["total"] == 5
    assert graded["status"] == "approved"


def test_release_never_happens_without_a_human_decision():
    """Structural guarantee: without a resume, nothing is
    ever marked approved/released — the gate is not bypassable."""
    graph = _build_gate_graph()
    cfg = {"configurable": {"thread_id": "gate-6"}}
    state = graph.invoke(
        {"graded": [GRADED_ESSAY], "loops": 0}, config=cfg)
    assert "released" not in state
    assert state["graded"][0]["status"] == "screened"
