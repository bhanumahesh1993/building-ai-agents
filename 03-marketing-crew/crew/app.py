# crew/app.py
from __future__ import annotations

import os

import litellm
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .crew import run_campaign
from .models import CampaignKit

litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]

app = FastAPI(title="Marketing Campaign Crew API")


class BriefRequest(BaseModel):
    product_name: str
    one_liner: str
    audience: str
    key_facts: list[str]
    tone: str
    banned_claims: list[str] = []
    channels: list[str] = [
        "blog", "instagram", "tiktok", "x"]


@app.post("/campaign", response_model=CampaignKit)
def create_campaign(req: BriefRequest):
    """Run the crew end to end and return the kit."""
    if len(req.key_facts) == 0:
        raise HTTPException(
            400,
            "Brief needs at least one key_fact, or "
            "the editor has nothing to check claims "
            "against.")
    return run_campaign(req.model_dump())
