# tests/test_never_merge.py
from __future__ import annotations

import ast
from pathlib import Path

import agent.app as app_module
import agent.github_stub as github_stub_module

AGENT_DIR = Path(__file__).resolve().parent.parent / "agent"


def test_no_merge_function_defined_anywhere():
    """Structural guard: nowhere in the agent package is
    there a merge() function (or anything named like one).
    Branch protection on the real GitHub repo is the
    backstop of last resort -- this asserts the code itself
    never even offers an auto-merge path to fall back on."""
    for path in AGENT_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                assert "merge" not in node.name.lower(), (
                    f"{path.name} defines {node.name}() -- "
                    "no merge path may exist in code; PRs "
                    "must stay open for human review")


def test_no_merge_route_registered():
    """No FastAPI route path or handler name mentions
    merge -- the only HTTP surface is /issues, which opens
    a PR and stops."""
    for route in app_module.app.routes:
        path = getattr(route, "path", "")
        name = getattr(route, "name", "")
        assert "merge" not in path.lower()
        assert "merge" not in name.lower()


def test_pull_request_record_has_no_merge_method():
    """The PR dataclass itself exposes no merge() -- there
    is nothing for a caller to invoke even by accident."""
    pr = github_stub_module.PullRequest(
        number=1, title="t", body="b",
        branch="br", diff="d")
    assert not hasattr(pr, "merge")
    assert pr.merged is False
    assert pr.status == "open"


def test_open_pull_request_always_opens_never_merges(
        tmp_path, monkeypatch):
    """The only way to create a PR record leaves it open;
    nothing in this stub (or a real GitHub integration
    behind it) flips status to merged."""
    monkeypatch.setattr(
        github_stub_module, "STORE",
        tmp_path / "prs.jsonl")
    pr = github_stub_module.open_pull_request(
        title="fix: something", body="body",
        branch="agent/abc123", diff="diff --git a/x b/x")
    assert pr.status == "open"
    assert pr.merged is False
