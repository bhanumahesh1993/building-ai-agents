# tutor/observability.py
from __future__ import annotations

import base64
import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from pydantic_ai.agent import Agent


def setup_tracing() -> None:
    """Ship every agent call to Langfuse as OTel spans."""
    creds = base64.b64encode(
        f"{os.environ['LANGFUSE_PUBLIC_KEY']}:"
        f"{os.environ['LANGFUSE_SECRET_KEY']}".encode()
    ).decode()
    exporter = OTLPSpanExporter(
        endpoint=os.environ["LANGFUSE_HOST"]
        + "/api/public/otel/v1/traces",
        headers={"Authorization": f"Basic {creds}"},
    )
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    Agent.instrument_all()
