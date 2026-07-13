# grading/app.py
from __future__ import annotations

import uuid

from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.types import Command
from langfuse.langchain import CallbackHandler

from .graph import build_graph

app = FastAPI(title="Grading Assistant API")
graph = build_graph()
handler = CallbackHandler()


class StartReq(BaseModel):
    prompt: str
    submissions: list[dict]
    max_loops: int = 1


class ReviewReq(BaseModel):
    thread_id: str
    approve: list[str] = []
    return_for_rescore: list[str] = []
    edits: dict = {}


def _config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id},
            "callbacks": [handler]}


@app.post("/grade")
def start(req: StartReq):
    """Score, draft feedback, screen — then pause."""
    thread_id = str(uuid.uuid4())
    state = graph.invoke(
        {"prompt": req.prompt,
         "submissions": req.submissions,
         "max_loops": req.max_loops, "loops": 0},
        config=_config(thread_id))
    queue = state["__interrupt__"][0].value["queue"]
    return {"thread_id": thread_id, "queue": queue}


@app.post("/review")
def review(req: ReviewReq):
    """Resume with the teacher's decisions."""
    payload = {"approve": req.approve,
               "return_for_rescore":
                   req.return_for_rescore,
               "edits": req.edits}
    state = graph.invoke(
        Command(resume=payload),
        config=_config(req.thread_id))
    if "__interrupt__" in state:
        q = state["__interrupt__"][0].value["queue"]
        return {"thread_id": req.thread_id, "queue": q}
    return {"released": state["released"],
            "class_summary": state["class_summary"]}
