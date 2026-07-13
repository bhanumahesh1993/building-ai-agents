# tests/test_gate.py — the payment-authorization gate must
# never regress. This project's design implements the stop as
# an ABSENCE of capability: no agent is ever wired with a
# spend/confirm tool, and catalog_server.confirm_order is never
# wrapped with @function_tool in shopping/tools.py. These tests
# assert that absence directly, rather than trusting a prompt.
from __future__ import annotations

import inspect

import shopping.tools as tools_module
from agents.tool import FunctionTool
from shopping.agents import all_agents
from shopping.app import confirm


def test_no_agent_has_a_confirm_or_spend_tool():
    """No agent anywhere in the chain may see confirm_order,
    or any tool whose name suggests it can move money."""
    banned = {"confirm_order", "charge", "pay", "checkout_charge"}
    for agent in all_agents():
        names = {t.name for t in agent.tools}
        assert not (names & banned), (
            f"{agent.name} is wired with a banned tool: "
            f"{names & banned}"
        )


def test_confirm_order_is_never_a_function_tool():
    """shopping/tools.py - the module every agent's tools are
    imported from - must never define a FunctionTool named
    confirm_order, and must not even import the name."""
    assert not hasattr(tools_module, "confirm_order"), (
        "shopping.tools must never expose confirm_order at all"
    )
    for name in dir(tools_module):
        obj = getattr(tools_module, name)
        if isinstance(obj, FunctionTool):
            assert obj.name != "confirm_order"


def test_catalog_server_confirm_order_exists_but_is_isolated():
    """The capability exists on the MCP server (the app's own
    client calls it after a human confirms) but is never
    imported into the agent-facing tools module."""
    import catalog_server

    assert callable(catalog_server.confirm_order)
    assert "confirm_order" not in dir(tools_module)


def test_confirm_route_is_a_plain_function_not_an_agent_tool():
    """POST /confirm in shopping/app.py is a plain FastAPI
    route - not a function_tool, not reachable by any agent.
    No agent object appears anywhere in its source."""
    assert not isinstance(confirm, FunctionTool)
    src = inspect.getsource(confirm)
    assert "Agent(" not in src
    assert "Runner.run" not in src


def test_gate_agent_tool_wiring_is_exactly_as_designed():
    """Pin the exact tool sets so a future edit can't quietly
    smuggle a spend tool onto an unexpected agent."""
    by_name = {a.name: {t.name for t in a.tools} for a in all_agents()}
    assert by_name["Concierge"] == set()
    assert by_name["Product Search"] == {
        "search_products", "get_product",
    }
    assert by_name["Comparator"] == {"get_product"}
    assert by_name["Cart & Checkout Gate"] == {
        "add_to_cart", "get_cart", "price_cart",
        "create_pending_order",
    }
