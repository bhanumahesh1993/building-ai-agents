# shopping/tools.py
from __future__ import annotations

from agents import function_tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# catalog_server.py lives at the repo root (not inside the
# shopping/ package) - see catalog_server.py's own module
# docstring. Path is relative to the process's cwd, which is
# the project root for both `uvicorn shopping.app:app` and the
# Docker CMD below.
_PARAMS = StdioServerParameters(
    command="python",
    args=["catalog_server.py"],
)

# Every MCP call an agent makes is logged here, so
# tests and evals can assert on it without touching
# SDK internals - see the gate test below.
CALLED_TOOLS: list[str] = []


async def _call(name: str, args: dict) -> str:
    """Open a session, call one MCP tool, tear down."""
    CALLED_TOOLS.append(name)
    async with stdio_client(_PARAMS) as (read, write):
        async with ClientSession(read, write) as sess:
            await sess.initialize()
            out = await sess.call_tool(name, args)
            return out.content[0].text


@function_tool
async def search_products(
    query: str, max_price: float = 0.0,
) -> str:
    """Search the catalog by keyword and price ceiling."""
    return await _call(
        "search_products",
        {"query": query, "max_price": max_price})


@function_tool
async def get_product(product_id: str) -> str:
    """Return full details for one product by its id."""
    return await _call(
        "get_product", {"product_id": product_id})


@function_tool
async def add_to_cart(
    session_id: str, product_id: str, qty: int = 1,
) -> str:
    """Add a product to the shopper's cart."""
    return await _call("add_to_cart", {
        "session_id": session_id,
        "product_id": product_id, "qty": qty,
    })


@function_tool
async def get_cart(session_id: str) -> str:
    """Return the current cart contents."""
    return await _call(
        "get_cart", {"session_id": session_id})


@function_tool
async def price_cart(session_id: str) -> str:
    """Return a server-computed, itemized cart total."""
    return await _call(
        "price_cart", {"session_id": session_id})


@function_tool
async def create_pending_order(session_id: str) -> str:
    """Stage a pending order. Does NOT charge anything."""
    return await _call(
        "create_pending_order",
        {"session_id": session_id})
