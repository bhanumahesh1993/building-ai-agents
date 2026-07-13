# firm/app.py
from __future__ import annotations

import uuid

from fastapi import FastAPI
from langfuse.langchain import CallbackHandler
from langgraph.types import Command
from pydantic import BaseModel

from .graph import build_graph

app = FastAPI(title="Trading Research Firm (paper only)")
graph = build_graph()
handler = CallbackHandler()


class DecideReq(BaseModel):
    symbol: str
    as_of: str
    max_debate_rounds: int = 2


class ConfirmReq(BaseModel):
    thread_id: str
    confirmed: bool = True


def _config(thread_id: str) -> dict:
    return {
        "configurable": {"thread_id": thread_id},
        "callbacks": [handler],
    }


@app.post("/decide")
def decide(req: DecideReq):
    """Run one research cycle. NEVER places a real order —
    the result is a simulated paper decision."""
    thread_id = str(uuid.uuid4())
    state = graph.invoke(
        {
            "symbol": req.symbol, "as_of": req.as_of,
            "debate_round": 0,
            "max_debate_rounds": req.max_debate_rounds,
            "risk_revisions": 0, "max_risk_revisions": 1,
        },
        config=_config(thread_id),
    )
    if "__interrupt__" in state:
        pending = state["__interrupt__"][0].value
        return {
            "thread_id": thread_id,
            "status": "awaiting_confirmation",
            "pending": pending,
        }
    return {
        "thread_id": thread_id, "status": "done",
        "paper_fill": state["paper_fill"],
    }


@app.post("/confirm")
def confirm(req: ConfirmReq):
    """Resume after a human confirms/declines a large paper
    trade. Still never touches a brokerage — it only decides
    whether the simulated blotter records the fill."""
    state = graph.invoke(
        Command(resume={"confirmed": req.confirmed}),
        config=_config(req.thread_id),
    )
    return {"status": "done", "paper_fill": state["paper_fill"]}
