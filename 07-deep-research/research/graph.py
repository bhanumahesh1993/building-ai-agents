# research/graph.py
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langgraph.checkpoint.memory import InMemorySaver

from .state import ReportState
from .nodes.planner import plan_node
from .nodes.researcher import research_node
from .nodes.synthesizer import synthesize_node
from .nodes.citations import cite_node


def fan_out(state: ReportState):
    """Spawn one worker per plan task, in parallel."""
    return [
        Send("research",
             {"task": t,
              "question": state["question"]})
        for t in state["plan"]
    ]


def route_after_synth(state: ReportState):
    """Quality gate: loop on gaps, else cite."""
    covered = {f["topic"] for f in state["findings"]}
    gaps = [
        t for t in state["plan"]
        if t["topic"] not in covered
    ]
    if gaps and state["loops"] < state["max_loops"]:
        return [
            Send("research",
                 {"task": t,
                  "question": state["question"]})
            for t in gaps
        ]
    return "citations"


def build_graph(checkpointer=None):
    g = StateGraph(ReportState)
    g.add_node("plan", plan_node)
    g.add_node("research", research_node)
    g.add_node("synthesize", synthesize_node)
    g.add_node("citations", cite_node)

    g.add_edge(START, "plan")
    g.add_conditional_edges(
        "plan", fan_out, ["research"])
    g.add_edge("research", "synthesize")
    g.add_conditional_edges(
        "synthesize", route_after_synth,
        ["research", "citations"])
    g.add_edge("citations", END)

    cp = checkpointer or InMemorySaver()
    return g.compile(checkpointer=cp)
