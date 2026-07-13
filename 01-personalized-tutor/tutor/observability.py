# tutor/observability.py
from __future__ import annotations

import base64
import logging
import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
    OTLPSpanExporter,
)
from pydantic_ai.agent import Agent

logger = logging.getLogger(__name__)


def setup_tracing() -> None:
    """Ship every agent call to Langfuse as OTel spans.

    Self-disables (with a warning) when Langfuse credentials are
    not configured, so the app can still import and run offline.
    """
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("LANGFUSE_HOST")
    if not (public_key and secret_key and host):
        logger.warning(
            "Langfuse credentials not set (LANGFUSE_PUBLIC_KEY / "
            "LANGFUSE_SECRET_KEY / LANGFUSE_HOST) -- tracing disabled."
        )
        return

    creds = base64.b64encode(
        f"{public_key}:{secret_key}".encode()
    ).decode()
    exporter = OTLPSpanExporter(
        endpoint=host + "/api/public/otel/v1/traces",
        headers={"Authorization": f"Basic {creds}"},
    )
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    Agent.instrument_all()
