# agent/app.py
from __future__ import annotations

from fastapi import FastAPI
from langfuse.langchain import CallbackHandler
from pydantic import BaseModel

from .agent import run_issue

app = FastAPI(title="Autonomous Coding & PR Agent")
handler = CallbackHandler()


class IssueReq(BaseModel):
    repo_url: str
    base_ref: str = "main"
    title: str
    body: str


@app.post("/issues")
async def submit_issue(req: IssueReq):
    """Take an issue, return the PR that resulted."""
    result = await run_issue(
        req.repo_url, req.base_ref, req.title, req.body)
    return result
