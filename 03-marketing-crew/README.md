# Project 03 — Marketing Content Pipeline Crew

**Tier:** Starter  ·  **Frameworks:** CrewAI · Langfuse

A five-role crew that turns one brief into a full campaign kit.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 03** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `.env.example`
- `Dockerfile`
- `crew/agents.py`
- `crew/app.py`
- `crew/crew.py`
- `crew/models.py`
- `crew/tasks.py`
- `crew/tools.py`
- `evals/judge.py`
- `evals/run_evals.py`
- `requirements.txt`
- `tests/test_context_chain.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
