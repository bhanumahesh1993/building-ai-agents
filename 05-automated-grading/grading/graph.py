# grading/graph.py
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import InMemorySaver

from .state import BatchState
from .nodes.score import score_node
from .nodes.feedback import feedback_node
from .nodes.similarity import similarity_node
from .nodes.review_gate import review_gate_node


def fan_out_score(state: BatchState):
    """Score any submission not yet scored this round."""
    done = {g["essay_id"] for g in state.get(
        "graded", [])}
    return [
        Send("score", {"submission": s,
                        "prompt": state["prompt"]})
        for s in state["submissions"]
        if s["essay_id"] not in done
    ] or "feedback"


def fan_out_feedback(state: BatchState):
    """Draft feedback for anything freshly scored."""
    pending = [
        g for g in state["graded"]
        if g["status"] == "scored"
    ]
    if not pending:
        return "similarity"
    return [
        Send("feedback", {"graded": g,
                           "prompt": state["prompt"]})
        for g in pending
    ]


def route_after_review(state: BatchState):
    """Loop back only the essays sent for a re-score."""
    returned = [
        g for g in state["graded"]
        if g["status"] == "returned"
    ]
    if returned and state["loops"] < state["max_loops"]:
        return [
            Send("score", {
                "submission": {
                    "student_id": g["student_id"],
                    "essay_id": g["essay_id"],
                    "text": g["text"]},
                "prompt": state["prompt"]})
            for g in returned
        ]
    return "release"


def release_node(state: BatchState) -> dict:
    """Mark approved essays final, roll up the class."""
    approved = [
        g for g in state["graded"]
        if g["status"] == "approved"
    ]
    by_criterion: dict[str, list[int]] = {}
    for g in approved:
        for s in g["scores"]:
            by_criterion.setdefault(
                s["criterion"], []).append(s["points"])
    summary = {
        "n_released": len(approved),
        "n_flagged": sum(
            g["similarity_flag"] for g in approved),
        "avg_by_criterion": {
            k: round(sum(v) / len(v), 2)
            for k, v in by_criterion.items()},
    }
    return {"released": approved, "class_summary": summary}


def build_graph(checkpointer=None):
    g = StateGraph(BatchState)
    g.add_node("score", score_node)
    g.add_node("feedback", feedback_node)
    g.add_node("similarity", similarity_node)
    g.add_node("review", review_gate_node)
    g.add_node("release", release_node)

    g.add_conditional_edges(
        START, fan_out_score, ["score", "feedback"])
    g.add_conditional_edges(
        "score", fan_out_feedback,
        ["feedback", "similarity"])
    g.add_edge("feedback", "similarity")
    g.add_edge("similarity", "review")
    g.add_conditional_edges(
        "review", route_after_review,
        ["score", "release"])
    g.add_edge("release", END)

    cp = checkpointer or InMemorySaver()
    return g.compile(checkpointer=cp)
