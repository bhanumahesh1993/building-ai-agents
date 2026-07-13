# research/app.py
from __future__ import annotations

import anyio
from fastapi import FastAPI
from pydantic import BaseModel
from langfuse import observe

from .orchestrator import run_research
from .synthesize import synthesize_issue
from .citations import verify_citations
from .memo import build_memo

app = FastAPI(title="Legal Research Deep-Dive")

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


class ResearchReq(BaseModel):
    facts: str
    jurisdiction: str


@app.post("/research")
@observe(name="legal_research_run")
async def research(req: ResearchReq):
    """One call: issues -> subagents -> synth -> cite."""
    state = await run_research(
        req.facts, req.jurisdiction)

    arguments = []
    for finding in state["findings"]:
        arg = await synthesize_issue(finding)
        arguments.append(arg)

    verified: dict[str, list[dict]] = {}
    for arg in arguments:
        cites = arg["for_cites"] + arg["against_cites"]
        verified[arg["issue_id"]] = (
            await verify_citations(cites))

    memo = build_memo(
        req.facts, req.jurisdiction,
        state["issues"], arguments, verified)
    return {"memo": memo}
