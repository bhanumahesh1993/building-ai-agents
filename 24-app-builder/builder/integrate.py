# builder/integrate.py
from __future__ import annotations

from pathlib import Path

from .planner import BuildPlan


class IntegrationReport:
    """What integration found, if anything."""

    def __init__(self) -> None:
        self.ok = True
        self.issues: list[str] = []

    def flag(self, msg: str) -> None:
        self.ok = False
        self.issues.append(msg)


def integrate_project(
    root: Path, plan: BuildPlan,
) -> IntegrationReport:
    """Reconcile the four workers against one contract."""
    report = IntegrationReport()
    api_src = _read(root / "backend/app/api")
    front_src = _read(root / "frontend/src")

    for ep in plan.contract.endpoints:
        path = ep["path"]
        if path not in api_src:
            report.flag(f"api never defines {path}")
        writes = ep["method"] in ("POST", "PATCH")
        if writes and path not in front_src:
            report.flag(f"frontend never calls {path}")

    _write_run_script(root)
    return report


def _read(folder: Path) -> str:
    if not folder.exists():
        return ""
    return "\n".join(
        p.read_text(errors="ignore")
        for p in folder.rglob("*") if p.is_file())


def _write_run_script(root: Path) -> None:
    (root / "run.sh").write_text(
        "#!/bin/sh\n"
        "cd backend && uvicorn app.main:app "
        "--host 0.0.0.0 --port 8000 &\n"
        "cd ../frontend && python3 -m http.server "
        "5173\n")
