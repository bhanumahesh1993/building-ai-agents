# agent/github_stub.py
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path

STORE = Path("/tmp/coding-agent-sandboxes/prs.jsonl")


@dataclass
class PullRequest:
    number: int
    title: str
    body: str
    branch: str
    diff: str
    status: str = "open"
    merged: bool = field(default=False, init=False)


def open_pull_request(
    title: str, body: str, branch: str, diff: str
) -> PullRequest:
    """Create a PR record. There is no merge() function.

    A real integration calls the GitHub REST API's
    POST /repos/{owner}/{repo}/pulls with this same
    payload. This stub exists so the book's build runs
    with no external account required.
    """
    number = int(time.time()) % 100000
    pr = PullRequest(
        number=number, title=title, body=body,
        branch=branch, diff=diff,
    )
    with STORE.open("a") as fh:
        fh.write(json.dumps({
            "number": pr.number, "title": title,
            "branch": branch, "status": "open",
        }) + "\n")
    return pr
