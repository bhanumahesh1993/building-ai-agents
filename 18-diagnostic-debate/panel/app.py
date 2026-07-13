# panel/app.py
from __future__ import annotations

import uuid

from fastapi import FastAPI
from pydantic import BaseModel
from langgraph.types import Command
from langfuse.langchain import CallbackHandler

from .graph import build_graph

app = FastAPI(title="Clinical Diagnostic Debate Panel")
graph = build_graph()
handler = CallbackHandler()


class CaseReq(BaseModel):
    vignette: str
    available_results: dict[str, str]
    max_rounds: int = 3
    cost_cap: float = 500.0


class ReviewReq(BaseModel):
    thread_id: str
    reviewed: bool
    clinician_notes: str = ""


def _config(thread_id: str) -> dict:
    return {
        "configurable": {"thread_id": thread_id},
        "callbacks": [handler],
    }


@app.post("/diagnose")
def diagnose(req: CaseReq):
    """Run the panel; always pauses for clinician review."""
    thread_id = str(uuid.uuid4())
    state = graph.invoke({
        "vignette": req.vignette,
        "available_results": req.available_results,
        "max_rounds": req.max_rounds,
        "cost_cap": req.cost_cap,
    }, config=_config(thread_id))
    payload = state["__interrupt__"][0].value
    return {"thread_id": thread_id, **payload}


@app.post("/review")
def review(req: ReviewReq):
    """Resume only after a human reviews the research output."""
    state = graph.invoke(
        Command(resume={
            "reviewed": req.reviewed,
            "notes": req.clinician_notes}),
        config=_config(req.thread_id))
    return {
        "final_differential": state["final_differential"],
        "approved": state["approved"],
        "notice": "RESEARCH OUTPUT ONLY -- see the "
                   "guardrails section before using this.",
    }
