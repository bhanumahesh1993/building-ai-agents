# tests/test_tools.py
from __future__ import annotations

from voice.tools import get_order_status, run_tool, search_faq


def test_get_order_status_known_order():
    result = get_order_status("a1042")
    assert result["status"] == "out for delivery"


def test_get_order_status_unknown_order_never_invents():
    result = get_order_status("Z9999")
    assert result == {"error": "no order with that ID"}


def test_search_faq_matches_keyword():
    result = search_faq("what is the return policy")
    assert any(
        "30 days" in m["a"] for m in result["matches"])


def test_search_faq_falls_back_to_first_entry():
    result = search_faq("xyzzy nonsense query")
    assert len(result["matches"]) == 1


def test_run_tool_dispatches_by_name():
    assert run_tool(
        "get_order_status", {"order_id": "A1099"}
    )["status"] == "processing"
    assert "matches" in run_tool(
        "search_faq", {"query": "shipping cost"})


def test_run_tool_unknown_name_errors():
    assert run_tool("nope", {}) == {"error": "unknown tool nope"}
