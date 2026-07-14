# agent/implement.py
from __future__ import annotations

import os

from .prompts import IMPLEMENT_SYSTEM, FIX_FAILURE_SYSTEM
from .sandbox import Sandbox

WORKER_MODEL = os.getenv(
    "WORKER_MODEL", "claude-sonnet-4-6")
BLOCKED_PATHS = (".github/", ".env")


async def _veto_protected_paths(input_data, tool_use_id,
                                 context):
    """Hook: deterministically refuse risky edits."""
    tool = input_data.get("tool_name", "")
    args = input_data.get("tool_input", {})
    target = str(args.get("file_path", "")
                  or args.get("command", ""))
    if tool in ("Edit", "Write") and any(
        p in target for p in BLOCKED_PATHS
    ):
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason":
                "protected path — human approval required",
        }}
    return {}


def _options(box: Sandbox):
    # Imported lazily so this module (and the hook
    # function above, which is unit-tested directly) can
    # be imported without claude-agent-sdk installed or
    # any credentials present.
    from claude_agent_sdk import ClaudeAgentOptions, HookMatcher

    return ClaudeAgentOptions(
        system_prompt="You edit code carefully and small.",
        model=WORKER_MODEL,
        cwd=str(box.host_path),
        allowed_tools=["Read", "Edit", "Bash"],
        permission_mode="acceptEdits",
        hooks={"PreToolUse": [HookMatcher(
            hooks=[_veto_protected_paths])]},
    )


async def implement_plan(box: Sandbox, plan: dict) -> None:
    """First pass: write code and a test from the plan."""
    from claude_agent_sdk import query

    prompt = IMPLEMENT_SYSTEM.format(**plan)
    async for _ in query(
        prompt=prompt, options=_options(box)):
        pass


async def fix_failure(box: Sandbox, failures: str) -> None:
    """One targeted retry after a failed test run."""
    from claude_agent_sdk import query

    prompt = FIX_FAILURE_SYSTEM.format(failures=failures)
    async for _ in query(
        prompt=prompt, options=_options(box)):
        pass
