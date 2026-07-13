# voice/tools.py
from __future__ import annotations

ORDERS = {
    "A1042": {"status": "out for delivery",
              "eta": "today by 6pm"},
    "A1099": {"status": "processing",
              "eta": "ships within 24 hours"},
}

FAQS = [
    {"q": "return policy",
     "a": "Returns are free within 30 days of "
          "delivery, no questions asked."},
    {"q": "shipping cost",
     "a": "Standard shipping is free over $35; "
          "otherwise it is $4.99."},
    {"q": "change address",
     "a": "You can change a delivery address "
          "until the order ships, from Account "
          "Settings."},
]

TOOL_SCHEMAS = [
    {
        "name": "get_order_status",
        "description": (
            "Look up the status of an order "
            "by ID."),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "search_faq",
        "description": "Search support FAQs.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        },
    },
]


def get_order_status(order_id: str) -> dict:
    """Look up one order. Never invents a status."""
    order = ORDERS.get(order_id.upper())
    if order is None:
        return {"error": "no order with that ID"}
    return {"order_id": order_id, **order}


def search_faq(query: str) -> dict:
    """Keyword match over the FAQ table."""
    q = query.lower()
    hits = [f for f in FAQS if any(
        w in f["q"] for w in q.split())]
    if not hits:
        hits = FAQS[:1]
    return {"matches": hits[:2]}


def run_tool(name: str, args: dict) -> dict:
    """Dispatch a tool call by name."""
    if name == "get_order_status":
        return get_order_status(args["order_id"])
    if name == "search_faq":
        return search_faq(args["query"])
    return {"error": f"unknown tool {name}"}
