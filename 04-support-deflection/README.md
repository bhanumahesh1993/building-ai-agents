# Project 04 — Tier-1 Support Deflection System

**Tier:** Starter  ·  **Frameworks:** LangGraph · MCP

Routes, answers from a KB with citations, or escalates with a structured handoff.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 04** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

The package imports and its deterministic tests (routing logic, escalation
precision, the human-review gate) run offline with no environment variables
set: `uv run --no-project pytest -q`.

For live use — actually answering tickets end to end — you need a running
Postgres instance with the `pgvector` extension enabled (`support/ingest.py`
creates the `kb_chunks` table and embeddings) and an `ANTHROPIC_API_KEY` /
`OPENAI_API_KEY` pair set in `.env`. Without those, `classify_node`,
`answer_node`, `retrieve_node`, and `escalate_node` build their clients
lazily and will only raise the first time they actually try to reach a
model or the database — not at import time.

## Files

- `.env.example`
- `Dockerfile`
- `pyproject.toml`
- `support/__init__.py`
- `support/app.py`
- `support/evals/__init__.py`
- `support/evals/judge.py`
- `support/evals/run_evals.py`
- `support/graph.py`
- `support/ingest.py`
- `support/nodes/__init__.py`
- `support/nodes/answer.py`
- `support/nodes/classify.py`
- `support/nodes/escalate.py`
- `support/nodes/retrieve.py`
- `support/state.py`
- `support/ticket_server.py`
- `tests/test_escalation_precision.py`
- `tests/test_gate.py`
- `tests/test_routing.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
