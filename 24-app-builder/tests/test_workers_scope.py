# tests/test_workers_scope.py
from __future__ import annotations

import asyncio

from builder.workers import _scope_hook


def _veto(prefix: str, tool: str, file_path: str):
    hook = _scope_hook(prefix)
    return asyncio.run(hook(
        {"tool_name": tool, "tool_input": {"file_path": file_path}},
        "tool-use-1", None))


def test_write_inside_component_folder_is_allowed():
    result = _veto(
        "backend/app/api", "Write", "backend/app/api/routes.py")
    assert result == {}


def test_edit_inside_component_folder_is_allowed():
    result = _veto(
        "frontend/src", "Edit", "frontend/src/index.html")
    assert result == {}


def test_write_to_claude_md_is_always_allowed():
    """CLAUDE.md is the one shared file every worker may touch."""
    result = _veto("backend/app/api", "Write", "CLAUDE.md")
    assert result == {}


def test_write_outside_component_folder_is_denied():
    """The api worker must never write into another
    component's folder -- this is the structural sandbox
    boundary, not a prompt instruction."""
    result = _veto(
        "backend/app/api", "Write", "frontend/src/index.html")
    output = result["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    assert "not under backend/app/api" in (
        output["permissionDecisionReason"])


def test_edit_outside_component_folder_is_denied():
    result = _veto(
        "frontend/src", "Edit", "backend/app/models/poll.py")
    assert (
        result["hookSpecificOutput"]["permissionDecision"]
        == "deny")


def test_read_and_bash_are_never_vetoed_by_scope():
    """The hook only gates Edit/Write; Read/Bash pass through
    (worker still runs inside its own sandboxed container)."""
    result = _veto(
        "backend/app/api", "Read", "frontend/src/index.html")
    assert result == {}
    result = _veto(
        "backend/app/api", "Bash", "frontend/src/index.html")
    assert result == {}


def test_missing_file_path_defaults_to_empty_string():
    """A tool call with no file_path must not crash the hook,
    and an empty target is out of scope for any non-root prefix."""
    hook = _scope_hook("backend/app/api")
    result = asyncio.run(hook(
        {"tool_name": "Write", "tool_input": {}},
        "tool-use-2", None))
    assert result["hookSpecificOutput"]["permissionDecision"] == (
        "deny")
