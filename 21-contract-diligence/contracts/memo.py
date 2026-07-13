# contracts/memo.py
from __future__ import annotations

from .state import DDState

DISCLAIMER = (
    "DECISION-SUPPORT -- NOT LEGAL ADVICE. Every flag "
    "below is a machine-generated observation, not a "
    "legal conclusion. It must be reviewed by a "
    "qualified attorney before any clause is relied "
    "upon, executed, or waived."
)


def build_memo(state: DDState) -> str:
    """Assemble the due-diligence memo across the set."""
    lines = [
        DISCLAIMER, "",
        f"# Due-Diligence Memo -- Matter "
        f"{state['matter_id']}", "",
    ]
    by_sev = {"high": [], "medium": [], "low": []}
    for g in state.get("grounded", []):
        by_sev[g["severity"]].append(g)
    lines.append(
        f"## Summary: {len(by_sev['high'])} high, "
        f"{len(by_sev['medium'])} medium, "
        f"{len(by_sev['low'])} low, across "
        f"{len(state['contracts'])} contracts")
    by_clause = {
        r["clause_id"]: r for r in state.get("redlines", [])}
    for sev in ("high", "medium", "low"):
        if not by_sev[sev]:
            continue
        lines.append(f"\n## {sev.upper()} severity")
        for g in by_sev[sev]:
            lines.append(
                f"\n### {g['clause_type']} -- "
                f"{g['clause_id']}")
            lines.append(f"> {g['quote']}")
            lines.append(
                f"\n{g['rationale']} "
                f"(playbook: {g['playbook_ref']})")
            rl = by_clause.get(g["clause_id"])
            if rl:
                lines.append(
                    f"\n**Proposed redline:** "
                    f"{rl['proposed_text']}")
                lines.append(f"*Why:* {rl['rationale']}")
    lines.append(f"\n---\n{DISCLAIMER}")
    return "\n".join(lines)


def memo_node(state: DDState) -> dict:
    """Assemble the memo; no model call happens here."""
    return {"memo": build_memo(state)}
