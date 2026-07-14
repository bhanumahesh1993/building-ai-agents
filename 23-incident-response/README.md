# Project 23 — DevOps Incident-Response Copilot

**Tier:** Advanced  ·  **Frameworks:** LangGraph · MCP

Parallel investigation and root-cause; remediation is always human-approved.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 23** of _Building AI Agents_. This folder is the complete code.

## Run it

This is a DevOps tool: it investigates an alert in parallel (logs, metrics,
deploys, dependency status) and proposes a root cause, but it is built for
**bounded autonomy** — read-only investigation always runs on its own, while
any state-changing remediation (`rollback_deploy`, `restart_service`,
`scale_service`) is hard-gated behind a structural `langgraph` `interrupt()`
and a human's explicit approval. The root-cause reasoning node itself is
never given those tools — it can only emit a hypothesis for
`copilot/nodes/remediate.py` to act on, so there is no prompt path that lets
the model roll back a deploy, restart a service, or scale a service on its
own.

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

The package imports and its deterministic tests (the bounded-autonomy gate,
root-cause correlation logic, and the runbook-RAG retrieval structure) run
offline with no environment variables set: `uv run --no-project pytest -q`.

For live use — a real hypothesis from the model, a real runbook retrieval
via the Voyage embeddings API, and a real stdio round trip to the stub
logs/metrics/deploys MCP servers — you need `ANTHROPIC_API_KEY` and
`VOYAGE_API_KEY` set in `.env`. Without them, `root_cause_node` and
`copilot/runbooks.py` build their clients lazily and will only raise the
first time they actually try to reach the model or the embeddings API — not
at import time. `tests/test_live.py` exercises the real model, the real
embeddings call, and the real MCP stub servers end to end; it is marked
`@pytest.mark.skipif(...)` so it stays skipped until both keys are present.

## Files

- `.env.example`
- `Dockerfile`
- `copilot/app.py`
- `copilot/graph.py`
- `copilot/nodes/__init__.py`
- `copilot/nodes/investigate.py`
- `copilot/nodes/remediate.py`
- `copilot/nodes/root_cause.py`
- `copilot/nodes/triage.py`
- `copilot/prompts.py`
- `copilot/runbooks.py`
- `copilot/state.py`
- `copilot/__init__.py`
- `docker-compose.yml`
- `evals/run_evals.py`
- `mcp_servers/__init__.py`
- `mcp_servers/deploys_stub.py`
- `mcp_servers/logs_stub.py`
- `mcp_servers/metrics_stub.py`
- `pyproject.toml`
- `requirements.txt`
- `tests/__init__.py`
- `tests/test_gate.py`
- `tests/test_live.py`
- `tests/test_root_cause.py`
- `tests/test_runbooks.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
