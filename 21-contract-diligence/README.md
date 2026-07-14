# Project 21 — Contract Due-Diligence & Redlining

**Tier:** Advanced  ·  **Frameworks:** LlamaIndex · LangGraph

Clause extraction, parallel risk flagging, playbook-grounded redlines. Not legal advice.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 21** of _Building AI Agents_. This folder is the complete code.

## Run it

This is a decision-support tool for lawyers, **not legal advice**. Every risk
flag is a machine-generated observation with a verbatim citation to the
clause it came from -- never a legal conclusion -- and delivery is gated
behind a structural `langgraph` `interrupt()` that requires an attorney's
explicit sign-off before a memo goes out.

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

The package imports and its deterministic tests (clause-extraction
structure, the parallel risk-flag `Send` fan-out, the playbook-grounded flag
logic, and the no-legal-conclusions guardrail) run offline with no
environment variables set: `uv run --no-project pytest -q`.

For live use you need both an LLM key and a running **pgvector** database:

- `ANTHROPIC_API_KEY` for clause extraction, risk flagging, and redlining
  (`ChatAnthropic`, built lazily by each module the first time it's needed --
  never at import time).
- `OPENAI_API_KEY` plus a `PLAYBOOK_DB_URL` pointing at a Postgres instance
  with the `pgvector` extension and a populated `playbook_positions` table,
  for grounding flags against this firm's standard positions
  (`docker-compose.yml` brings up a local `pgvector/pgvector:pg16` for this).

Without those set, everything still imports and the deterministic test suite
still passes -- only the two `tests/test_live.py` checks (real model call,
real pgvector retrieval) stay skipped via `@pytest.mark.skipif` until the
keys and database are present.

## Files

- `.env.example`
- `Dockerfile`
- `contracts/app.py`
- `contracts/extract.py`
- `contracts/graph.py`
- `contracts/ingest.py`
- `contracts/memo.py`
- `contracts/playbook.py`
- `contracts/redline.py`
- `contracts/risk_workers.py`
- `contracts/state.py`
- `docker-compose.yml`
- `evals/metrics.py`
- `pyproject.toml`
- `requirements.txt`
- `tests/test_extract.py`
- `tests/test_fanout.py`
- `tests/test_graph.py`
- `tests/test_live.py`
- `tests/test_playbook.py`
- `tests/test_risk_workers.py`
- `uv.lock`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
