# builder/telemetry.py
from __future__ import annotations

_handler = None


def _get_handler():
    """Lazily build the client so the module imports
    without Langfuse credentials present (tests, offline
    use)."""
    global _handler
    if _handler is None:
        from langfuse.langchain import CallbackHandler
        _handler = CallbackHandler()
    return _handler


def trace_config(build_id: str) -> dict:
    """Attach the build id so spend groups by build."""
    return {"metadata": {"build_id": build_id},
            "callbacks": [_get_handler()]}
