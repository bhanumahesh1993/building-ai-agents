# inventory_agent/mcp_server.py
from __future__ import annotations

import sqlite3

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("inventory-stock")
DB_PATH = "inventory.db"


def _conn():
    return sqlite3.connect(DB_PATH)


def _seed():
    with _conn() as c:
        c.execute(
            "CREATE TABLE IF NOT EXISTS stock ("
            "sku TEXT PRIMARY KEY, on_hand INT, "
            "reorder_at INT, unit_cost REAL)")
        c.execute(
            "INSERT OR IGNORE INTO stock VALUES "
            "('GASKET-9', 3, 10, 12.40)")


@mcp.tool()
def get_stock_level(sku: str) -> dict:
    """Look up on-hand qty and reorder line
    for one SKU."""
    with _conn() as c:
        row = c.execute(
            "SELECT on_hand, reorder_at, unit_cost "
            "FROM stock WHERE sku = ?", (sku,),
        ).fetchone()
    if row is None:
        return {"error": f"unknown sku {sku}"}
    on_hand, reorder_at, unit_cost = row
    return {
        "sku": sku, "on_hand": on_hand,
        "reorder_at": reorder_at,
        "unit_cost": unit_cost,
    }


@mcp.tool()
def list_low_stock() -> list[dict]:
    """List every SKU below its reorder line."""
    with _conn() as c:
        rows = c.execute(
            "SELECT sku, on_hand, reorder_at, "
            "unit_cost FROM stock "
            "WHERE on_hand < reorder_at").fetchall()
    return [
        {"sku": r[0], "on_hand": r[1],
         "reorder_at": r[2], "unit_cost": r[3]}
        for r in rows
    ]


if __name__ == "__main__":
    _seed()
    mcp.run()  # stdio transport
