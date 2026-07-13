# Project 05 — Automated Grading & Feedback

**Tier:** Starter  ·  **Frameworks:** LangGraph

Rubric scoring with an evaluator-optimizer pass and mandatory human sign-off.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 05** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
uv run uvicorn grading.app:app --reload --port 8000
```

Live use needs `ANTHROPIC_API_KEY` (the score/feedback nodes and
`evals/calibrate.py` call `claude-*` models via `langchain-anthropic`) and
`VOYAGE_API_KEY` (the similarity node embeds essays via `voyageai`).
`DATABASE_URL` must point at a Postgres instance with the `pgvector`
extension and a `class_corpus` table (see `docker-compose.yml` for a local
`db` service) — only the similarity node touches it, and only when actually
run. `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` are
optional — tracing self-disables with a warning if unset. Every client
(the LLMs and the Voyage embedder) is built lazily on first use, so the
whole package imports with zero environment variables set.

Run the offline, deterministic test suite (no keys, no DB, no network
needed) with:

```bash
uv run pytest -q
```

It covers rubric scoring, scoring consistency/variance, the
fairness/calibration evals, and the human sign-off gate (pause-and-resume
via `Command(resume=...)`). One test (`tests/test_live_api.py`) calls the
real model and is skipped automatically unless `ANTHROPIC_API_KEY` is set.

## Files

- `.env.example`
- `Dockerfile`
- `docker-compose.yml`
- `pyproject.toml`
- `requirements.txt`
- `.python-version`
- `evals/calibrate.py`
- `evals/fairness.py`
- `grading/__init__.py`
- `grading/app.py`
- `grading/graph.py`
- `grading/rubric.py`
- `grading/state.py`
- `grading/nodes/__init__.py`
- `grading/nodes/feedback.py`
- `grading/nodes/review_gate.py`
- `grading/nodes/score.py`
- `grading/nodes/similarity.py`
- `tests/test_rubric.py`
- `tests/test_score.py`
- `tests/test_similarity.py`
- `tests/test_review_gate.py`
- `tests/test_fairness_calibration.py`
- `tests/test_live_api.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
