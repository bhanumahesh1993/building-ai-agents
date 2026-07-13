# app.py — FastAPI: one endpoint, one grounded answer
from __future__ import annotations

import logging
import os

import psycopg
from fastapi import FastAPI
from pydantic import BaseModel

from .workflow import workflow

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://localhost/kb")

app = FastAPI(title="Knowledge Assistant API")

_db: psycopg.Connection | None = None


def _get_db() -> psycopg.Connection:
    """Lazily connect so the module imports (and the
    app boots enough to serve /health) without a live
    Postgres reachable yet."""
    global _db
    if _db is None:
        _db = psycopg.connect(
            DATABASE_URL, autocommit=True)
    return _db


def setup_tracing() -> None:
    """Ship every LlamaIndex call to Langfuse via OTel.

    Self-disables (with a warning) when the OTel/Langfuse
    endpoint is not configured, so the app can still
    import and run offline. Reads OTEL_EXPORTER_OTLP_ENDPOINT
    / _HEADERS from the environment — see .env.example.
    """
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not endpoint:
        logger.warning(
            "OTEL_EXPORTER_OTLP_ENDPOINT not set -- "
            "LlamaIndex tracing disabled."
        )
        return
    from openinference.instrumentation.llama_index import (
        LlamaIndexInstrumentor,
    )
    LlamaIndexInstrumentor().instrument()


@app.on_event("startup")
async def _on_startup() -> None:
    setup_tracing()


class AskReq(BaseModel):
    question: str
    acl: list[str] | None = None


@app.post("/ask")
async def ask(req: AskReq):
    """Answer one question, grounded and cited."""
    result = await workflow.run(
        question=req.question, conn=_get_db(),
        acl=req.acl or ["public"])
    return result
