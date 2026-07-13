# builder/telemetry.py
from __future__ import annotations

from langfuse.langchain import CallbackHandler

handler = CallbackHandler()


def trace_config(build_id: str) -> dict:
    """Attach the build id so spend groups by build."""
    return {"metadata": {"build_id": build_id},
            "callbacks": [handler]}
