# crew/crew.py
from __future__ import annotations

import json
import os

from crewai import Crew, Process, Task

from .agents import (
    requirements_analyst, terraform_generator,
    policy_reviewer, cost_estimator, drift_detective,
)
from .tasks import (
    intake_task, generate_task, policy_task, cost_task,
)
from .models import IacPlan, HclBundle, PolicyReport
from .tools import parse_hcl_resources, state_diff

MAX_REVISIONS = int(os.getenv("MAX_REVISIONS", "2"))
MONTHLY_BUDGET_CAP = float(
    os.getenv("MONTHLY_BUDGET_CAP_USD", "500"))


def _core_crew() -> Crew:
    """Intake -> generate -> policy, in order."""
    return Crew(
        agents=[requirements_analyst,
                terraform_generator, policy_reviewer],
        tasks=[intake_task, generate_task, policy_task],
        process=Process.sequential,
        verbose=True,
    )


def _revise(violations: list, prior_ctx: list[Task]):
    """One rewrite-and-recheck pass, as its own small
    crew - the same shape as the marketing crew's
    Copywriter/Editor loop, applied to HCL instead of
    prose."""
    revised_hcl = Task(
        description=(
            "Rewrite the Terraform HCL to fix these "
            f"policy violations, staying inside the "
            f"original request:\n{violations}"
        ),
        expected_output="An updated HclBundle.",
        agent=terraform_generator,
        context=prior_ctx,
        output_pydantic=HclBundle,
    )
    recheck = Task(
        description=(
            "Re-run HCL Resource Parser and "
            "Deterministic Policy Check on the "
            "revised HCL. Approve, or say what is "
            "still wrong."
        ),
        expected_output="An updated PolicyReport.",
        agent=policy_reviewer,
        context=[revised_hcl] + prior_ctx,
        output_pydantic=PolicyReport,
    )
    crew = Crew(
        agents=[terraform_generator, policy_reviewer],
        tasks=[revised_hcl, recheck],
        process=Process.sequential,
    )
    crew.kickoff()
    return revised_hcl, recheck


def generate_plan(brief: str) -> IacPlan:
    """Run the crew, with a capped rewrite loop
    between the Generator and the Policy Reviewer.
    Cost and compliance are the only things this
    function ever touches - there is no path from
    here to a real cloud API."""
    core = _core_crew()
    core.kickoff(inputs={"brief": brief})

    request = intake_task.output.pydantic
    current_hcl = generate_task
    policy = policy_task.output.pydantic

    revisions = 0
    while (not policy.approved
           and revisions < MAX_REVISIONS):
        revisions += 1
        current_hcl, recheck = _revise(
            policy.violations, [intake_task])
        policy = recheck.output.pydantic

    if not policy.approved:
        policy.reviewer_notes += (
            " [Shipped unapproved: revision cap "
            "reached - do not run terraform plan on "
            "this file until a human resolves the "
            "open violations.]")

    Crew(
        agents=[cost_estimator],
        tasks=[cost_task],
        process=Process.sequential,
    ).kickoff()
    cost = cost_task.output.pydantic

    if cost.total_monthly_usd > MONTHLY_BUDGET_CAP:
        policy.reviewer_notes += (
            f" [Cost cap exceeded: "
            f"${cost.total_monthly_usd:.2f} vs "
            f"${MONTHLY_BUDGET_CAP:.2f} cap - "
            "flagged for manual sizing review.]")

    return IacPlan(
        request=request,
        hcl=current_hcl.output.pydantic,
        policy=policy,
        cost=cost,
        revisions_used=revisions,
    )


def run_drift_check(hcl_text: str,
                     live_state_path: str) -> dict:
    """Separate, read-only crew: compare a previously
    approved plan against a live-state snapshot. Takes
    no action - only ever produces a report."""
    declared = parse_hcl_resources(hcl_text)
    with open(live_state_path) as fh:
        live = json.load(fh)
    entries = state_diff(declared, live)
    task = Task(
        description=(
            "Given these raw drift entries, write a "
            "one-paragraph human-readable summary "
            f"and confirm each remediation is a "
            f"suggestion only:\n{json.dumps(entries)}"
        ),
        expected_output=(
            "A short summary plus the entries, "
            "unchanged."
        ),
        agent=drift_detective,
    )
    Crew(agents=[drift_detective],
         tasks=[task],
         process=Process.sequential).kickoff()
    return {
        "drifted": len(entries) > 0,
        "entries": entries,
        "summary": task.output.raw,
    }
