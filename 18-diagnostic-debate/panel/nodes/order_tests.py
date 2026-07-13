# panel/nodes/order_tests.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..prompts import ORDER_SYSTEM
from ..state import PanelState

ORDER_MODEL = os.getenv(
    "ORDER_MODEL", "claude-sonnet-4-5")

_llm = ChatAnthropic(model=ORDER_MODEL, temperature=0)

TEST_COSTS = {
    "cbc": 15, "cmp": 20, "esr": 12, "crp": 18,
    "ana": 45, "rf": 35, "blood_culture": 60,
    "urinalysis": 10, "chest_xray": 45,
    "joint_xray": 55, "ct_chest": 450,
    "mri_joint": 900, "synovial_fluid_culture": 220,
    "lyme_serology": 55, "echocardiogram": 380,
}


def order_tests_node(state: PanelState) -> dict:
    """Propose discriminating tests and price them."""
    menu = ", ".join(TEST_COSTS)
    hyps = "\n".join(
        f"- {h['name']}: {h['rationale']}"
        for h in state["hypotheses"]
        if h["status"] == "active")
    prompt = ORDER_SYSTEM.format(
        menu=menu, hypotheses=hyps)
    resp = _llm.invoke(prompt)
    data = json.loads(resp.content)

    orders = list(state.get("orders", []))
    revealed = dict(state.get("revealed_results", {}))
    spent = state.get("cost_total", 0.0)
    for o in data["orders"]:
        test = o["test"]
        if test not in TEST_COSTS or test in revealed:
            continue
        cost = TEST_COSTS[test]
        orders.append({
            "test": test, "rationale": o["rationale"],
            "cost_usd": cost})
        spent += cost
        revealed[test] = state["available_results"].get(
            test, "not available for this case")

    return {
        "orders": orders,
        "revealed_results": revealed,
        "cost_total": spent,
    }
