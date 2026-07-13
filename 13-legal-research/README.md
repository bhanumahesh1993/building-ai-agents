# Project 13 — Legal Research Deep-Dive Agent

**Tier:** Intermediate  ·  **Frameworks:** Claude Agent SDK

Orchestrator + subagents + a separate citation-verification pass. Not legal advice.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 13** of _Building AI Agents_. This folder is the complete code.

## Run it

> **This is a research aid, not legal advice.** Every memo it produces
> carries a disclaimer, and every citation is either verified against
> a real case corpus, flagged as unsupported, or stripped outright —
> see [Safety](#safety) below. Nothing here is a substitute for review
> by a licensed attorney.

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys (see below)
uv run --no-project pytest -q
```

All modules import with **no environment variables set** — external
clients (the Claude Agent SDK, the OpenAI embedding client, the
Postgres/pgvector corpus connection, Langfuse) are built lazily behind
`_get_*()`/`_conn()` helpers on first use, not at import time.

Running the service for real (not just the offline test suite)
additionally requires:

- `ANTHROPIC_API_KEY` — the lead/worker/judge agents (issue-spotting,
  retrieval sub-agents, argument synthesis, citation verification) all
  call the Claude Agent SDK.
- `OPENAI_API_KEY` — `research/embeddings.py` embeds each issue's
  question with `text-embedding-3-small` before the pgvector search.
- `CASE_DB_URL` — a Postgres + pgvector database populated with a real
  case corpus (`cases` / `case_chunks` tables). Without a corpus, every
  citation resolves to "not found" and is stripped — which is the
  correct, safe default, not a bug.

```bash
uvicorn research.app:app --host 0.0.0.0 --port 8000
```

### Dependency caveat: `claude-agent-sdk`

`requirements.txt`'s `claude-agent-sdk==0.9.4` pin is illustrative and
does not exist on PyPI at the time of this hardening pass — the
latest published release resolves to `0.2.116`. `pyproject.toml` pins
`claude-agent-sdk>=0.1,<1.0` instead, which installs cleanly on Python
3.12 and includes the version this project actually installs with.
`uv pip install -e ".[dev]"` and `uv lock` both succeed with this
range; if a future SDK release moves past `1.0`, bump the upper bound
accordingly.

## Files

- `.env.example`
- `Dockerfile`
- `pyproject.toml` / `.python-version` / `uv.lock`
- `evals/run_evals.py`
- `requirements.txt`
- `research/app.py`
- `research/citations.py` — the citation verify-or-strip pass
- `research/corpus.py`
- `research/embeddings.py` — lazy OpenAI embedding client for pgvector search
- `research/issues.py`
- `research/memo.py`
- `research/orchestrator.py`
- `research/prompts.py`
- `research/retrieval_subagent.py`
- `research/synthesize.py`
- `tests/test_citations.py` — citation verify-or-strip logic (verified / flagged / stripped)
- `tests/test_issues.py` — issue-spotting decomposition
- `tests/test_synthesize.py` — argument-balance structure

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
