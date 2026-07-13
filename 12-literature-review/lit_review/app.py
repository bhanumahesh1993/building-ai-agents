# lit_review/app.py
from __future__ import annotations

from fastapi import FastAPI
from langfuse import Langfuse
from pydantic import BaseModel

from .workflow import run_review

app = FastAPI(title="Literature Review Agent")

_langfuse: Langfuse | None = None


def _get_langfuse() -> Langfuse:
    """Lazily build the client so the module imports without
    LANGFUSE_* present (tests, offline use)."""
    global _langfuse
    if _langfuse is None:
        _langfuse = Langfuse()  # reads LANGFUSE_* from env
    return _langfuse


class ReviewReq(BaseModel):
    topic: str


@app.post("/review")
async def review(req: ReviewReq):
    """Run the five-agent pipeline, traced end to end."""
    with _get_langfuse().start_as_current_span(
        name="lit-review", input={"topic": req.topic},
    ) as span:
        result = await run_review(req.topic)
        span.update(output={
            "n_hypotheses": len(result["hypotheses"]),
            "citations_clean":
                result["citation_guard"]["clean"],
        })
    return result
