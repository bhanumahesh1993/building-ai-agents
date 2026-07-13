# tests/test_catalog_constraints.py — constraint-satisfaction
# (budget respected) checks against the catalog server's own
# logic. catalog_server functions are plain callables (FastMCP's
# @mcp.tool() does not wrap them opaquely), so they can be
# exercised directly with no subprocess and no live model -
# these are the same functions shopping/tools.py calls over MCP.
from __future__ import annotations

import uuid

import catalog_server as cs


def _sid() -> str:
    """A fresh session id per test - catalog_server's CARTS /
    PENDING / CONFIRMED dicts are module-level and shared."""
    return f"test-{uuid.uuid4().hex[:8]}"


def test_search_products_never_returns_a_result_over_max_price():
    # Empty query text matches every product (substring of
    # anything); max_price=100 should leave only the $89 buds.
    hits = cs.search_products("", max_price=100.0)
    assert "hp-300" in hits
    for line in hits.splitlines():
        if not line or line == "No matching products.":
            continue
        price = float(line.split("$")[1].split(" ")[0])
        assert price <= 100.0


def test_search_products_no_ceiling_returns_all_matches():
    hits = cs.search_products("", max_price=0.0)
    assert hits.count("hp-") == 3  # all three products match


def test_price_cart_total_equals_sum_of_line_items():
    sid = _sid()
    cs.add_to_cart(sid, "hp-100", qty=2)   # $129.00 x2
    cs.add_to_cart(sid, "hp-300", qty=1)   # $89.00 x1
    breakdown = cs.price_cart(sid)
    expected_total = 129.00 * 2 + 89.00
    assert f"Total: ${expected_total:.2f}" in breakdown


def test_pending_order_total_matches_priced_cart_not_agent_claim():
    """The order total is server-computed from PRODUCTS, never
    trusted from anything an agent might have said."""
    sid = _sid()
    cs.add_to_cart(sid, "hp-200", qty=1)
    staged = cs.create_pending_order(sid)
    order_id = staged.split()[2].rstrip(":")
    assert cs.PENDING[order_id]["total"] == 137.98
    assert "Awaiting human confirmation" in staged
    assert "nothing charged" in staged.lower()


def test_confirm_order_is_idempotent_and_does_not_double_charge():
    sid = _sid()
    cs.add_to_cart(sid, "hp-100", qty=1)
    staged = cs.create_pending_order(sid)
    order_id = staged.split()[2].rstrip(":")
    key = f"key-{sid}"

    first = cs.confirm_order(order_id, key)
    assert "Charged" in first
    assert order_id not in cs.PENDING  # moved out of pending

    second = cs.confirm_order(order_id, key)
    assert "idempotent replay" in second
    # only one receipt was ever recorded for this key
    assert cs._IDEMPOTENCY[key] == order_id
