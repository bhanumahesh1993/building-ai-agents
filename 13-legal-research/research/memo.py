# research/memo.py
from __future__ import annotations

DISCLAIMER = (
    "RESEARCH AID — NOT LEGAL ADVICE. This memo is "
    "generated from a synthetic case corpus for "
    "research support only. It is not a substitute "
    "for advice from a licensed attorney, may not "
    "reflect current law in your jurisdiction, and "
    "every citation below must be independently "
    "verified before it is relied upon or filed."
)


def build_memo(
    facts: str,
    jurisdiction: str,
    issues: list[dict],
    arguments: list[dict],
    verified: dict[str, list[dict]],
) -> str:
    """Assemble the final memo. Disclaimer is never
    optional."""
    lines = [
        f"# Legal Research Memo ({jurisdiction})",
        "", DISCLAIMER, "",
        f"**Facts:** {facts}", "",
    ]
    for issue in issues:
        arg = next(
            a for a in arguments
            if a["issue_id"] == issue["id"])
        cites = verified[issue["id"]]
        lines += [
            f"## Issue: {issue['question']}", "",
            "**Argument for:**", arg["for"], "",
            "**Argument against:**", arg["against"], "",
            f"**Weight of authority:** {arg['weight']}",
            "", "**Cited authority:**",
        ]
        for c in cites:
            tag = {"verified": "✓ verified",
                   "flagged": "⚠ flagged — see note",
                   "stripped": "✗ removed"}[c["status"]]
            if c["status"] == "stripped":
                lines.append(f"- {tag}: {c['reason']}")
            else:
                lines.append(
                    f"- {tag}: {c['case_name']} "
                    f"({c['citation']}) — {c['reason']}"
                    if c["status"] == "flagged"
                    else f"- {tag}: {c['case_name']} "
                    f"({c['citation']})"
                )
        lines.append("")
    lines.append(DISCLAIMER)
    return "\n".join(lines)
