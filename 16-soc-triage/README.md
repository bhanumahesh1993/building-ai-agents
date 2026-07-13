# Project 16 — Autonomous SOC Alert-Triage System

**Tier:** Advanced  ·  **Frameworks:** LangGraph · MCP

Bounded autonomy: read-only enrichment is autonomous, state-changing response is gated.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 16** of _Building AI Agents_. This folder is the complete code.

## Run it

This is a defensive-security tool: it triages SIEM alerts and recommends a
response, but it is built for **bounded autonomy** — read-only enrichment
(asset, user, and threat-intel lookups, plus correlation across recent
alerts) always runs on its own, while any state-changing response
(`disable_account`, `isolate_host`) is hard-gated behind a structural
`langgraph` `interrupt()` and a human's explicit approval. The verdict/
reasoning node itself is never given those tools — it can only emit an
opinion for `triage/nodes/respond.py` to act on, so there is no prompt path
that lets the model contain a host or disable an account on its own.

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

The package imports and its deterministic tests (the bounded-autonomy gate,
verdict accuracy and false-negative rate on a labeled set) run offline with
no environment variables set: `uv run --no-project pytest -q`.

For live use — a real verdict from the model, and a real stdio round trip to
the stub SIEM/intel MCP servers — you need an `ANTHROPIC_API_KEY` set in
`.env`. Without it, `verdict_node` builds its `ChatAnthropic` client lazily
and will only raise the first time it actually tries to reach the model —
not at import time. `tests/test_live.py` exercises the real model and the
real MCP stub servers end to end; it is marked
`@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), ...)` so it
stays skipped until a key is present.

## Files

- `.env.example`
- `Dockerfile`
- `docker-compose.yml`
- `evals/run_evals.py`
- `mcp_servers/__init__.py`
- `mcp_servers/intel_stub.py`
- `mcp_servers/siem_stub.py`
- `pyproject.toml`
- `requirements.txt`
- `tests/__init__.py`
- `tests/test_gate.py`
- `tests/test_live.py`
- `tests/test_verdict_accuracy.py`
- `triage/__init__.py`
- `triage/app.py`
- `triage/graph.py`
- `triage/nodes/__init__.py`
- `triage/nodes/correlate.py`
- `triage/nodes/enrich.py`
- `triage/nodes/normalize.py`
- `triage/nodes/respond.py`
- `triage/nodes/verdict.py`
- `triage/prompts.py`
- `triage/state.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
