# Project 17 — Threat-Intel Briefing & Vuln Prioritization

**Tier:** Advanced  ·  **Frameworks:** CrewAI

Risk-based CVE prioritization (severity × exploit × exposure) and exec briefings.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 17** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
docker compose up -d db   # pgvector-backed dedup store
uv run uvicorn crew.app:app --reload
```

Every module imports cleanly with no environment variables set at all
(`env -i` clean) — the OpenAI client in `crew/tools.py` and the Postgres
connection string are both built lazily, on first use, not at import time.
Nothing here calls a live model, embedder, or database until you actually
run the crew, `docker compose up`, or the live-gated tests below.

Run the deterministic test suite (no API keys, no database, no network
required):

```bash
uv run --no-project pytest -q
```

`tests/test_ranking.py` exercises the deterministic severity × exploit ×
exposure scoring in `crew/ranking.py`, `tests/test_dedup.py` exercises
dedup accuracy against a mocked embedder and mocked pgvector row, and
`tests/test_guardrails.py` exercises the no-invented-CVE guard in
`crew/crew.py`. One additional test in `tests/test_dedup.py` is marked
`@pytest.mark.skipif` and only runs against the real OpenAI embedder and a
live pgvector database when `OPENAI_API_KEY` and `DATABASE_URL` are both
set — it mirrors `evals/dedup_check_eval.py`.

This project is defensive security tooling: it ingests public advisory
feeds, correlates already-published exploitation signals, and ranks
already-known CVEs against your own asset inventory — it does not probe,
exploit, or attack anything. Any vendor-attributed figures the agents cite
(KEV listings, PoC counts, exploitation claims) are vendor-reported, not
independently verified by this crew; the correlator and briefing writer are
built to hedge accordingly rather than launder a claim into false certainty.

## Files

- `.env.example`
- `.python-version`
- `Dockerfile`
- `crew/__init__.py`
- `crew/agents.py`
- `crew/app.py`
- `crew/crew.py`
- `crew/models.py`
- `crew/ranking.py`
- `crew/tasks.py`
- `crew/tools.py`
- `docker-compose.yml`
- `evals/dedup_check_eval.py`
- `evals/judge.py`
- `evals/ranking_check.py`
- `pyproject.toml`
- `requirements.txt`
- `schema.sql`
- `tests/__init__.py`
- `tests/test_dedup.py`
- `tests/test_guardrails.py`
- `tests/test_ranking.py`
- `uv.lock`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
