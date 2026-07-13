# Project 15 — E-commerce Shopping Agent

**Tier:** Intermediate  ·  **Frameworks:** OpenAI Agents SDK · MCP

Search, compare, cart — with a hard human authorization gate before any payment.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 15** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys (see below)
uv run --no-project pytest -q
```

All modules import with **no environment variables set** — the OpenAI
Agents SDK `Agent`s (concierge, search, comparator, cart/checkout gate)
are built lazily behind `get_*()` helpers in `shopping/agents.py` on
first use, not at import time, and `evals/judge.py`'s `OpenAI` client
is likewise built lazily behind `_get_client()`.

Running the service for real (not just the offline test suite)
additionally requires:

- `OPENAI_API_KEY` — the concierge/search/comparator/cart-gate agents
  (`LEAD_MODEL` / `WORKER_MODEL`, default `gpt-5.1` / `gpt-5.1-mini`)
  and `evals/judge.py` (`JUDGE_MODEL`) all call the OpenAI Agents SDK.
- The catalog MCP server has no external dependency — `catalog_server.py`
  is spawned as a stdio subprocess by `shopping/tools.py` and needs no
  keys. Run it standalone with `python catalog_server.py` if you want
  to drive it directly with an MCP client.
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` are
  optional tracing config for the `docker-compose.yml` stack.

```bash
uv run uvicorn shopping.app:app --host 0.0.0.0 --port 8000
```

### The payment-authorization gate

The design implements the payment stop as an **absence of capability**,
not a prompt instruction: `catalog_server.confirm_order` (the only tool
that can charge a pending order) is never wrapped with `@function_tool`
in `shopping/tools.py`, so no agent in the chain — Concierge, Product
Search, Comparator, or the Cart & Checkout Gate — is ever wired with a
spend/confirm tool. `POST /confirm` in `shopping/app.py` is a plain
FastAPI route that calls the MCP tool directly; no agent can reach it.
`tests/test_gate.py` asserts this absence directly (tool-set inspection
on every agent, plus a check that `confirm_order` is never a
`FunctionTool`), rather than trusting the system prompt.

## Files

- `.env.example`
- `Dockerfile`
- `catalog_server.py`
- `docker-compose.yml`
- `pyproject.toml` / `.python-version` / `uv.lock`
- `evals/dataset.jsonl`
- `evals/judge.py`
- `evals/run_evals.py`
- `requirements.txt`
- `shopping/agents.py`
- `shopping/app.py`
- `shopping/guardrails.py`
- `shopping/tools.py`
- `tests/test_gate.py` — payment-authorization gate: no agent has a
  spend/confirm tool, `confirm_order` is never a `FunctionTool`
- `tests/test_guardrails.py` — spend-cap and no-claim guardrail logic
- `tests/test_catalog_constraints.py` — constraint satisfaction
  (budget respected), server-computed pricing, idempotent confirmation
- `tests/test_agents_structure.py` — comparison-faithfulness structure
  (the Comparator's only tool is `get_product`) and handoff wiring
- `tests/test_live_smoke.py` — end-to-end smoke test against the real
  Agents SDK `Runner`, skipped unless `OPENAI_API_KEY` is set

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
