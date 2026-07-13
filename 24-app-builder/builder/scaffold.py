# builder/scaffold.py
from __future__ import annotations

from pathlib import Path

from .planner import BuildPlan

LAYOUT = (
    "backend/app", "backend/tests",
    "frontend/src", "tests",
)

BACKEND_REQS = (
    "fastapi==0.118.0\n"
    "uvicorn[standard]==0.35.0\n"
    "sqlmodel==0.0.24\n"
    "pytest==8.3.4\n"
    "httpx==0.28.1\n"
)

CLAUDE_MD = """# CLAUDE.md - read me first, always

Generated app. Do not restructure this layout.

## Layout
- backend/app - FastAPI + SQLModel
- frontend/src - static UI, no build step
- tests - one acceptance test per criterion

## Entities
{entities}

## Contract (frozen - replan before changing it)
{endpoints}

## Rules
- Stay inside your assigned folder only.
- Every test maps to exactly one criterion id.
- Build nothing the spec did not ask for.
"""


def scaffold_project(root: Path, plan: BuildPlan) -> None:
    """Lay out folders and write the agent's own brief."""
    for rel in LAYOUT:
        (root / rel).mkdir(parents=True, exist_ok=True)
    (root / "CLAUDE.md").write_text(_claude_md(plan))
    (root / "backend/requirements.txt").write_text(
        BACKEND_REQS)
    (root / "frontend/package.json").write_text(
        _package_json())


def _claude_md(plan: BuildPlan) -> str:
    entities = ", ".join(plan.contract.entities)
    lines = [
        f"- {e['method']} {e['path']} - {e['summary']}"
        for e in plan.contract.endpoints
    ]
    return CLAUDE_MD.format(
        entities=entities, endpoints="\n".join(lines))


def _package_json() -> str:
    return (
        '{"name": "app-frontend", "private": true, '
        '"scripts": {"start": '
        '"python3 -m http.server 5173"}}'
    )
