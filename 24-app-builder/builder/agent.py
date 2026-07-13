# builder/agent.py
from __future__ import annotations

import tempfile
from pathlib import Path

from .spec import AppSpec
from .planner import make_plan, BuildPlan
from .scaffold import scaffold_project
from .workers import build_all_components, \
    retry_component
from .integrate import integrate_project
from .verify import (
    start_sandbox_app, check_classpoll, CRITERION_OWNER,
)


class BuildResult:
    """Everything a caller needs after a build attempt."""

    def __init__(
        self, root: Path, plan: BuildPlan, verify,
        iterations: int,
    ) -> None:
        self.root = root
        self.plan = plan
        self.verify = verify
        self.iterations = iterations

    @property
    def ready(self) -> bool:
        return self.verify.all_passed


async def run_build(spec: AppSpec) -> BuildResult:
    """Spec in, a verified (not yet deployed) app out."""
    plan = await make_plan(spec)
    root = Path(tempfile.mkdtemp(prefix="appbuild-"))
    scaffold_project(root, plan)
    await build_all_components(str(root), plan)

    verify = None
    iterations = 0
    for i in range(spec.max_iterations + 1):
        integrate_project(root, plan)
        base_url = start_sandbox_app(root)
        verify = await check_classpoll(base_url)
        iterations = i
        if verify.all_passed or i == spec.max_iterations:
            break
        for cid in verify.failing():
            component = CRITERION_OWNER[cid]
            detail = verify.details.get(cid, "")
            await retry_component(
                str(root), plan, component,
                f"Fix {cid}: {detail}")

    return BuildResult(root, plan, verify, iterations)
