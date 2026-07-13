# monitor/app.py
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel
from langfuse.langchain import CallbackHandler

from .schedule import run_once, start_scheduler

handler = CallbackHandler()
_last_digest = {"text": "No run yet.", "run_id": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = start_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Competi-Watch API", lifespan=lifespan)


class RunReq(BaseModel):
    min_score: int = 3


@app.post("/run")
def trigger_run(req: RunReq):
    """Trigger a scan now, outside the schedule."""
    state = run_once(min_score=req.min_score)
    _last_digest["text"] = state.get(
        "digest", "No changes found.")
    _last_digest["run_id"] = state.get("run_id")
    return _last_digest


@app.get("/digest")
def latest_digest():
    """Return the most recent digest produced."""
    return _last_digest
