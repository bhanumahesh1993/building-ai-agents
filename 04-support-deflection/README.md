# Project 04 — Tier-1 Support Deflection System

**Tier:** Starter  ·  **Frameworks:** LangGraph · MCP

Routes, answers from a KB with citations, or escalates with a structured handoff.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 04** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `.env.example`
- `Dockerfile`
- `support/app.py`
- `support/evals/judge.py`
- `support/evals/run_evals.py`
- `support/graph.py`
- `support/ingest.py`
- `support/nodes/answer.py`
- `support/nodes/classify.py`
- `support/nodes/escalate.py`
- `support/nodes/retrieve.py`
- `support/state.py`
- `support/ticket_server.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
