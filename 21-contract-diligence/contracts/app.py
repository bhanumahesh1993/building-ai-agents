# contracts/app.py
from __future__ import annotations

import uuid

from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.types import Command
from langfuse.langchain import CallbackHandler

from .graph import build_graph

app = FastAPI(title="Contract Due-Diligence API")
graph = build_graph()
handler = CallbackHandler()


class StartReq(BaseModel):
    doc_folder: str
    jurisdiction: str = "Delaware"


class ApproveReq(BaseModel):
    thread_id: str
    approved: bool = True


def _config(thread_id: str) -> dict:
    return {
        "configurable": {"thread_id": thread_id},
        "callbacks": [handler],
    }


@app.post("/matters")
def start(req: StartReq):
    """Run the whole pipeline up to attorney sign-off."""
    thread_id = str(uuid.uuid4())
    state = graph.invoke(
        {"doc_folder": req.doc_folder,
         "jurisdiction": req.jurisdiction,
         "matter_id": thread_id[:8]},
        config=_config(thread_id))
    pending = state["__interrupt__"][0].value
    return {"thread_id": thread_id, **pending}


@app.post("/matters/approve")
def approve(req: ApproveReq):
    """Resume the run after attorney sign-off."""
    state = graph.invoke(
        Command(resume={"approved": req.approved}),
        config=_config(req.thread_id))
    return {
        "memo": state["memo"],
        "reviewed": state["reviewed"],
    }
