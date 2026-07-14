# tests/test_sandbox_isolation.py
from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

from agent.implement import _veto_protected_paths
from agent.sandbox import Sandbox


def test_sandbox_run_disables_network(tmp_path):
    """Every command the agent runs inside the sandbox
    must go out with --network none -- no host or
    internet access, full stop."""
    box = Sandbox(
        sandbox_id="abc123", host_path=tmp_path,
        branch="agent/abc123")
    captured = {}

    def _fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return MagicMock(returncode=0, stdout="", stderr="")

    with patch(
        "agent.sandbox.subprocess.run", side_effect=_fake_run
    ):
        box.run(["echo", "hi"])

    cmd = captured["cmd"]
    assert "--network" in cmd
    assert cmd[cmd.index("--network") + 1] == "none"


def test_sandbox_run_mounts_only_its_own_worktree(tmp_path):
    """The container gets exactly one bind mount: this
    sandbox's own disposable worktree, read-write, at
    /work. No host path outside the worktree (docker
    socket, root fs, home dir, etc.) is ever exposed."""
    box = Sandbox(
        sandbox_id="abc123", host_path=tmp_path,
        branch="agent/abc123")
    captured = {}

    def _fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return MagicMock(returncode=0, stdout="", stderr="")

    with patch(
        "agent.sandbox.subprocess.run", side_effect=_fake_run
    ):
        box.run(["pytest", "-q"])

    cmd = captured["cmd"]
    assert cmd.count("-v") == 1
    mount_arg = cmd[cmd.index("-v") + 1]
    assert mount_arg == f"{tmp_path}:/work:rw"
    joined = " ".join(cmd)
    assert "/var/run/docker.sock" not in joined
    assert "--privileged" not in cmd
    assert "--rm" in cmd


def test_hook_blocks_github_workflow_edits():
    """The PreToolUse hook must deny edits under .github/
    -- CI/CD config is a human-approval-only path."""
    async def _run():
        return await _veto_protected_paths(
            {"tool_name": "Edit",
             "tool_input": {
                 "file_path": ".github/workflows/ci.yml"}},
            "tool_use_1", None)

    result = asyncio.run(_run())
    assert (result["hookSpecificOutput"]["permissionDecision"]
            == "deny")


def test_hook_blocks_dotenv_edits():
    """The hook must also deny writes to any .env* file --
    secrets are off-limits to the agent."""
    async def _run():
        return await _veto_protected_paths(
            {"tool_name": "Write",
             "tool_input": {"file_path": ".env"}},
            "tool_use_2", None)

    result = asyncio.run(_run())
    assert (result["hookSpecificOutput"]["permissionDecision"]
            == "deny")


def test_hook_allows_ordinary_source_edits():
    """Everything outside the protected paths is left
    alone -- the hook is a scoped veto, not a blanket
    lockdown."""
    async def _run():
        return await _veto_protected_paths(
            {"tool_name": "Edit",
             "tool_input": {"file_path": "agent/loop.py"}},
            "tool_use_3", None)

    result = asyncio.run(_run())
    assert result == {}


def test_hook_ignores_non_edit_tools():
    """A Bash command that merely mentions .github/ in its
    text (e.g. `ls .github/`) is not a file edit and must
    not be denied by this hook."""
    async def _run():
        return await _veto_protected_paths(
            {"tool_name": "Bash",
             "tool_input": {"command": "ls .github/"}},
            "tool_use_4", None)

    result = asyncio.run(_run())
    assert result == {}
