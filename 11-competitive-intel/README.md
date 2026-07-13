# Project 11 — Competitive-Intelligence Monitor

**Tier:** Intermediate  ·  **Frameworks:** LangGraph · pgvector

Parallel fetch, semantic change detection, significance scoring, scheduled digests.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 11** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `.env.example`
- `Dockerfile`
- `evals/run_evals.py`
- `monitor/app.py`
- `monitor/fetch_tool.py`
- `monitor/graph.py`
- `monitor/nodes/computer_use_fallback.py`
- `monitor/nodes/diff.py`
- `monitor/nodes/digest.py`
- `monitor/nodes/fetch.py`
- `monitor/nodes/score.py`
- `monitor/prompts.py`
- `monitor/registry.py`
- `monitor/schedule.py`
- `monitor/state.py`
- `requirements.txt`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
