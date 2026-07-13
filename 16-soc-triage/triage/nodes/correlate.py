# triage/nodes/correlate.py
from __future__ import annotations

import asyncio

from ..state import TriageState
from .enrich import SIEM, _call

PATTERN_THRESHOLD = 2


def correlate_node(state: TriageState) -> dict:
    """Check whether this alert is part of a bigger
    pattern touching the same user or host."""
    ent = state["alert"]["entities"]
    entity = ent.get("user") or ent.get("host") or ""
    text = asyncio.run(_call(
        SIEM, "query_related_alerts",
        {"entity": entity, "hours": 24}))
    lines = [l for l in text.splitlines() if l.strip()]
    count = len(lines)

    if count == 0:
        notes = f"no related alerts on {entity} in 24h"
    else:
        notes = (
            f"{count} related alert(s) on {entity} "
            "in 24h")
        if count >= PATTERN_THRESHOLD:
            notes += " — looks like a pattern, not " \
                     "a one-off"

    return {
        "related_alerts": lines,
        "pattern_notes": notes,
        "audit": [{"node": "correlate", "count": count}],
    }
