# evals/run_evals.py
from __future__ import annotations

import json

import anyio

from research.orchestrator import run_research
from research.synthesize import synthesize_issue
from research.citations import verify_citations


async def run_one(facts: str, jurisdiction: str) -> dict:
    state = await run_research(facts, jurisdiction)
    args = [await synthesize_issue(f)
            for f in state["findings"]]
    total = verified_ct = flagged_ct = 0
    for a in args:
        cites = a["for_cites"] + a["against_cites"]
        checked = await verify_citations(cites)
        total += len(checked)
        verified_ct += sum(
            1 for c in checked
            if c["status"] == "verified")
        flagged_ct += sum(
            1 for c in checked
            if c["status"] == "flagged")
    return {
        "issues_found": len(state["issues"]),
        "citation_validity": (
            verified_ct / total if total else 0.0),
        "flag_rate": (
            flagged_ct / total if total else 0.0),
    }


if __name__ == "__main__":
    with open("evals/dataset.jsonl") as fh:
        for line in fh:
            case = json.loads(line)
            result = anyio.run(
                run_one, case["facts"],
                case["jurisdiction"])
            print(case["facts"][:40], result)
