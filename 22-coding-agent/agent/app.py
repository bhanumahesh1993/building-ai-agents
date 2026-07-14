# agent/app.py
from __future__ import annotations

from fastapi import FastAPI
from langfuse import observe
from pydantic import BaseModel

from .agent import run_issue

app = FastAPI(title="Autonomous Coding & PR Agent")

_langfuse = None


def _get_langfuse():
    """Lazily build the client so the module imports
    without Langfuse credentials present (tests, offline
    use)."""
    global _langfuse
    if _langfuse is None:
        from langfuse import get_client
        _langfuse = get_client()
    return _langfuse


class IssueReq(BaseModel):
    repo_url: str
    base_ref: str = "main"
    title: str
    body: str


@app.post("/issues")
@observe(name="coding_agent_run")
async def submit_issue(req: IssueReq):
    """Take an issue, return the PR that resulted."""
    result = await run_issue(
        req.repo_url, req.base_ref, req.title, req.body)
    return result
