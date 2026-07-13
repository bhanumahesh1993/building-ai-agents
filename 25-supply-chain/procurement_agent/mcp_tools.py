# procurement_agent/mcp_tools.py
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("procurement-tools")

CATALOG = {
    "GASKET-9": [
        {"supplier": "Anchor Fasteners Co.",
         "unit_price": 12.40, "lead_time_days": 9,
         "moq": 100},
        {"supplier": "BoltWorks Inc.",
         "unit_price": 11.95, "lead_time_days": 14,
         "moq": 250},
        {"supplier": "Fastenal Direct",
         "unit_price": 13.10, "lead_time_days": 5,
         "moq": 50},
    ],
}

_ORDERS: dict[str, dict] = {}


@mcp.tool()
def get_quotes(sku: str) -> list[dict]:
    """Return every vendor quote on file for a SKU."""
    return CATALOG.get(sku, [])


@mcp.tool()
def record_order(po_number: str, order: dict) -> dict:
    """Persist a finalized purchase order."""
    _ORDERS[po_number] = order
    return {"stored": po_number}


@mcp.tool()
def get_order(po_number: str) -> dict:
    """Look up a previously recorded PO."""
    return _ORDERS.get(
        po_number, {"error": "not found"})


if __name__ == "__main__":
    mcp.run()
