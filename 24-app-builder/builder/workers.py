# builder/workers.py
from __future__ import annotations

import asyncio
import os

from .planner import BuildPlan, ComponentTask

WORKER_MODEL = os.getenv(
    "WORKER_MODEL", "claude-sonnet-4-6")

COMPONENT_PATHS = {
    "schema": "backend/app/models",
    "api": "backend/app/api",
    "frontend": "frontend/src",
    "tests": "tests",
}

WORKER_PROMPT = """You are the {component} builder for
a small full-stack app. Build ONLY your slice, against
this frozen contract. Never touch another folder.

Entities: {entities}
Endpoints: {endpoints}

Your instructions:
{instructions}"""


def _scope_hook(prefix: str):
    """Deny any edit outside this worker's own folder."""
    async def _veto(input_data, tool_use_id, context):
        tool = input_data.get("tool_name", "")
        args = input_data.get("tool_input", {})
        target = str(args.get("file_path", ""))
        allowed = target.startswith(prefix)
        allowed = allowed or target == "CLAUDE.md"
        if tool in ("Edit", "Write") and not allowed:
            return {"hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason":
                    f"out of scope: not under {prefix}",
            }}
        return {}
    return _veto


def _options(root: str, prefix: str):
    # Imported lazily so this module can be imported (and
    # _scope_hook's path-scoping logic tested) without
    # claude-agent-sdk installed or any credentials present.
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

    return ClaudeAgentOptions(
        system_prompt="You write small, correct code.",
        model=WORKER_MODEL,
        cwd=root,
        allowed_tools=["Read", "Write", "Edit", "Bash"],
        permission_mode="acceptEdits",
        hooks={"PreToolUse": [HookMatcher(
            hooks=[_scope_hook(prefix)])]},
    )


async def _build_one(
    root: str, plan: BuildPlan, task: ComponentTask,
) -> str:
    """Run one sandboxed component worker to completion."""
    from claude_agent_sdk import query

    prefix = COMPONENT_PATHS[task.component]
    prompt = WORKER_PROMPT.format(
        component=task.component,
        entities=list(plan.contract.entities),
        endpoints=plan.contract.endpoints,
        instructions=task.instructions,
    )
    async for _ in query(
        prompt=prompt, options=_options(root, prefix)
    ):
        pass
    return task.component


async def build_all_components(
    root: str, plan: BuildPlan,
) -> list[str]:
    """Fan out one sandboxed worker per component."""
    return list(await asyncio.gather(*(
        _build_one(root, plan, task)
        for task in plan.tasks
    )))


async def retry_component(
    root: str, plan: BuildPlan, component: str,
    feedback: str,
) -> str:
    """Re-run one worker with the failing check's detail."""
    task = next(
        t for t in plan.tasks if t.component == component)
    patched = task.model_copy(update={
        "instructions": task.instructions
        + "\n\nPrevious attempt failed:\n" + feedback,
    })
    return await _build_one(root, plan, patched)
