# review/graph.py
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import InMemorySaver

from .state import ReviewState
from .nodes.gather import gather_node
from .nodes.reviewers import review_node, ROLES
from .nodes.verify import verify_node
from .nodes.consolidate import consolidate_node
from .nodes.gate import gate_node

MAX_FINDINGS_TOTAL = 24


def fan_out_reviewers(state: ReviewState):
    return [
        Send("review", {
            "role": role, "hunks": state["hunks"],
            "pr_id": state["pr_id"]})
        for role in ROLES
    ]


def fan_out_verify(state: ReviewState):
    by_path = {h["path"]: h for h in state["hunks"]}
    findings = state["findings"][:MAX_FINDINGS_TOTAL]
    return [
        Send("verify", {
            "finding": f,
            "context": by_path.get(
                f["path"], {}).get("patch", "")})
        for f in findings
    ]


def build_graph(checkpointer=None):
    g = StateGraph(ReviewState)
    g.add_node("gather", gather_node)
    g.add_node("review", review_node)
    g.add_node("verify", verify_node)
    g.add_node("consolidate", consolidate_node)
    g.add_node("gate", gate_node)

    g.add_edge(START, "gather")
    g.add_conditional_edges(
        "gather", fan_out_reviewers, ["review"])
    g.add_conditional_edges(
        "review", fan_out_verify, ["verify"])
    g.add_edge("verify", "consolidate")
    g.add_edge("consolidate", "gate")
    g.add_edge("gate", END)

    cp = checkpointer or InMemorySaver()
    return g.compile(checkpointer=cp)
