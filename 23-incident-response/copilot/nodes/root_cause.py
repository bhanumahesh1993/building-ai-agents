# copilot/nodes/root_cause.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..prompts import ROOT_CAUSE_SYSTEM
from ..state import IncidentState

ROOT_CAUSE_MODEL = os.getenv(
    "ROOT_CAUSE_MODEL", "claude-opus-4-5")

_llm: ChatAnthropic | None = None


def _get_llm() -> ChatAnthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _llm
    if _llm is None:
        _llm = ChatAnthropic(
            model=ROOT_CAUSE_MODEL, temperature=0)
    return _llm


def root_cause_node(state: IncidentState) -> dict:
    """Reason over the case; no tools, only an
    opinion. remediate owns the only hands here."""
    findings = "\n\n".join(
        f"[{i['kind']}] {i['summary']}"
        for i in state["investigations"])
    prompt = ROOT_CAUSE_SYSTEM.format(
        signal=state["alert"]["signal"],
        alert=state["alert"]["raw"],
        findings=findings,
    )
    resp = _get_llm().invoke(prompt)
    rc = json.loads(resp.content)
    return {
        "root_cause": rc,
        "audit": [{"node": "root_cause",
                    "category": rc["category"]}],
    }
