# monitor/graph.py
from __future__ import annotations

import os
import uuid

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import InMemorySaver

from .registry import default_registry
from .state import MonitorState
from .nodes.fetch import fetch_node
from .nodes.diff import diff_node
from .nodes.score import score_node
from .nodes.digest import digest_node

MAX_TARGETS = int(os.getenv("MAX_TARGETS", "25"))


def fan_out_fetch(state: MonitorState):
    """Spawn one fetch worker per registry target,
    capped so a huge registry can't blow the budget."""
    registry = default_registry()
    targets = registry.targets[:MAX_TARGETS]
    return [
        Send("fetch", {
            "url": t.url,
            "competitor": t.competitor,
            "kind": t.kind.value,
            "content_selector": t.content_selector,
        })
        for t in targets
    ]


def fan_diff(state: MonitorState):
    """Every fetch result gets its own diff check."""
    # fetch_node's private results are gathered by
    # LangGraph's own per-node output; diff runs once
    # per worker via the same fan-out mechanism.
    return "diff"


def fan_score(state: MonitorState):
    """One score pass per confirmed change."""
    return [
        Send("score", {"_change": c})
        for c in state.get("changes", [])
    ]


def build_graph(checkpointer=None):
    g = StateGraph(MonitorState)
    g.add_node("fetch", fetch_node)
    g.add_node("diff", diff_node)
    g.add_node("score", score_node)
    g.add_node("digest", digest_node)

    g.add_edge(START, "fetch")
    g.add_conditional_edges(
        START, fan_out_fetch, ["fetch"])
    g.add_edge("fetch", "diff")
    g.add_conditional_edges(
        "diff", fan_score, ["score", "digest"])
    g.add_edge("score", "digest")
    g.add_edge("digest", END)

    cp = checkpointer or InMemorySaver()
    return g.compile(checkpointer=cp)
