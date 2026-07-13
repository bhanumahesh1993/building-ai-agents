# Project 21 — Contract Due-Diligence & Redlining

**Tier:** Advanced  ·  **Frameworks:** LlamaIndex · LangGraph

Clause extraction, parallel risk flagging, playbook-grounded redlines. Not legal advice.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 21** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

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
- `requirements.txt`
- `tests/test_graph.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
