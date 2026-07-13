# run.py
from __future__ import annotations

import threading
import time

import uvicorn

from a2a_client import (
    can_fulfill, confirm, delegate, discover,
)
from shared.schemas import ReorderRequest

PROCUREMENT_URL = "http://localhost:8001"


def _serve(module: str, port: int):
    app = __import__(module, fromlist=["app"]).app
    uvicorn.run(app, host="0.0.0.0", port=port,
                log_level="warning")


def run_demo():
    time.sleep(1.5)  # let both servers finish booting
    card = discover(PROCUREMENT_URL)
    if not can_fulfill(card, "fulfill_reorder"):
        raise SystemExit("ProcureIQ can't fulfill.")

    req = ReorderRequest(
        sku="GASKET-9", quantity=500,
        spend_cap=5000.0, buyer_org="northwind")
    task = delegate(card, req)
    print(f"Task {task['id']}: {task['status']}")

    if task["status"]["state"] == "input-required":
        print(task["status"]["message"])
        answer = input("Approve? [y/N] ")
        task = confirm(
            card["url"], task["id"],
            answer.strip().lower() == "y")

    po = task["artifacts"][0]["parts"][0]["data"]
    print(f"PO {po['po_number']}: {po['supplier']} "
          f"— ${po['total']:.2f}")


if __name__ == "__main__":
    threading.Thread(
        target=_serve,
        args=("inventory_agent.agent", 8000),
        daemon=True).start()
    threading.Thread(
        target=_serve,
        args=("procurement_agent.agent", 8001),
        daemon=True).start()
    run_demo()
