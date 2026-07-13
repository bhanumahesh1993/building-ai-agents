# review/nodes/verify.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..prompts import VERIFY_SYSTEM
from ..state import VerifierState

VERIFIER_MODEL = os.getenv(
    "VERIFIER_MODEL", "claude-opus-4-5")

_llm = ChatAnthropic(
    model=VERIFIER_MODEL, temperature=0)


def verify_node(state: VerifierState) -> dict:
    """Adversarially try to refute one finding."""
    finding = state["finding"]
    prompt = VERIFY_SYSTEM.format(
        finding=json.dumps(finding),
        context=state["context"] or "(no context)")
    resp = _llm.invoke(prompt)
    raw = json.loads(resp.content)
    verified = {
        "finding": finding,
        "verdict": raw["verdict"],
        "rationale": raw["rationale"],
    }
    return {"verified": [verified]}
