# review/nodes/reviewers.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from ..diff_utils import render_hunks
from ..prompts import (
    CORRECTNESS_SYSTEM, SECURITY_SYSTEM,
    TESTS_SYSTEM, STYLE_SYSTEM,
)
from ..state import ReviewerState

REVIEWER_MODEL = os.getenv(
    "REVIEWER_MODEL", "claude-sonnet-4-5")
MAX_FINDINGS_PER_REVIEWER = 8

ROLES = ["correctness", "security", "tests", "style"]

PROMPTS = {
    "correctness": CORRECTNESS_SYSTEM,
    "security": SECURITY_SYSTEM,
    "tests": TESTS_SYSTEM,
    "style": STYLE_SYSTEM,
}

_llm = ChatAnthropic(
    model=REVIEWER_MODEL, temperature=0)


def review_node(state: ReviewerState) -> dict:
    """One specialist: read the diff, report findings."""
    role = state["role"]
    prompt = PROMPTS[role].format(
        diff=render_hunks(state["hunks"]))
    resp = _llm.invoke(prompt)
    raw = json.loads(resp.content)
    items = raw.get("findings", [])
    findings = []
    for item in items[:MAX_FINDINGS_PER_REVIEWER]:
        findings.append({
            "reviewer": role,
            "path": item["path"],
            "line": item["line"],
            "severity": item["severity"],
            "claim": item["claim"],
            "evidence": item["evidence"],
        })
    return {"findings": findings}
