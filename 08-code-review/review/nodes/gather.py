# review/nodes/gather.py
from __future__ import annotations

from ..diff_utils import parse_diff
from ..state import ReviewState

MAX_HUNKS = 40
MAX_DIFF_CHARS = 60_000


def gather_node(state: ReviewState) -> dict:
    """Parse the diff and cap it for cost control."""
    raw = state["diff"]
    diff = raw[:MAX_DIFF_CHARS]
    hunks = parse_diff(diff)
    capped = hunks[:MAX_HUNKS]
    truncated = (
        len(raw) > MAX_DIFF_CHARS
        or len(hunks) > MAX_HUNKS)
    return {"hunks": capped, "truncated": truncated}
