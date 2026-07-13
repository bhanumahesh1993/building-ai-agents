# Project 01 — Personalized Tutor Agent

**Tier:** Starter  ·  **Frameworks:** Pydantic AI · Langfuse

A Socratic study coach that diagnoses level, plans a lesson, and adapts difficulty.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 01** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
uv run uvicorn tutor.app:app --reload --port 8000
```

Live use needs `ANTHROPIC_API_KEY` (the tutor/planner/diagnostic/evaluator
agents and `evals/judge.py` all call `anthropic:claude-*` models via
Pydantic AI). `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST`
are optional — tracing self-disables with a warning if unset. No external
DB service is required: `tutor.db` is a local SQLite file (path
configurable via `TUTOR_DB_PATH`).

Run the offline, deterministic test suite (no keys needed) with:

```bash
uv run pytest -q
```

## Files

- `.env.example`
- `Dockerfile`
- `evals/judge.py`
- `evals/run_evals.py`
- `requirements.txt`
- `tutor/agents.py`
- `tutor/app.py`
- `tutor/guardrails.py`
- `tutor/memory.py`
- `tutor/models.py`
- `tutor/observability.py`
- `tutor/prompts.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
