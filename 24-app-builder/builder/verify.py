# builder/verify.py
from __future__ import annotations

import subprocess
import time
from pathlib import Path

import httpx

CRITERION_OWNER = {
    "AC-1": "schema", "AC-2": "api",
    "AC-3": "api", "AC-4": "api", "AC-5": "api",
}


class VerifyResult:
    """Per-criterion pass/fail plus the overall verdict."""

    def __init__(self) -> None:
        self.passed: dict[str, bool] = {}
        self.details: dict[str, str] = {}

    @property
    def all_passed(self) -> bool:
        return bool(self.passed) and all(
            self.passed.values())

    def failing(self) -> list[str]:
        return [c for c, ok in self.passed.items()
                if not ok]


def start_sandbox_app(root: Path, port: int = 8090) -> str:
    """Run the generated app in a network-isolated box."""
    subprocess.run(
        ["docker", "network", "create", "--internal",
         "verify-net"], capture_output=True)
    subprocess.run(
        ["docker", "build", "-t", "verify-run",
         str(root)], check=True, capture_output=True)
    subprocess.run(
        ["docker", "run", "-d", "--rm",
         "--network", "verify-net",
         "-p", f"127.0.0.1:{port}:8000",
         "--memory", "512m", "--cpus", "1",
         "verify-run"], check=True, capture_output=True)
    time.sleep(2)   # let uvicorn come up
    return f"http://127.0.0.1:{port}"


async def check_classpoll(base_url: str) -> VerifyResult:
    """Run the five ClassPoll acceptance checks live."""
    result = VerifyResult()
    async with httpx.AsyncClient(
        base_url=base_url, timeout=5.0
    ) as c:
        poll = (await c.post("/polls", json={
            "question": "Best language?",
            "options": ["Python", "TypeScript"],
        })).json()
        pid, opts = poll["id"], poll["options"]

        got = await c.get(f"/polls/{pid}")
        result.passed["AC-1"] = (
            got.status_code == 200
            and got.json()["question"] == poll["question"])

        before = opts[0]["vote_count"]
        v = await c.post(f"/polls/{pid}/vote",
            json={"option_id": opts[0]["id"]})
        after = v.json()["options"][0]["vote_count"]
        result.passed["AC-2"] = after == before + 1

        await c.post(f"/polls/{pid}/close")
        closed = await c.post(f"/polls/{pid}/vote",
            json={"option_id": opts[0]["id"]})
        result.passed["AC-3"] = closed.status_code == 409

        p2 = (await c.post("/polls", json={
            "question": "Q2", "options": ["A", "B"]})
        ).json()
        bad = await c.post(f"/polls/{p2['id']}/vote",
            json={"option_id": 999999})
        result.passed["AC-4"] = bad.status_code == 400

        p3 = (await c.post("/polls", json={
            "question": "Q3", "options": ["A", "B"],
            "closes_at": "2000-01-01T00:00:00Z",
        })).json()
        late = await c.post(f"/polls/{p3['id']}/vote",
            json={"option_id": p3["options"][0]["id"]})
        result.passed["AC-5"] = late.status_code == 409

        for cid, ok in result.passed.items():
            if not ok:
                result.details[cid] = "unexpected response"
    return result
