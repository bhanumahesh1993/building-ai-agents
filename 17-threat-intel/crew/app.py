# crew/app.py
from __future__ import annotations

import litellm
from fastapi import FastAPI
from pydantic import BaseModel

from .crew import run_weekly_brief
from .models import ThreatBrief

litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]

app = FastAPI(title="Threat-Intel Briefing Crew API")


class BriefRequest(BaseModel):
    days: int = 7
    week_of: str


@app.post("/weekly-brief", response_model=ThreatBrief)
def create_brief(req: BriefRequest):
    """Run the crew end to end and return the brief."""
    return run_weekly_brief(
        days=req.days, week_of=req.week_of)
