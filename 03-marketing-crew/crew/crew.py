# crew/crew.py
from __future__ import annotations

import json
import os

from crewai import Crew, Process, Task

from .agents import (
    strategist, copywriter, seo_specialist, editor,
    art_director,
)
from .tasks import (
    strategy_task, copy_task, seo_task, editor_task,
)
from .models import (
    CampaignKit, DraftCopy, EditorVerdict,
    ImageBrief, ImageBriefSet,
)

MAX_REVISIONS = int(os.getenv("MAX_REVISIONS", "2"))
COST_CAP_USD = float(os.getenv("COST_CAP_USD", "1.5"))
_PRICE = {"claude-sonnet-4-5": (3.0, 15.0)}  # $/M tok

image_task = Task(
    description=(
        "From the approved strategy and copy, write "
        "one art-direction brief per channel (blog "
        "hero, instagram, tiktok). Each is text for "
        "a designer: concept, composition, mood, "
        "and what to avoid. Do not generate images."
    ),
    expected_output=(
        "A list of ImageBrief entries, one per "
        "channel."
    ),
    agent=art_director,
    output_pydantic=ImageBriefSet,
)


def _usd(usage) -> float:
    """Rough cost from CrewAI's per-run token usage."""
    p_in, p_out = _PRICE["claude-sonnet-4-5"]
    return (usage.prompt_tokens * p_in
            + usage.completion_tokens * p_out) / 1e6


def _core_crew() -> Crew:
    """Strategy -> copy -> SEO -> editor, in order."""
    return Crew(
        agents=[strategist, copywriter,
                seo_specialist, editor],
        tasks=[strategy_task, copy_task, seo_task,
               editor_task],
        process=Process.sequential,
        memory=True,
        verbose=True,
    )


def _revise(feedback: str, prior_ctx: list[Task]):
    """One rewrite-and-recheck pass, as its own tiny
    crew. Process.sequential has no built-in back
    edge, so the loop itself lives here in Python."""
    revised_copy = Task(
        description=(
            "Revise the blog post and social "
            "variants using this editor feedback, "
            f"staying inside the brief:\n{feedback}"
        ),
        expected_output="An updated DraftCopy.",
        agent=copywriter,
        context=prior_ctx,
        output_pydantic=DraftCopy,
    )
    recheck = Task(
        description=(
            "Re-check the revised copy against the "
            "brand guide and the brief's key_facts. "
            "Approve, or say what is still wrong."
        ),
        expected_output="An updated EditorVerdict.",
        agent=editor,
        context=[revised_copy] + prior_ctx,
        output_pydantic=EditorVerdict,
    )
    crew = Crew(
        agents=[copywriter, editor],
        tasks=[revised_copy, recheck],
        process=Process.sequential,
    )
    crew.kickoff()
    return crew, revised_copy, recheck


def run_campaign(brief: dict) -> CampaignKit:
    """Run the crew, with a capped rewrite loop
    between the copywriter and the editor."""
    core = _core_crew()
    core.kickoff(inputs={
        "brief_json": json.dumps(brief)})
    spent = _usd(core.usage_metrics)

    strategy = strategy_task.output.pydantic
    seo = seo_task.output.pydantic
    current_copy = copy_task
    verdict = editor_task.output.pydantic

    revisions = 0
    while (not verdict.approved
           and revisions < MAX_REVISIONS
           and spent < COST_CAP_USD):
        revisions += 1
        rev_crew, current_copy, recheck = _revise(
            verdict.notes, [strategy_task, seo_task])
        spent += _usd(rev_crew.usage_metrics)
        verdict = recheck.output.pydantic

    if not verdict.approved:
        verdict.notes += (
            " [Shipped without full approval: "
            "revision or cost cap reached.]")

    image_task.context = [strategy_task, current_copy]
    Crew(
        agents=[art_director],
        tasks=[image_task],
        process=Process.sequential,
    ).kickoff()
    images: ImageBriefSet = image_task.output.pydantic

    return CampaignKit(
        strategy=strategy,
        copy=current_copy.output.pydantic,
        seo=seo,
        editor=verdict,
        image_briefs=images.briefs,
        revisions_used=revisions,
    )
