# Project 02 — Autonomous Data Analyst

**Tier:** Starter  ·  **Frameworks:** Pydantic AI · DuckDB

NL→SQL over a sandboxed read-only connection, with self-correction and honest narration.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 02** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

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

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
