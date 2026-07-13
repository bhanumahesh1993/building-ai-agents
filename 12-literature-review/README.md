# Project 12 — Scientific Literature Review Agent

**Tier:** Intermediate  ·  **Frameworks:** Google ADK

Multi-agent review with contradiction detection and grounded hypothesis generation.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 12** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add DATABASE_URL, GOOGLE_API_KEY, LANGFUSE_* keys

# offline, deterministic tests — no keys or database needed
uv run --no-project pytest -q

# serve the API (needs a running Postgres + pgvector instance
# reachable at DATABASE_URL, and a real GOOGLE_API_KEY)
uv run uvicorn lit_review.app:app --reload
```

Every external client (Google ADK LLM agents, the `google-genai` embedding
client, the Postgres/pgvector connection, Langfuse) is built lazily behind a
`_get_*()` helper or inside the function that needs it — so every module in
this project imports cleanly with **no environment variables set at all**.
Constructing an actual `LlmAgent`/`ParallelAgent` also requires no key (only
issuing a real model call does), which is what lets `tests/test_workflow.py`
build the real ADK agent graph and drive it end to end with a faked
`_run_agent` seam, entirely offline.

Tests that hit a live model are marked `@pytest.mark.skipif` on the relevant
API key and are skipped by default; see `05-automated-grading` /
`06-agentic-rag` in this repo for the same pattern used elsewhere.

### Dependency note

`google-adk` currently emits `DeprecationWarning`s for `ParallelAgent`,
`LoopAgent`, and `SequentialAgent` in favor of a new `Workflow` API — the
warnings are harmless today but worth watching before the next `google-adk`
major bump, since the workflow in `lit_review/agents.py` and
`lit_review/workflow.py` leans on all three.

## Files

- `.env.example`
- `.python-version`
- `Dockerfile`
- `pyproject.toml`
- `requirements.txt`
- `uv.lock`
- `evals/__init__.py`
- `evals/judge.py`
- `evals/run_evals.py`
- `lit_review/__init__.py`
- `lit_review/agents.py`
- `lit_review/app.py`
- `lit_review/corpus.py`
- `lit_review/tools.py`
- `lit_review/workflow.py`
- `tests/__init__.py`
- `tests/conftest.py`
- `tests/test_corpus.py`
- `tests/test_guardrails.py`
- `tests/test_workflow.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
