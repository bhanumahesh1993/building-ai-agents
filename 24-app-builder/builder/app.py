# builder/app.py
from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .agent import run_build, BuildResult
from .deploy import deploy, DeployRefused
from .spec import AppSpec

app = FastAPI(title="Full-Stack App Builder")
BUILDS: dict[str, BuildResult] = {}


class BuildReq(BaseModel):
    spec: AppSpec


class ApproveReq(BaseModel):
    approved: bool = True


@app.post("/builds")
async def start_build(req: BuildReq):
    """Run spec -> plan -> build -> verify, end to end."""
    build_id = str(uuid.uuid4())
    result = await run_build(req.spec)
    BUILDS[build_id] = result
    return {
        "build_id": build_id,
        "ready_for_deploy": result.ready,
        "criteria": result.verify.passed,
        "iterations": result.iterations,
    }


@app.post("/builds/{build_id}/approve")
def approve_build(build_id: str, req: ApproveReq):
    """Human gate: deploy only if passing AND approved."""
    result = BUILDS.get(build_id)
    if result is None:
        raise HTTPException(404, "unknown build")
    try:
        out = deploy(
            result.root, result.verify,
            req.approved, build_id)
    except DeployRefused as exc:
        raise HTTPException(409, str(exc))
    return {"url": out.url, "container": out.container_id}
