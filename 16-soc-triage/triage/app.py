# triage/app.py
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.types import Command
from langfuse.langchain import CallbackHandler

from .graph import build_graph

app = FastAPI(title="SOC Alert-Triage API")
graph = build_graph()
handler = CallbackHandler()


class AlertReq(BaseModel):
    alert_id: str
    source: str = "siem"
    rule_name: str = ""
    severity: str = "medium"
    raw: str = ""


class ApproveReq(BaseModel):
    thread_id: str
    approved: bool


def _config(thread_id: str) -> dict:
    return {
        "configurable": {"thread_id": thread_id},
        "callbacks": [handler],
    }


@app.post("/alerts")
def ingest(req: AlertReq):
    """Run triage; may pause for containment approval."""
    thread_id = req.alert_id
    state = graph.invoke(
        {"raw_event": req.model_dump()},
        config=_config(thread_id),
    )
    if "__interrupt__" in state:
        gate = state["__interrupt__"][0].value
        return {"thread_id": thread_id,
                 "status": "awaiting_approval",
                 "gate": gate}
    return {"thread_id": thread_id,
             "status": state["resolution"],
             "result": state["action_result"]}


@app.post("/approve")
def approve(req: ApproveReq):
    """Resume after a human approves or declines."""
    state = graph.invoke(
        Command(resume={"approved": req.approved}),
        config=_config(req.thread_id),
    )
    return {"status": state["resolution"],
             "result": state["action_result"]}
