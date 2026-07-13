# Project 06 — Agentic RAG Knowledge Assistant

**Tier:** Intermediate  ·  **Frameworks:** LlamaIndex · pgvector

Query planning, hybrid search + RRF, reranking, and citation self-check.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 06** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
uv run --no-project pytest -q
```

This project needs, for live (non-test) use:

- **Postgres + pgvector** (`docker-compose up db`, the default `PgVectorStore`
  backend) **or** a running **Qdrant** instance (`QDRANT_URL` /
  `QDRANT_API_KEY`, the `QdrantStore` backend) — set `DATABASE_URL` in `.env`
  for the pgvector path.
- An embedding + LLM key: `OPENAI_API_KEY` (embeddings), `ANTHROPIC_API_KEY`
  (query analysis, synthesis, citation self-check), and `COHERE_API_KEY`
  (reranking). Every client that needs one of these is built lazily on first
  use, so the whole package still imports and its offline test suite still
  passes with no environment variables set at all.

Note: `llama-index-core`, `llama-index-workflows`, and
`openinference-instrumentation-llama-index` all installed cleanly against
Python 3.12 during hardening — no compatibility issues were found.

## Files

- `.env.example`
- `Dockerfile`
- `assistant/app.py`
- `assistant/citations.py`
- `assistant/index.py`
- `assistant/ingest.py`
- `assistant/rerank.py`
- `assistant/synthesize.py`
- `assistant/workflow.py`
- `docker-compose.yml`
- `evals/run_evals.py`
- `pyproject.toml`
- `requirements.txt`
- `tests/test_citations.py`
- `tests/test_index.py`
- `tests/test_ingest.py`
- `uv.lock`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
