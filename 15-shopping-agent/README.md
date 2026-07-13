# Project 15 — E-commerce Shopping Agent

**Tier:** Intermediate  ·  **Frameworks:** OpenAI Agents SDK · MCP

Search, compare, cart — with a hard human authorization gate before any payment.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 15** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `.env.example`
- `Dockerfile`
- `catalog_server.py`
- `docker-compose.yml`
- `evals/dataset.jsonl`
- `evals/judge.py`
- `evals/run_evals.py`
- `requirements.txt`
- `shopping/agents.py`
- `shopping/app.py`
- `shopping/guardrails.py`
- `shopping/tools.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
