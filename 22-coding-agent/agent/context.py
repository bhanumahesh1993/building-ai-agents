# agent/context.py
from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .sandbox import Sandbox

MAX_FILES = 40
MAX_SNIPPET = 800


@dataclass
class RepoContext:
    """A curated map, not a copy, of the repository."""
    tree: str
    test_command: str
    relevant_files: dict[str, str] = field(
        default_factory=dict)


def _list_tree(box: Sandbox) -> str:
    res = box.run(["find", ".", "-type", "f",
                    "-name", "*.py"])
    files = sorted(res.stdout.splitlines())[:MAX_FILES]
    return "\n".join(files)


def _detect_test_command(box: Sandbox) -> str:
    if (box.host_path / "pytest.ini").exists():
        return "pytest -q"
    if (box.host_path / "package.json").exists():
        return "npm test --silent"
    return "pytest -q"


def _grep_relevant(
    box: Sandbox, keywords: list[str]
) -> dict[str, str]:
    hits: dict[str, str] = {}
    for kw in keywords:
        res = box.run(
            ["grep", "-rl", "--include=*.py", kw, "."])
        for path in res.stdout.splitlines()[:5]:
            if path in hits:
                continue
            text = Path(box.host_path / path).read_text(
                errors="ignore")
            hits[path] = text[:MAX_SNIPPET]
    return hits


def build_context(
    box: Sandbox, issue_title: str, issue_body: str
) -> RepoContext:
    """Build a compact map: tree, test cmd, likely files."""
    keywords = [
        w.strip(".,:;\"'()")
        for w in (issue_title + " " + issue_body).split()
        if len(w) > 4
    ][:8]
    return RepoContext(
        tree=_list_tree(box),
        test_command=_detect_test_command(box),
        relevant_files=_grep_relevant(box, keywords),
    )
