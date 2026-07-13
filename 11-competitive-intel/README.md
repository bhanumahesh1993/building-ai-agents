# Project 11 — Competitive-Intelligence Monitor

**Tier:** Intermediate  ·  **Frameworks:** LangGraph · pgvector

Parallel fetch, semantic change detection, significance scoring, scheduled digests.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 11** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
uv run uvicorn monitor.app:app --reload --port 8000
```

Live use needs `ANTHROPIC_API_KEY` (the diff, score, and digest nodes call
`claude-sonnet-4-5` directly, and `fetch.py` embeds page text via the same
client) and `DATABASE_URL` (a Postgres + pgvector instance for snapshot
storage). `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST`
are optional — tracing self-disables with a warning if unset.
`MIN_FETCH_INTERVAL_SECONDS` (default `2.0`) throttles repeat fetches of
the same competitor domain; every fetch is also gated on that domain's
`robots.txt`.

Run the offline, deterministic test suite (no keys, no DB, no network
needed) with:

```bash
uv run pytest -q
```

## Files

- `.env.example`
- `Dockerfile`
- `evals/run_evals.py`
- `monitor/app.py`
- `monitor/fetch_tool.py`
- `monitor/graph.py`
- `monitor/nodes/computer_use_fallback.py`
- `monitor/nodes/diff.py`
- `monitor/nodes/digest.py`
- `monitor/nodes/fetch.py`
- `monitor/nodes/score.py`
- `monitor/prompts.py`
- `monitor/registry.py`
- `monitor/schedule.py`
- `monitor/state.py`
- `pyproject.toml`
- `requirements.txt`
- `tests/test_diff.py`
- `tests/test_fetch_tool.py`
- `tests/test_registry.py`
- `tests/test_score.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
