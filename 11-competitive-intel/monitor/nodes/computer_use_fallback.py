# monitor/nodes/computer_use_fallback.py (sketch)
from __future__ import annotations

import anthropic

CU_MODEL = "claude-opus-4-5"


def fetch_via_computer_use(
        url: str, login_steps: list[str]) -> str:
    """Sketch only: drive a real browser through a
    login flow via Claude's computer-use tool, then
    hand the rendered page back to the same
    selectolax-based text extraction fetch_tool.py
    already has. Each step below is one model call
    that sees a screenshot and returns one action
    (click, type, screenshot) via the computer-use
    tool definition -- see the vendor docs for the
    exact tool schema and action loop.
    """
    raise NotImplementedError(
        "Wire this to your computer-use runtime; "
        "see Exercise 1 for the guided build-out.")
