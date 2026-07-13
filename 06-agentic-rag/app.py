# app.py — FastAPI: one endpoint, one grounded answer
from __future__ import annotations

import psycopg
from fastapi import FastAPI
from pydantic import BaseModel
from openinference.instrumentation.llama_index \
    import LlamaIndexInstrumentor

from workflow import workflow

LlamaIndexInstrumentor().instrument()
# Reads OTEL_EXPORTER_OTLP_ENDPOINT / _HEADERS from
# the environment — see .env.example. That is the
# entire Langfuse wiring for this project.

app = FastAPI(title="Knowledge Assistant API")
DB = psycopg.connect(
    "postgresql://localhost/kb", autocommit=True)


class AskReq(BaseModel):
    question: str
    acl: list[str] | None = None


@app.post("/ask")
async def ask(req: AskReq):
    """Answer one question, grounded and cited."""
    result = await workflow.run(
        question=req.question, conn=DB,
        acl=req.acl or ["public"])
    return result
