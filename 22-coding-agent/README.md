# Project 22 — Autonomous Coding & PR Agent

**Tier:** Advanced  ·  **Frameworks:** Claude Agent SDK · Docker

Issue→plan→implement in a sandbox→test→open a PR. Never merges autonomously.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 22** of _Building AI Agents_. This folder is the complete code.

## Run it

> **Every run is sandboxed and this agent never merges.** Each issue gets
> its own disposable git worktree, executed inside a container with
> `--network none` (no internet, no host access) — see
> [Sandbox isolation](#sandbox-isolation) below. The pipeline stops at
> an **open pull request**; there is no `merge()` function anywhere in
> this code, and nothing here ever flips a PR to merged. Branch
> protection on the real repo is the backstop of last resort, not the
> only line of defense — see [Safety](#safety).

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys (see below)
uv run --no-project pytest -q
```

All modules import with **no environment variables set** — the Claude
Agent SDK's `query`/`ClaudeAgentOptions` (in `agent/plan.py`,
`agent/implement.py`, `agent/pr.py`, `evals/judge.py`) and the Langfuse
client (in `agent/app.py`) are all imported and built lazily, on first
use inside a function, not at module import time.

Running the service for real (not just the offline test suite)
additionally requires:

- `ANTHROPIC_API_KEY` — the lead/worker/judge agents (planning,
  implementation, PR-description writing, and the eval judge) all call
  the Claude Agent SDK.
- `docker` on `PATH`, plus the `coding-agent-runner:latest` image built
  from this project's `Dockerfile` — `agent/sandbox.py` shells out to
  `docker run` for every command executed against a cloned repo.
- `GITHUB_APP_ID` / `GITHUB_APP_PRIVATE_KEY` — only needed if you swap
  `agent/github_stub.py` for a real GitHub App integration; the stub
  writes PR records to a local JSONL file so the book's build runs
  with no external account required.
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` — for
  tracing via the `@observe` decorator on `agent/app.py`'s endpoint.

```bash
uvicorn agent.app:app --host 0.0.0.0 --port 8000
```

### Dependency caveat: `claude-agent-sdk`

`requirements.txt`'s `claude-agent-sdk==0.9.4` pin is illustrative and
does not exist on PyPI at the time of this hardening pass — the
latest published release resolves to `0.2.117`. `pyproject.toml` pins
`claude-agent-sdk>=0.1,<1.0` instead, which installs cleanly on Python
3.12 and includes the version this project actually installs with.
`uv pip install -e ".[dev]"` and `uv lock` both succeed with this
range; if a future SDK release moves past `1.0`, bump the upper bound
accordingly.

### Sandbox isolation

Every command the agent runs against a cloned repo executes inside a
container, never on the host:

- `docker run --rm --network none --memory 1g --cpus 1` — no
  internet, no host network, and hard resource caps.
- Exactly one bind mount: the sandbox's own disposable worktree at
  `/work`, read-write. No docker socket, no root filesystem, no home
  directory is ever exposed to the container.
- A `PreToolUse` hook (`agent/implement.py::_veto_protected_paths`)
  denies any `Edit`/`Write` targeting `.github/` or `.env*`, even
  though the agent is already sandboxed — CI/CD config and secrets
  stay human-approval-only regardless of what the container can reach.
- The plan → implement → test → fix loop is capped at
  `MAX_RETRIES = 3` retries (`agent/loop.py`); a suite that never
  passes is reported as failing, not looped on forever.

See `tests/test_sandbox_isolation.py` and `tests/test_never_merge.py`
for the tests that assert these guarantees structurally.

## Files

- `.env.example`
- `Dockerfile`
- `pyproject.toml` / `.python-version` / `uv.lock`
- `agent/agent.py`
- `agent/app.py`
- `agent/context.py`
- `agent/github_stub.py` — the PR stub with no `merge()` path
- `agent/implement.py`
- `agent/loop.py` — the capped plan→implement→test→fix retry loop
- `agent/plan.py`
- `agent/pr.py`
- `agent/prompts.py`
- `agent/sandbox.py` — Docker sandbox: `--network none`, one scoped mount
- `agent/test_runner.py`
- `evals/judge.py`
- `requirements.txt`
- `tests/test_self_correct.py` — the retry loop caps at `MAX_RETRIES`
- `tests/test_never_merge.py` — structural guard: no `merge()` anywhere
- `tests/test_sandbox_isolation.py` — `--network none`, scoped mount, path-scoped hook

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
