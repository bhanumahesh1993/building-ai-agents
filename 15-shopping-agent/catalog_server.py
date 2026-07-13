# catalog_server.py — FastMCP server for the shop's
# catalog, cart, and orders.
# Run: pip install "mcp[cli]", then
#      python catalog_server.py
from __future__ import annotations

import time
import uuid

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("shop-catalog")

# In-memory catalog. Swap for a real product database —
# the MCP surface would not change.
PRODUCTS = {
    "hp-100": {
        "title": "Aria ANC Headphones", "brand": "Aria",
        "price": 129.00, "category": "audio",
        "rating": 4.5,
        "desc": "Over-ear, 30h battery, active ANC.",
    },
    "hp-200": {
        "title": "NoiseOut Pro", "brand": "Kestrel",
        "price": 137.98, "category": "audio",
        "rating": 4.3,
        "desc": "Over-ear, 40h battery, adaptive ANC, "
                "app EQ.",
    },
    "hp-300": {
        "title": "Buds Air 3", "brand": "Aria",
        "price": 89.00, "category": "audio",
        "rating": 4.0,
        "desc": "In-ear, 6h battery, basic ANC.",
    },
}

CARTS: dict[str, list[dict]] = {}
PENDING: dict[str, dict] = {}
CONFIRMED: dict[str, dict] = {}
_IDEMPOTENCY: dict[str, str] = {}  # key -> order_id


@mcp.tool()
def search_products(query: str, max_price: float = 0.0) -> str:
    """Search the catalog by keyword and price ceiling.

    Use when the shopper describes what they want rather
    than naming an exact product id.

    Args:
        query: words to match in title, brand, or desc.
        max_price: 0 means no ceiling.
    """
    q = query.lower()
    hits = []
    for pid, p in PRODUCTS.items():
        text = f'{p["title"]} {p["brand"]} {p["desc"]}'
        if q not in text.lower():
            continue
        if max_price and p["price"] > max_price:
            continue
        hits.append(
            f'{pid}: {p["title"]} - ${p["price"]:.2f} '
            f'({p["rating"]} stars)')
    return "\n".join(hits) or "No matching products."


@mcp.tool()
def get_product(product_id: str) -> str:
    """Return full details for one product by its id."""
    p = PRODUCTS.get(product_id)
    if p is None:
        return f"No product with id {product_id!r}."
    return (
        f'{product_id} - {p["title"]} ({p["brand"]})\n'
        f'Price: ${p["price"]:.2f}  '
        f'Rating: {p["rating"]} stars\n{p["desc"]}'
    )


@mcp.tool()
def add_to_cart(
    session_id: str, product_id: str, qty: int = 1,
) -> str:
    """Add a product to the shopper's cart."""
    if product_id not in PRODUCTS:
        return f"No product with id {product_id!r}."
    cart = CARTS.setdefault(session_id, [])
    cart.append({"product_id": product_id, "qty": qty})
    return f"Added {qty}x {product_id} to cart."


@mcp.tool()
def get_cart(session_id: str) -> str:
    """Return the current cart contents, as text."""
    cart = CARTS.get(session_id, [])
    if not cart:
        return "Cart is empty."
    return "\n".join(
        f'{i["qty"]}x {i["product_id"]}' for i in cart)


@mcp.tool()
def price_cart(session_id: str) -> str:
    """Return a server-computed, itemized cart total.

    Always call this before staging an order - never
    trust a total you computed yourself.
    """
    cart = CARTS.get(session_id, [])
    lines, total = [], 0.0
    for item in cart:
        p = PRODUCTS[item["product_id"]]
        line = p["price"] * item["qty"]
        total += line
        lines.append(
            f'{item["qty"]}x {p["title"]}: ${line:.2f}')
    lines.append(f"Total: ${total:.2f}")
    return "\n".join(lines)


@mcp.tool()
def create_pending_order(session_id: str) -> str:
    """Stage a pending order. Never charges anything.

    Returns an order id and itemized total. Payment
    requires a separate, human-confirmed call this
    tool does not perform.
    """
    cart = CARTS.get(session_id)
    if not cart:
        return "Cart is empty; nothing to stage."
    total = sum(
        PRODUCTS[i["product_id"]]["price"] * i["qty"]
        for i in cart)
    order_id = f"ord_{uuid.uuid4().hex[:10]}"
    PENDING[order_id] = {
        "session_id": session_id, "items": list(cart),
        "total": round(total, 2),
        "staged_at": time.time(),
    }
    return (
        f"Pending order {order_id}: ${total:.2f} across "
        f"{len(cart)} line(s). Awaiting human "
        "confirmation - nothing charged.")


@mcp.tool()
def confirm_order(order_id: str, idempotency_key: str) -> str:
    """Charge a pending order. HUMAN-ONLY capability.

    Never list this tool on an Agent. It exists so the
    app's own MCP client can charge after a human
    confirms - the model must never reach it.

    Args:
        order_id: id from create_pending_order.
        idempotency_key: caller-supplied dedupe key; a
            repeat call with the same key returns the
            original receipt and charges nothing twice.
    """
    if idempotency_key in _IDEMPOTENCY:
        oid = _IDEMPOTENCY[idempotency_key]
        r = CONFIRMED[oid]
        return (f"Already confirmed: {oid} - "
                f'${r["total"]:.2f} (idempotent replay).')
    order = PENDING.get(order_id)
    if order is None:
        return f"No pending order {order_id!r}."
    receipt = {**order, "confirmed_at": time.time()}
    CONFIRMED[order_id] = receipt
    _IDEMPOTENCY[idempotency_key] = order_id
    del PENDING[order_id]
    return (f"Charged {order_id}: ${order['total']:.2f}. "
            "Receipt recorded.")


@mcp.resource("shop://categories")
def list_categories() -> str:
    """Product categories, for the app to preload."""
    cats = sorted(
        {p["category"] for p in PRODUCTS.values()})
    return "\n".join(cats)


if __name__ == "__main__":
    mcp.run()  # stdio transport by default
