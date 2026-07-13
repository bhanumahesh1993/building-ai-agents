# review/app.py
from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel
from langfuse.langchain import CallbackHandler

from .graph import build_graph

app = FastAPI(title="Code Review Panel API")
graph = build_graph()
handler = CallbackHandler()


class ReviewReq(BaseModel):
    pr_id: str
    diff: str


def _config(thread_id: str) -> dict:
    return {
        "configurable": {"thread_id": thread_id},
        "callbacks": [handler],
    }


@app.post("/review")
def review(req: ReviewReq):
    """Run the full panel on one PR diff."""
    state = graph.invoke(
        {"pr_id": req.pr_id, "diff": req.diff},
        config=_config(req.pr_id),
    )
    return {
        "decision": state["decision"],
        "report": state["report"],
    }
