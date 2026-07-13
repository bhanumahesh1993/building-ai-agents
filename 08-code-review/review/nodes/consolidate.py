# review/nodes/consolidate.py
from __future__ import annotations

from ..state import ReviewState

SEVERITY_ORDER = {
    "critical": 0, "high": 1, "medium": 2, "low": 3}


def _dedup(confirmed: list[dict]) -> list[dict]:
    seen: set[tuple] = set()
    out = []
    for v in confirmed:
        f = v["finding"]
        key = (f["path"], f["line"], f["claim"][:40])
        if key in seen:
            continue
        seen.add(key)
        out.append(v)
    return out


def consolidate_node(state: ReviewState) -> dict:
    """Rank and format the surviving findings."""
    verified = state["verified"]
    confirmed = [
        v for v in verified if v["verdict"] == "confirmed"]
    confirmed = _dedup(confirmed)
    confirmed.sort(
        key=lambda v: SEVERITY_ORDER[
            v["finding"]["severity"]])
    refuted = [
        v for v in verified if v["verdict"] == "refuted"]

    lines = ["# Review Findings", ""]
    lines.append(
        f"Confirmed: {len(confirmed)} · "
        f"Refuted by verification: {len(refuted)}")
    if state.get("truncated"):
        lines.append(
            "\n_Diff was capped — this review did "
            "not see the full change._")
    lines.append("")
    for v in confirmed:
        f = v["finding"]
        lines.append(
            f"- **[{f['severity'].upper()}]** "
            f"`{f['path']}:{f['line']}` "
            f"({f['reviewer']}) — {f['claim']}")
    return {"report": "\n".join(lines)}
