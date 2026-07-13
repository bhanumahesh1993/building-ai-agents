# crew/app.py
from __future__ import annotations

import os

import litellm
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .crew import generate_plan, run_drift_check
from .tools import _run_terraform
from .models import IacPlan

litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]

app = FastAPI(title="IaC Generation & Drift API")

_LAST_HCL: dict[str, str] = {}


class GenerateReq(BaseModel):
    brief: str
    workdir: str = "./workspace"


class DriftReq(BaseModel):
    live_state_path: str = (
        "data/live_state_snapshot.json")


@app.post("/generate", response_model=IacPlan)
def generate(req: GenerateReq):
    """Run the crew end to end and return the plan.
    Writes main.tf to workdir for /plan to use -
    never calls plan or apply itself."""
    plan = generate_plan(req.brief)
    os.makedirs(req.workdir, exist_ok=True)
    path = os.path.join(req.workdir, plan.hcl.filename)
    with open(path, "w") as fh:
        fh.write(plan.hcl.hcl)
    _LAST_HCL[req.workdir] = plan.hcl.hcl
    return plan


@app.post("/plan")
def preview(req: GenerateReq):
    """Run Terraform's own read-only plan against the
    generated file. Requires your own cloud
    credentials in the environment - this endpoint
    never supplies or stores any."""
    if req.workdir not in _LAST_HCL:
        raise HTTPException(
            400, "No generated plan in this workdir "
            "yet - call /generate first.")
    out = _run_terraform(
        ["init", "-input=false"], req.workdir)
    out += _run_terraform(
        ["plan", "-no-color", "-input=false"],
        req.workdir)
    destructive = ("1 to destroy" in out
                   or "forces replacement" in out)
    return {
        "plan_output": out,
        "destructive": destructive,
        "note": (
            "This is a read-only preview. Nothing "
            "was changed. Run terraform apply "
            "yourself, in your own terminal, only "
            "after you have read this."),
    }


@app.post("/drift-check")
def drift_check(req: DriftReq):
    """Compare a previously generated plan against a
    live-state snapshot. Never modifies anything on
    either side of the comparison."""
    workdir = "./workspace"
    if workdir not in _LAST_HCL:
        raise HTTPException(
            400, "No generated plan to check yet.")
    return run_drift_check(
        _LAST_HCL[workdir], req.live_state_path)
