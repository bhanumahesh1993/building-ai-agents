# agent/sandbox.py
from __future__ import annotations

import shutil
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

WORKROOT = Path("/tmp/coding-agent-sandboxes")
IMAGE = "coding-agent-runner:latest"


@dataclass
class Sandbox:
    """One disposable, isolated copy of a repo."""
    sandbox_id: str
    host_path: Path
    branch: str

    def run(
        self, cmd: list[str], timeout: int = 120
    ) -> subprocess.CompletedProcess:
        """Run a command INSIDE the container, not here."""
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "1g", "--cpus", "1",
            "-v", f"{self.host_path}:/work:rw",
            "-w", "/work",
            IMAGE, *cmd,
        ]
        return subprocess.run(
            docker_cmd, capture_output=True,
            text=True, timeout=timeout,
        )


def create_sandbox(repo_url: str, base_ref: str) -> Sandbox:
    """Clone a fresh worktree copy; nothing shared with host."""
    sid = uuid.uuid4().hex[:12]
    host_path = WORKROOT / sid
    host_path.mkdir(parents=True, exist_ok=True)
    branch = f"agent/{sid}"

    subprocess.run(
        ["git", "clone", "--depth", "50", repo_url,
         str(host_path)],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(host_path), "checkout",
         "-b", branch, base_ref],
        check=True, capture_output=True,
    )
    return Sandbox(sandbox_id=sid, host_path=host_path,
                    branch=branch)


def destroy_sandbox(box: Sandbox) -> None:
    """Delete the whole workspace. Nothing to leak."""
    shutil.rmtree(box.host_path, ignore_errors=True)
