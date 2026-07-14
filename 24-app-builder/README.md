# Project 24 — Full-Stack App Builder Agent

**Tier:** Advanced  ·  **Frameworks:** Claude Agent SDK

Spec→plan→parallel build→verify→deploy. The book's spec-driven method, executable.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 24** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys (see below)
uv run --no-project pytest -q
```

All modules import with **no environment variables set** — external
clients (the Claude Agent SDK, Langfuse) and every Docker/subprocess
call are built or invoked lazily inside functions, not at import time.

Running the service for real (not just the offline test suite)
additionally requires:

- `ANTHROPIC_API_KEY` — the lead planner, the four component workers,
  and the eval judge all call the Claude Agent SDK.
- A running **Docker daemon** — `builder/verify.py` builds and runs
  the generated app inside a `--network --internal`, loopback-only
  sandbox to run acceptance checks before anything is offered for
  deploy; `builder/deploy.py` builds and runs the real container only
  after both gates (`verify.all_passed` and human `approved`) pass.
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` —
  optional; only needed for `builder/telemetry.py`'s trace callback.

```bash
uvicorn builder.app:app --host 0.0.0.0 --port 8000
```

### Dependency caveat: `claude-agent-sdk`

`requirements.txt`'s `claude-agent-sdk==0.9.2` pin is illustrative and
does not exist on PyPI at the time of this hardening pass — the
latest published release resolves to `0.2.117`. `pyproject.toml` pins
`claude-agent-sdk>=0.1,<1.0` instead, which installs cleanly on Python
3.12 and includes the version this project actually installs with.
`uv pip install -e ".[dev]"` and `uv lock` both succeed with this
range; if a future SDK release moves past `1.0`, bump the upper bound
accordingly.

## Files

- `.env.example`
- `Dockerfile`
- `pyproject.toml` / `.python-version` / `uv.lock`
- `builder/agent.py` — plan → scaffold → build → verify → deploy loop
- `builder/app.py`
- `builder/deploy.py` — the deploy gate: passing tests AND human approval
- `builder/integrate.py`
- `builder/planner.py`
- `builder/scaffold.py`
- `builder/spec.py` — EARS acceptance-criteria spec model
- `builder/telemetry.py` — lazy Langfuse callback handler
- `builder/verify.py` — network-isolated verify sandbox
- `builder/workers.py` — path-scoped PreToolUse hook per component worker
- `docker-compose.yml`
- `evals/dataset.jsonl`
- `evals/judge.py`
- `evals/run_evals.py`
- `requirements.txt`
- `skills/scaffold-conventions/SKILL.md`
- `tests/test_gate.py` — acceptance-gate loop shape
- `tests/test_spec.py` — EARS criterion rendering and scope guardrail
- `tests/test_planner.py` — plan/contract JSON parsing
- `tests/test_workers_scope.py` — path-scoped PreToolUse hook boundary
- `tests/test_deploy_gate.py` — never deploy without passing tests + approval
- `tests/test_verify_sandbox.py` — network-isolated sandbox invocation shape
- `tests/test_agent_pipeline.py` — plan→scaffold→build→verify→deploy order

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
