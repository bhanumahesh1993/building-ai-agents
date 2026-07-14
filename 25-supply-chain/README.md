# Project 25 — Cross-Enterprise A2A Supply-Chain Orchestrator

**Tier:** Advanced  ·  **Frameworks:** Google ADK · A2A

Two independently-owned agents negotiate a reorder across a trust boundary.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 25** of _Building AI Agents_. This folder is the complete code.

## Run it

Two independently-owned agents, each with its own package, its own MCP
tool server, and its own A2A endpoint:

- `inventory_agent/` — Northwind's buyer agent (port 8000). Watches stock
  via a stdio MCP server (`inventory_agent/mcp_server.py`) and publishes a
  public Agent Card advertising `report_stock_status`.
- `procurement_agent/` — ProcureIQ's supplier agent (port 8001). Runs a
  three-step ADK `SequentialAgent` workflow (select → compare → draft)
  against its own MCP tool server (`procurement_agent/mcp_tools.py`), then
  gates the resulting purchase order on spend before it ever crosses back
  to Northwind.

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add GOOGLE_API_KEY; the model caps and spend
                         # caps have working defaults already

# Run the two-agent demo (spins up both ADK/A2A servers, then delegates
# a reorder across the boundary):
uv run --no-project python run.py

# Or run each agent standalone, one process per org:
uv run --no-project uvicorn inventory_agent.agent:app --port 8000
uv run --no-project uvicorn procurement_agent.agent:app --port 8001
```

**Human approval on spend.** `procurement_agent/agent.py`'s
`apply_spend_gate()` is a structural, in-code gate, not a prompt
instruction: any reorder whose total is under the `$5000` soft cap
completes immediately; anything between the soft and `$25000` hard cap
pauses in an `input-required` state — no `PurchaseOrder` is returned
until a human calls `on_confirm()` with sign-off; anything over the hard
cap is refused outright. See `tests/test_spend_gate.py`.

**Remote output is untrusted.** ProcureIQ's completed-task artifact
crosses an organizational trust boundary the same way any third-party
API response does. `a2a_client.extract_purchase_order()` validates it
against `shared.schemas.PurchaseOrder` before a single field is used —
malformed or malicious artifacts are rejected, not passed through. See
`tests/test_remote_output_validation.py`.

### Caveat: A2A task-lifecycle hooks

The installed `google-adk` (2.4.0) ships `to_a2a()` as
`@a2a_experimental` and, as released, does not yet accept `on_task` /
`on_resume` kwargs — there is no hook to wire the spend gate into the
*live* A2A HTTP transport in this version. The gate itself
(`apply_spend_gate` / `on_reorder` / `on_confirm`) is fully real,
structural code and is exercised directly in tests; only its wiring into
this particular experimental transport shim is pending an ADK release
that exposes the hook. `run.py`'s end-to-end demo drives `on_reorder`
directly rather than through the ASGI app for the same reason.

## Files

- `a2a_client.py` — A2A JSON-RPC client + `extract_purchase_order()`
  (untrusted-remote-output validation)
- `docker-compose.demo.yml`
- `evals/run_evals.py`
- `inventory_agent/agent.py`, `inventory_agent/mcp_server.py`
- `procurement_agent/agent.py`, `procurement_agent/mcp_tools.py`,
  `procurement_agent/workflow.py`
- `run.py`
- `shared/schemas.py` — the cross-boundary task schema
- `tests/` — spend gate, cross-boundary schema, remote-output
  validation, Agent Card structure, keyless-import checks

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
