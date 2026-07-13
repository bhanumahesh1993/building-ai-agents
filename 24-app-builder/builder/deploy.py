# builder/deploy.py
from __future__ import annotations

import subprocess
from pathlib import Path

from .verify import VerifyResult

IMAGE_PREFIX = "generated-app"


class DeployRefused(Exception):
    """Raised whenever a required gate was not met."""


class DeployResult:
    def __init__(
        self, image: str, container_id: str, url: str,
    ) -> None:
        self.image = image
        self.container_id = container_id
        self.url = url


def deploy(
    root: Path, verify: VerifyResult, approved: bool,
    build_id: str, port: int = 8080,
) -> DeployResult:
    """Build and run the real container. Gated twice."""
    if not verify.all_passed:
        raise DeployRefused(
            "acceptance criteria are not all passing")
    if not approved:
        raise DeployRefused(
            "no human approval recorded for this build")

    image = f"{IMAGE_PREFIX}:{build_id}"
    subprocess.run(
        ["docker", "build", "-t", image, str(root)],
        check=True, capture_output=True)
    run = subprocess.run(
        ["docker", "run", "-d",
         "-p", f"{port}:8000",
         "--memory", "512m", "--cpus", "1", image],
        check=True, capture_output=True, text=True)
    return DeployResult(
        image=image, container_id=run.stdout.strip()[:12],
        url=f"http://localhost:{port}")
