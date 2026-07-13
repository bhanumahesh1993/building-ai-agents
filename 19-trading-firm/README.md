# Project 19 — Multi-Agent Trading Research Firm

**Tier:** Advanced  ·  **Frameworks:** LangGraph

Bull/bear debate + risk veto + manager decision. Paper-only, never places live trades.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 19** of _Building AI Agents_. This folder is the complete code.

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
