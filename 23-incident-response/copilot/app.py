# copilot/app.py
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.types import Command
from langfuse.langchain import CallbackHandler

from .graph import build_graph

app = FastAPI(title="Incident-Response Copilot API")
graph = build_graph()
handler = CallbackHandler()


class AlertReq(BaseModel):
    alert_id: str
    service: str
    signal: str = "error_rate_spike"
    severity: str = "high"
    raw: str = ""
    started_at: str = ""


class ApproveReq(BaseModel):
    thread_id: str
    approved: bool
    deploy_id: str | None = None
    replicas: int | None = None


def _config(thread_id: str) -> dict:
    return {
        "configurable": {"thread_id": thread_id},
        "callbacks": [handler],
    }


@app.post("/incidents")
def ingest(req: AlertReq):
    """Diagnose an alert; may pause for a gate."""
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
    payload: dict = {"approved": req.approved}
    if req.deploy_id is not None:
        payload["deploy_id"] = req.deploy_id
    if req.replicas is not None:
        payload["replicas"] = req.replicas
    state = graph.invoke(
        Command(resume=payload),
        config=_config(req.thread_id),
    )
    return {"status": state["resolution"],
             "result": state["action_result"]}
