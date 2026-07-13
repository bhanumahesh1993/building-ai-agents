# support/app.py
from __future__ import annotations

import uuid

from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.types import Command
from langfuse.langchain import CallbackHandler

from .graph import build_graph

app = FastAPI(title="Notewise Support Agent")
graph = build_graph()
handler = CallbackHandler()


class TicketReq(BaseModel):
    customer_id: str
    message: str


class ReviewReq(BaseModel):
    thread_id: str
    summary: dict


def _config(thread_id: str) -> dict:
    return {
        "configurable": {"thread_id": thread_id},
        "callbacks": [handler],
    }


@app.post("/ticket")
def submit(req: TicketReq):
    """Run a ticket; may pause for escalation review."""
    thread_id = str(uuid.uuid4())
    state = graph.invoke({
        "customer_id": req.customer_id,
        "message": req.message,
    }, config=_config(thread_id))
    if "__interrupt__" in state:
        pending = state["__interrupt__"][0].value
        return {
            "thread_id": thread_id,
            "status": "pending_review",
            "summary": pending["summary"],
        }
    return {
        "thread_id": thread_id,
        "status": state["resolution"],
        "answer": state.get("answer"),
        "citations": state.get("citations"),
    }


@app.post("/review")
def review(req: ReviewReq):
    """Resume after a support lead edits the summary."""
    state = graph.invoke(
        Command(resume={"summary": req.summary}),
        config=_config(req.thread_id))
    return {
        "status": state["resolution"],
        "ticket_id": state.get("ticket_id"),
    }
