# Project 19 — Multi-Agent Trading Research Firm

**Tier:** Advanced  ·  **Frameworks:** LangGraph

Bull/bear debate + risk veto + manager decision. Paper-only, never places live trades.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 19** of _Building AI Agents_. This folder is the complete code.

## Run it

This is an **educational/research** system, not investment advice: it is
**paper-only** and never places a live order. There is no brokerage or
exchange client anywhere in `firm/` — the trader, risk, and manager nodes
produce a *simulated* `paper_fill` with `broker_order_id` hard-coded to
`None` in source, and the position-size cap is enforced by a `min()` clamp
in code (`firm/nodes/risk.py`), never merely requested in a prompt. A
proposal above `CONFIRM_ABOVE_PCT` still pauses at a structural
`langgraph` `interrupt()` for human confirmation before the simulated
blotter records it.

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

The package imports and its deterministic tests (bull/bear debate cap, risk
veto and revision loop, and the no-live-trading guards) run offline with no
environment variables set: `uv run --no-project pytest -q`.

For live use — real model calls for each analyst/debate/trader/risk/manager
node — you need an `ANTHROPIC_API_KEY` set in `.env`. Without it, every
node builds its `ChatAnthropic` client lazily behind a module-level
`_get_llm()` and will only raise the first time it actually tries to reach
the model, not at import time.

## Files

- `.env.example`
- `Dockerfile`
- `docker-compose.yml`
- `evals/backtest.py`
- `evals/judge.py`
- `evals/run_evals.py`
- `firm/app.py`
- `firm/data.py`
- `firm/graph.py`
- `firm/nodes/analysts.py`
- `firm/nodes/debate.py`
- `firm/nodes/manager.py`
- `firm/nodes/risk.py`
- `firm/nodes/trader.py`
- `firm/prompts.py`
- `firm/state.py`
- `requirements.txt`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
