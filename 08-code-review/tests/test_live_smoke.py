# tests/test_live_smoke.py
from __future__ import annotations

import os

import pytest

from review.graph import build_graph

_LIVE_DIFF = (
    "--- a/x.py\n+++ b/x.py\n@@ -1,1 +1,1 @@\n-old\n+new\n"
)


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires a live ANTHROPIC_API_KEY; skipped by default",
)
def test_live_review_smoke():
    """Optional sanity check against the real API. Skipped unless
    ANTHROPIC_API_KEY is set -- never runs in the offline test suite."""
    graph = build_graph()
    state = graph.invoke(
        {"pr_id": "live-smoke-1", "diff": _LIVE_DIFF},
        config={"configurable": {"thread_id": "live-smoke-1"}},
    )
    assert "decision" in state
    assert "report" in state
