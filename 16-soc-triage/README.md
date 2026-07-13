# Project 16 — Autonomous SOC Alert-Triage System

**Tier:** Advanced  ·  **Frameworks:** LangGraph · MCP

Bounded autonomy: read-only enrichment is autonomous, state-changing response is gated.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 16** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `.env.example`
- `Dockerfile`
- `docker-compose.yml`
- `evals/run_evals.py`
- `mcp_servers/intel_stub.py`
- `mcp_servers/siem_stub.py`
- `requirements.txt`
- `tests/test_gate.py`
- `triage/app.py`
- `triage/graph.py`
- `triage/nodes/correlate.py`
- `triage/nodes/enrich.py`
- `triage/nodes/normalize.py`
- `triage/nodes/respond.py`
- `triage/nodes/verdict.py`
- `triage/prompts.py`
- `triage/state.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
