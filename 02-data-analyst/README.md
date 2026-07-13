# Project 02 — Autonomous Data Analyst

**Tier:** Starter  ·  **Frameworks:** Pydantic AI · DuckDB

NL→SQL over a sandboxed read-only connection, with self-correction and honest narration.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 02** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add ANTHROPIC_API_KEY (and Langfuse keys if tracing)
uv run python -m analyst.schema data/bikeshare.csv data/bikeshare.duckdb  # one-time ETL
uv run python -m analyst.app     # interactive NL->SQL REPL over the DuckDB file
```

No API key or running service is needed to import the package or run its
deterministic test suite:

```bash
uv run --no-project pytest -q
```

`ANTHROPIC_API_KEY` is only required at call time (`analyst.app`, `analyst.sql_agent`,
`evals.judge`) — the `pydantic_ai.Agent` instances are built lazily on first use, so
the modules import cleanly without it. `LANGFUSE_*` keys are optional and only needed
if you want tracing sent to Langfuse.

## Files

- `.env.example`
- `Dockerfile`
- `analyst/app.py`
- `analyst/charts.py`
- `analyst/critic.py`
- `analyst/runner.py`
- `analyst/schema.py`
- `analyst/sql_agent.py`
- `evals/judge.py`
- `evals/run_evals.py`
- `requirements.txt`
- `pyproject.toml`
- `tests/test_critic.py`
- `tests/test_runner.py`
- `tests/test_schema.py`
- `tests/test_sql_agent.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
