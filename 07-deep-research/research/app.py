# research/app.py
from __future__ import annotations

import uuid

from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.types import Command
from langfuse.langchain import CallbackHandler

from .graph import build_graph

app = FastAPI(title="Deep Research API")
graph = build_graph()
handler = CallbackHandler()


class StartReq(BaseModel):
    question: str
    max_loops: int = 2


class ResumeReq(BaseModel):
    thread_id: str
    approved: bool = True
    plan: list | None = None


def _config(thread_id: str) -> dict:
    return {
        "configurable": {"thread_id": thread_id},
        "callbacks": [handler],
    }


@app.post("/research")
def start(req: StartReq):
    """Kick off a run; pauses at plan approval."""
    thread_id = str(uuid.uuid4())
    state = graph.invoke(
        {"question": req.question,
         "max_loops": req.max_loops},
        config=_config(thread_id),
    )
    plan = state["__interrupt__"][0].value["plan"]
    return {"thread_id": thread_id, "plan": plan}


@app.post("/approve")
def approve(req: ResumeReq):
    """Resume after the human approves the plan."""
    payload: dict = {"approved": req.approved}
    if req.plan is not None:
        payload["plan"] = req.plan
    state = graph.invoke(
        Command(resume=payload),
        config=_config(req.thread_id),
    )
    return {"report": state["report"]}
