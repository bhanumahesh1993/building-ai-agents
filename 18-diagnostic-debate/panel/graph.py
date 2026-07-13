# panel/graph.py
from __future__ import annotations

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send, interrupt
from langgraph.checkpoint.memory import InMemorySaver

from .state import PanelState
from .nodes.intake import intake_node
from .nodes.analyze import analyze_node
from .nodes.order_tests import order_tests_node
from .nodes.debate import advocate_node, moderate_node
from .nodes.bias_check import bias_check_node
from .nodes.steward import steward_node


def fan_out_advocates(state: PanelState):
    """Spawn one advocate per active hypothesis."""
    active = [
        h for h in state["hypotheses"]
        if h["status"] == "active"]
    return [
        Send("advocate", {
            "hypothesis": h,
            "rivals": [r for r in active
                       if r["name"] != h["name"]],
            "findings": state["findings"],
            "revealed_results": state["revealed_results"],
            "round": state["round"],
        })
        for h in active
    ]


def route_after_moderate(state: PanelState):
    """Loop for another round, or move to bias check."""
    active = [
        h for h in state["hypotheses"]
        if h["status"] == "active"]
    confs = sorted(
        (h["confidence"] for h in active), reverse=True)
    gap = confs[0] - confs[1] if len(confs) > 1 else 1.0
    resolved = len(active) <= 1 or gap >= 0.3
    if resolved or state["round"] >= state["max_rounds"]:
        return "bias_check"
    return fan_out_advocates(state)


def route_after_bias(state: PanelState):
    """Take the one bounded recheck round, or proceed."""
    if state.get("force_recheck"):
        return fan_out_advocates(state)
    return "steward"


def clinician_review_node(state: PanelState) -> dict:
    """The only step that can ever close out a run."""
    decision = interrupt({
        "final_differential": state["final_differential"],
        "bias_flags": state["bias_flags"],
        "cost_total": state["cost_total"],
        "cost_note": state["cost_note"],
        "notice": (
            "RESEARCH OUTPUT ONLY -- not a diagnosis, "
            "not a treatment plan, never for a real "
            "patient."),
    })
    return {"approved": bool(decision.get("reviewed"))}


def build_graph(checkpointer=None):
    g = StateGraph(PanelState)
    g.add_node("intake", intake_node)
    g.add_node("analyze", analyze_node)
    g.add_node("order_tests", order_tests_node)
    g.add_node("advocate", advocate_node)
    g.add_node("moderate", moderate_node)
    g.add_node("bias_check", bias_check_node)
    g.add_node("steward", steward_node)
    g.add_node("clinician_review", clinician_review_node)

    g.add_edge(START, "intake")
    g.add_edge("intake", "analyze")
    g.add_edge("analyze", "order_tests")
    g.add_conditional_edges(
        "order_tests", fan_out_advocates, ["advocate"])
    g.add_edge("advocate", "moderate")
    g.add_conditional_edges(
        "moderate", route_after_moderate,
        ["advocate", "bias_check"])
    g.add_conditional_edges(
        "bias_check", route_after_bias,
        ["advocate", "steward"])
    g.add_edge("steward", "clinician_review")
    g.add_edge("clinician_review", END)

    cp = checkpointer or InMemorySaver()
    return g.compile(checkpointer=cp)
