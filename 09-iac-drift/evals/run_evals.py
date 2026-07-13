# evals/run_evals.py
from __future__ import annotations

import json

from crew.crew import generate_plan, run_drift_check
from crew.tools import hcl_validate


def hcl_validity(plan) -> dict:
    """Does terraform validate accept what we wrote?
    Deterministic, no model call."""
    import os
    workdir = "/tmp/eval-workdir"
    os.makedirs(workdir, exist_ok=True)
    with open(f"{workdir}/main.tf", "w") as fh:
        fh.write(plan.hcl.hcl)
    return hcl_validate(workdir)


def policy_catch_rate(seeded_violations: list) -> dict:
    """Run the deterministic layer against resources
    seeded with known violations - every one must be
    caught, or the rule engine has a real gap."""
    from crew.policies import run_deterministic
    findings = run_deterministic(seeded_violations)
    caught = {f["resource"] for f in findings}
    seeded = {r["name"] for r in seeded_violations}
    return {
        "seeded": len(seeded),
        "caught": len(caught & seeded),
        "catch_rate": len(caught & seeded) / len(seeded),
    }


def drift_accuracy(hcl_text: str, live_path: str,
                    expected_drifted: set) -> dict:
    """Compare reported drift against a known-answer
    live-state fixture."""
    report = run_drift_check(hcl_text, live_path)
    found = {e["resource"] for e in report["entries"]}
    return {
        "expected": len(expected_drifted),
        "found_correct": len(found & expected_drifted),
        "false_positives": len(found - expected_drifted),
    }


if __name__ == "__main__":
    with open("evals/dataset.jsonl") as fh:
        for line in fh:
            brief = json.loads(line)["brief"]
            plan = generate_plan(brief)
            print(brief, hcl_validity(plan))
