# Project 25 — Cross-Enterprise A2A Supply-Chain Orchestrator

**Tier:** Advanced  ·  **Frameworks:** Google ADK · A2A

Two independently-owned agents negotiate a reorder across a trust boundary.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 25** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `a2a_client.py`
- `docker-compose.demo.yml`
- `evals/run_evals.py`
- `inventory_agent/agent.py`
- `inventory_agent/mcp_server.py`
- `procurement_agent/agent.py`
- `procurement_agent/mcp_tools.py`
- `procurement_agent/workflow.py`
- `run.py`
- `shared/schemas.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
