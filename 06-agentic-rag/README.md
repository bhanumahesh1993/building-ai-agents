# Project 06 — Agentic RAG Knowledge Assistant

**Tier:** Intermediate  ·  **Frameworks:** LlamaIndex · pgvector

Query planning, hybrid search + RRF, reranking, and citation self-check.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 06** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `.env.example`
- `Dockerfile`
- `app.py`
- `citations.py`
- `docker-compose.yml`
- `evals/run_evals.py`
- `index.py`
- `ingest.py`
- `requirements.txt`
- `rerank.py`
- `synthesize.py`
- `workflow.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
