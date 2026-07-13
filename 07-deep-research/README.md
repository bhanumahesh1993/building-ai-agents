# Project 07 — Deep Research Report Generator

**Tier:** Intermediate  ·  **Frameworks:** LangGraph · Langfuse

Orchestrator + parallel research subagents + a separate citation pass.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 07** of _Building AI Agents_. This folder is the complete code.

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
- `evals/judge.py`
- `evals/run_evals.py`
- `requirements.txt`
- `research/app.py`
- `research/graph.py`
- `research/nodes/citations.py`
- `research/nodes/planner.py`
- `research/nodes/researcher.py`
- `research/nodes/synthesizer.py`
- `research/prompts.py`
- `research/state.py`
- `research/tools.py`
- `tests/test_graph.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
