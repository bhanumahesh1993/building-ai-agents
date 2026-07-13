# review/github_stub.py
from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field


@dataclass
class CheckRun:
    """A minimal stand-in for a GitHub Check Run."""
    pr_id: str
    name: str
    status: str
    conclusion: str
    title: str
    summary: str
    created_at: str = field(
        default_factory=lambda: dt.datetime.now(
            dt.timezone.utc).isoformat())


_POSTED: list[CheckRun] = []


def post_check(
    pr_id: str, conclusion: str,
    title: str, summary: str,
) -> CheckRun:
    """Record a check run instead of calling GitHub.

    A real integration POSTs to
    /repos/{owner}/{repo}/check-runs. This stub keeps
    the project runnable with no GitHub App, token, or
    webhook — swap it for a real client in exercise 3.
    """
    run = CheckRun(
        pr_id=pr_id, name="ai-review-panel",
        status="completed", conclusion=conclusion,
        title=title, summary=summary)
    _POSTED.append(run)
    return run


def last_check(pr_id: str) -> CheckRun | None:
    """Fetch the most recently posted check for a PR."""
    for run in reversed(_POSTED):
        if run.pr_id == pr_id:
            return run
    return None
