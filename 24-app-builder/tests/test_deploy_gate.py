# tests/test_deploy_gate.py
from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from builder.deploy import DeployRefused, deploy
from builder.verify import VerifyResult


def _verify(all_pass: bool) -> VerifyResult:
    v = VerifyResult()
    v.passed = {"AC-1": all_pass, "AC-2": all_pass}
    return v


def test_deploy_refuses_when_criteria_are_failing():
    """Never deploy without passing tests -- this must be
    checked before any docker command ever runs."""
    with patch("builder.deploy.subprocess.run") as run:
        with pytest.raises(DeployRefused, match="not all passing"):
            deploy(
                Path("/tmp/whatever"), _verify(False),
                approved=True, build_id="b1")
        run.assert_not_called()


def test_deploy_refuses_without_human_approval():
    """Never deploy without human approval, even if every
    acceptance criterion passed."""
    with patch("builder.deploy.subprocess.run") as run:
        with pytest.raises(DeployRefused, match="human approval"):
            deploy(
                Path("/tmp/whatever"), _verify(True),
                approved=False, build_id="b1")
        run.assert_not_called()


def test_deploy_refuses_when_neither_gate_is_met():
    with pytest.raises(DeployRefused, match="not all passing"):
        deploy(
            Path("/tmp/whatever"), _verify(False),
            approved=False, build_id="b1")


def test_deploy_builds_and_runs_only_after_both_gates_pass():
    """Both gates met: exactly one build, one run, using the
    build_id in the image tag."""
    completed = subprocess.CompletedProcess(
        args=[], returncode=0, stdout="abcdef0123456789\n")
    with patch(
        "builder.deploy.subprocess.run", return_value=completed
    ) as run:
        result = deploy(
            Path("/tmp/generated"), _verify(True),
            approved=True, build_id="b42", port=9000)

    assert run.call_count == 2
    build_cmd, run_cmd = (c.args[0] for c in run.call_args_list)
    assert build_cmd[:3] == ["docker", "build", "-t"]
    assert build_cmd[3] == "generated-app:b42"
    assert "run" in run_cmd
    assert "9000:8000" in run_cmd
    assert result.image == "generated-app:b42"
    assert result.container_id == "abcdef012345"
    assert result.url == "http://localhost:9000"
