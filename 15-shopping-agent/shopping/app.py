# shopping/app.py
from __future__ import annotations

import uuid

from agents import Runner
from fastapi import FastAPI
from pydantic import BaseModel

from .agents import concierge
from .tools import _call

app = FastAPI(title="Shopping Agent API")


class ShopReq(BaseModel):
    session_id: str | None = None
    message: str


class ConfirmReq(BaseModel):
    order_id: str
    idempotency_key: str | None = None


@app.post("/shop")
async def shop(req: ShopReq):
    """Run the agent chain up to the checkout gate."""
    sid = req.session_id or uuid.uuid4().hex[:12]
    prompt = f"[session_id={sid}] {req.message}"
    result = await Runner.run(concierge, prompt)
    return {
        "session_id": sid,
        "proposal": result.final_output,
    }


@app.post("/confirm")
async def confirm(req: ConfirmReq):
    """Human-confirmed charge. No agent calls this -
    it is a plain function call from here."""
    key = req.idempotency_key or req.order_id
    receipt = await _call("confirm_order", {
        "order_id": req.order_id,
        "idempotency_key": key,
    })
    return {"receipt": receipt}
