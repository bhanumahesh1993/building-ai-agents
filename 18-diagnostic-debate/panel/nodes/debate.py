# panel/nodes/debate.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..prompts import ADVOCATE_SYSTEM, MODERATE_SYSTEM
from ..state import AdvocateState, PanelState

ADVOCATE_MODEL = os.getenv(
    "ADVOCATE_MODEL", "claude-sonnet-4-5")
MODERATE_MODEL = os.getenv(
    "MODERATE_MODEL", "claude-opus-4-5")

_advocate_llm: ChatAnthropic | None = None
_moderate_llm: ChatAnthropic | None = None


def _get_advocate_llm() -> ChatAnthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _advocate_llm
    if _advocate_llm is None:
        _advocate_llm = ChatAnthropic(
            model=ADVOCATE_MODEL, temperature=0.3)
    return _advocate_llm


def _get_moderate_llm() -> ChatAnthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _moderate_llm
    if _moderate_llm is None:
        _moderate_llm = ChatAnthropic(
            model=MODERATE_MODEL, temperature=0)
    return _moderate_llm


def advocate_node(state: AdvocateState) -> dict:
    """One specialist argues for its hypothesis."""
    h = state["hypothesis"]
    rivals = ", ".join(r["name"] for r in state["rivals"])
    findings = "\n".join(
        f"- {f}" for f in state["findings"])
    results = "\n".join(
        f"- {k}: {v}" for k, v in
        state["revealed_results"].items()) or "none yet"
    prompt = ADVOCATE_SYSTEM.format(
        hypothesis=h["name"], rationale=h["rationale"],
        rivals=rivals, findings=findings, results=results)
    resp = _get_advocate_llm().invoke(prompt)
    data = json.loads(resp.content)
    r = state["round"]
    return {"arguments": [
        {"hypothesis": h["name"], "stance": "support",
         "text": data["support"], "round": r},
        {"hypothesis": data["challenge_target"],
         "stance": "challenge",
         "text": data["challenge"], "round": r},
    ]}


def moderate_node(state: PanelState) -> dict:
    """Weigh this round's arguments; narrow the field."""
    this_round = [
        a for a in state["arguments"]
        if a["round"] == state["round"]]
    args_text = "\n".join(
        f"[{a['stance']} -> {a['hypothesis']}] {a['text']}"
        for a in this_round)
    hyps_text = "\n".join(
        f"- {h['name']} (conf {h['confidence']:.2f})"
        for h in state["hypotheses"]
        if h["status"] == "active")
    prompt = MODERATE_SYSTEM.format(
        hypotheses=hyps_text, arguments=args_text)
    resp = _get_moderate_llm().invoke(prompt)
    data = json.loads(resp.content)
    updated = {h["name"]: h for h in data["hypotheses"]}

    new_hyps = []
    for h in state["hypotheses"]:
        u = updated.get(h["name"])
        if u is None:
            new_hyps.append(h)
            continue
        new_hyps.append({
            "name": h["name"], "rationale": h["rationale"],
            "confidence": u["confidence"],
            "status": u["status"]})

    return {
        "hypotheses": new_hyps,
        "round": state["round"] + 1,
    }
