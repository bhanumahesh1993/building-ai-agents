# tests/test_verify_sandbox.py
from __future__ import annotations

import shutil
import subprocess
import uuid
from pathlib import Path
from unittest.mock import patch

import anyio
import pytest

from builder import verify
from builder.verify import VerifyResult, check_classpoll


def _docker_daemon_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        return subprocess.run(
            ["docker", "info"], capture_output=True, timeout=5,
        ).returncode == 0
    except Exception:
        return False


requires_docker = pytest.mark.skipif(
    not _docker_daemon_available(),
    reason="requires a running docker daemon",
)


def test_verify_result_all_passed_requires_at_least_one_check():
    """An empty result must never read as passing -- otherwise
    a build that never ran any check would look ready to ship."""
    v = VerifyResult()
    assert v.all_passed is False


def test_verify_result_all_passed_true_only_when_every_check_passes():
    v = VerifyResult()
    v.passed = {"AC-1": True, "AC-2": True}
    assert v.all_passed is True
    v.passed["AC-2"] = False
    assert v.all_passed is False
    assert v.failing() == ["AC-2"]


def test_start_sandbox_app_creates_an_internal_network():
    """The verify sandbox network must be created with
    --internal so the generated app cannot reach the
    internet during acceptance checks."""
    completed_ok = subprocess.CompletedProcess(
        args=[], returncode=0)
    with patch(
        "builder.verify.subprocess.run", return_value=completed_ok,
    ) as run, patch("builder.verify.time.sleep"):
        url = verify.start_sandbox_app(Path("/tmp/gen"), port=8123)

    calls = [c.args[0] for c in run.call_args_list]
    network_cmd, build_cmd, run_cmd = calls
    assert network_cmd[:4] == [
        "docker", "network", "create", "--internal"]
    assert build_cmd[:3] == ["docker", "build", "-t"]
    assert "--network" in run_cmd
    assert run_cmd[run_cmd.index("--network") + 1] == (
        network_cmd[-1])
    assert "127.0.0.1:8123:8000" in run_cmd
    assert url == "http://127.0.0.1:8123"


def test_start_sandbox_app_does_not_publish_to_all_interfaces():
    """The port mapping must be loopback-only, never 0.0.0.0,
    so the sandbox isn't reachable from outside the host."""
    completed_ok = subprocess.CompletedProcess(
        args=[], returncode=0)
    with patch(
        "builder.verify.subprocess.run", return_value=completed_ok,
    ) as run, patch("builder.verify.time.sleep"):
        verify.start_sandbox_app(Path("/tmp/gen"), port=9999)

    run_cmd = run.call_args_list[-1].args[0]
    port_arg = run_cmd[run_cmd.index("-p") + 1]
    assert port_arg.startswith("127.0.0.1:")


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict:
        return self._payload


class _FakeClassPollClient:
    """Enough of a ClassPoll backend, in memory, to drive
    check_classpoll's five acceptance checks deterministically."""

    def __init__(self) -> None:
        self._polls: dict[str, dict] = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, path: str, json: dict | None = None):
        if path == "/polls":
            pid = str(uuid.uuid4())
            options = [
                {"id": i, "vote_count": 0}
                for i in range(len(json["options"]))]
            self._polls[pid] = {
                "id": pid, "question": json["question"],
                "options": options, "closed": False,
                "closes_at": json.get("closes_at"),
            }
            return _FakeResponse(200, self._polls[pid])

        _, pid, action = path.strip("/").split("/")
        poll = self._polls[pid]

        if action == "close":
            poll["closed"] = True
            return _FakeResponse(200, poll)

        if action == "vote":
            expired = poll["closes_at"] == "2000-01-01T00:00:00Z"
            if poll["closed"] or expired:
                return _FakeResponse(409, {})
            opt = next(
                (o for o in poll["options"]
                 if o["id"] == json["option_id"]), None)
            if opt is None:
                return _FakeResponse(400, {})
            opt["vote_count"] += 1
            return _FakeResponse(200, poll)

        raise AssertionError(f"unexpected path {path}")

    async def get(self, path: str):
        pid = path.rsplit("/", 1)[-1]
        return _FakeResponse(200, self._polls[pid])


def test_check_classpoll_all_five_criteria_pass(monkeypatch):
    """Drives the real check_classpoll logic against an
    in-memory fake backend -- no docker, no network."""
    monkeypatch.setattr(
        verify.httpx, "AsyncClient",
        lambda **kw: _FakeClassPollClient())

    result = anyio.run(check_classpoll, "http://fake")

    assert result.all_passed
    assert set(result.passed) == {
        "AC-1", "AC-2", "AC-3", "AC-4", "AC-5"}
    assert not result.failing()


def test_check_classpoll_reports_failures_with_detail(monkeypatch):
    class _BrokenCloseClient(_FakeClassPollClient):
        """A backend whose /close is a no-op -- the poll
        never actually stops accepting votes."""
        async def post(self, path, json=None):
            if path.endswith("/close"):
                return _FakeResponse(200, {})
            return await super().post(path, json)

    monkeypatch.setattr(
        verify.httpx, "AsyncClient",
        lambda **kw: _BrokenCloseClient())

    result = anyio.run(check_classpoll, "http://fake")

    assert not result.all_passed
    assert "AC-3" in result.failing()
    assert result.details["AC-3"] == "unexpected response"


@requires_docker
def test_start_sandbox_app_is_actually_network_isolated(tmp_path):
    """Live smoke test: build a trivial app image and confirm
    the verify sandbox really cannot reach the outside network.
    Skipped unless a docker daemon is reachable."""
    (tmp_path / "Dockerfile").write_text(
        "FROM python:3.12-slim\n"
        "CMD [\"python3\", \"-c\", "
        "\"import http.server; "
        "http.server.test(HandlerClass="
        "http.server.SimpleHTTPRequestHandler, port=8000, "
        "bind='0.0.0.0')\"]\n"
    )
    port = 18099
    try:
        base_url = verify.start_sandbox_app(tmp_path, port=port)
        import httpx as _httpx
        resp = _httpx.get(base_url, timeout=10.0)
        assert resp.status_code in (200, 404)

        # A container on the --internal network must not be
        # able to resolve/reach the public internet.
        container_id = subprocess.run(
            ["docker", "ps", "-q", "--filter",
             "ancestor=verify-run"],
            capture_output=True, text=True, check=True,
        ).stdout.strip().splitlines()[0]
        probe = subprocess.run(
            ["docker", "exec", container_id, "python3", "-c",
             "import urllib.request; "
             "urllib.request.urlopen("
             "'http://example.com', timeout=3)"],
            capture_output=True, timeout=15,
        )
        assert probe.returncode != 0
    finally:
        subprocess.run(
            ["docker", "ps", "-q", "--filter",
             "ancestor=verify-run"],
            capture_output=True, text=True,
        )
        ids = subprocess.run(
            ["docker", "ps", "-q", "--filter",
             "ancestor=verify-run"],
            capture_output=True, text=True,
        ).stdout.split()
        for cid in ids:
            subprocess.run(
                ["docker", "kill", cid], capture_output=True)
        subprocess.run(
            ["docker", "network", "rm", "verify-net"],
            capture_output=True)
