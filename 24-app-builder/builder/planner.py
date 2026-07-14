# builder/planner.py
from __future__ import annotations

import json
import os
from pydantic import BaseModel

from .spec import AppSpec, render_criterion

LEAD_MODEL = os.getenv("LEAD_MODEL", "claude-opus-4-8")
COMPONENTS = ("schema", "api", "frontend", "tests")


class Contract(BaseModel):
    """The shared interface every worker builds against."""
    entities: dict[str, dict[str, str]]
    endpoints: list[dict[str, str]]


class ComponentTask(BaseModel):
    """One worker's assignment against the frozen contract."""
    component: str
    instructions: str


class BuildPlan(BaseModel):
    """A contract plus one task per component."""
    contract: Contract
    tasks: list[ComponentTask]


PLAN_PROMPT = """You are the lead engineer for a small
full-stack app. Read the spec and design ONE shared
contract: the data entities (name -> field -> type)
and the REST endpoints (method, path, summary) that
together satisfy every acceptance criterion below.

Then write one self-contained instruction paragraph
per component — schema, api, frontend, tests — for a
worker who will see ONLY that paragraph and the
contract, never the other workers' output.

Return ONLY JSON:
{{"contract": {{"entities": {{}}, "endpoints": []}},
  "tasks": [{{"component": "schema",
              "instructions": "..."}}]}}

Spec goal: {goal}

Acceptance criteria:
{criteria}"""


def _parse_plan_response(text: str) -> BuildPlan:
    """Pure parsing logic: turn the lead agent's JSON
    reply into a validated BuildPlan. Factored out so the
    contract/task shape is unit-testable without the
    Claude Agent SDK or any live model call."""
    raw = json.loads(text)
    return BuildPlan(**raw)


async def make_plan(spec: AppSpec) -> BuildPlan:
    """Decompose a spec into a contract and four tasks."""
    # Imported lazily so this module can be imported (and
    # its pure parsing logic tested) without claude-agent-sdk
    # installed or any credentials present.
    from claude_agent_sdk import query, ClaudeAgentOptions

    spec.check_scope()
    criteria = "\n".join(
        f"- {render_criterion(c)}"
        for c in spec.acceptance_criteria)
    prompt = PLAN_PROMPT.format(
        goal=spec.goal, criteria=criteria)
    options = ClaudeAgentOptions(
        system_prompt=(
            "You design small, shippable app "
            "contracts. No prose outside the JSON."),
        model=LEAD_MODEL,
        allowed_tools=[],
        max_turns=1,
    )
    text = ""
    async for msg in query(prompt=prompt, options=options):
        if hasattr(msg, "content"):
            for block in msg.content:
                if hasattr(block, "text"):
                    text += block.text
    return _parse_plan_response(text)
