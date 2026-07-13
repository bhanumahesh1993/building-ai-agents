# lit_review/app.py
from __future__ import annotations

from fastapi import FastAPI
from langfuse import Langfuse
from pydantic import BaseModel

from .workflow import run_review

app = FastAPI(title="Literature Review Agent")
langfuse = Langfuse()  # reads LANGFUSE_* from env


class ReviewReq(BaseModel):
    topic: str


@app.post("/review")
async def review(req: ReviewReq):
    """Run the five-agent pipeline, traced end to end."""
    with langfuse.start_as_current_span(
        name="lit-review", input={"topic": req.topic},
    ) as span:
        result = await run_review(req.topic)
        span.update(output={
            "n_hypotheses": len(result["hypotheses"]),
            "citations_clean":
                result["citation_guard"]["clean"],
        })
    return result
