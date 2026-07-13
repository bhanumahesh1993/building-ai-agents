# Project 23 — DevOps Incident-Response Copilot

**Tier:** Advanced  ·  **Frameworks:** LangGraph · MCP

Parallel investigation and root-cause; remediation is always human-approved.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 23** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `.env.example`
- `Dockerfile`
- `copilot/app.py`
- `copilot/graph.py`
- `copilot/nodes/investigate.py`
- `copilot/nodes/remediate.py`
- `copilot/nodes/root_cause.py`
- `copilot/nodes/triage.py`
- `copilot/prompts.py`
- `copilot/runbooks.py`
- `copilot/state.py`
- `docker-compose.yml`
- `evals/run_evals.py`
- `mcp_servers/deploys_stub.py`
- `mcp_servers/logs_stub.py`
- `mcp_servers/metrics_stub.py`
- `requirements.txt`
- `tests/test_gate.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
