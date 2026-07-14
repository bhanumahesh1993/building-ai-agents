# panel/nodes/bias_check.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..prompts import BIAS_SYSTEM
from ..state import PanelState

BIAS_MODEL = os.getenv(
    "BIAS_MODEL", "claude-opus-4-5")

_llm: ChatAnthropic | None = None


def _get_llm() -> ChatAnthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _llm
    if _llm is None:
        _llm = ChatAnthropic(model=BIAS_MODEL, temperature=0)
    return _llm


def bias_check_node(state: PanelState) -> dict:
    """Independent read for anchoring and closure -- then,
    at most once, a forced recheck round."""
    transcript = "\n".join(
        f"round {a['round']} [{a['stance']} -> "
        f"{a['hypothesis']}] {a['text']}"
        for a in state["arguments"])
    leader = max(
        state["hypotheses"], key=lambda h: h["confidence"])
    prompt = BIAS_SYSTEM.format(
        transcript=transcript, leader=leader["name"],
        rounds=state["round"])
    resp = _get_llm().invoke(prompt)
    flags = json.loads(resp.content)["flags"]

    anchoring = [
        f for f in flags
        if f["kind"] == "anchoring"
        and f["target"] == leader["name"]]
    recheck = bool(anchoring) and state["bias_rechecks"] < 1

    hyps = state["hypotheses"]
    if recheck:
        hyps = [{**h, "status": "active"} for h in hyps]

    return {
        "bias_flags": state.get("bias_flags", []) + flags,
        "hypotheses": hyps,
        "bias_rechecks": (
            state["bias_rechecks"] + 1 if recheck
            else state["bias_rechecks"]),
        "force_recheck": recheck,
    }
