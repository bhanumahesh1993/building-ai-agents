# panel/nodes/intake.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..prompts import INTAKE_SYSTEM
from ..state import PanelState

INTAKE_MODEL = os.getenv(
    "INTAKE_MODEL", "claude-haiku-4-5")

_llm: ChatAnthropic | None = None


def _get_llm() -> ChatAnthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _llm
    if _llm is None:
        _llm = ChatAnthropic(model=INTAKE_MODEL, temperature=0)
    return _llm


def intake_node(state: PanelState) -> dict:
    """Turn prose into a list of atomic clinical facts."""
    prompt = INTAKE_SYSTEM.format(vignette=state["vignette"])
    resp = _get_llm().invoke(prompt)
    data = json.loads(resp.content)
    return {
        "findings": data["findings"],
        "revealed_results": {},
        "orders": [],
        "cost_total": 0.0,
        "round": 0,
        "bias_flags": [],
        "bias_rechecks": 0,
    }
