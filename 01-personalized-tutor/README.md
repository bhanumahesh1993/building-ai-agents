# Project 01 — Personalized Tutor Agent

**Tier:** Starter  ·  **Frameworks:** Pydantic AI · Langfuse

A Socratic study coach that diagnoses level, plans a lesson, and adapts difficulty.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 01** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `.env.example`
- `Dockerfile`
- `evals/judge.py`
- `evals/run_evals.py`
- `requirements.txt`
- `tutor/agents.py`
- `tutor/app.py`
- `tutor/guardrails.py`
- `tutor/memory.py`
- `tutor/models.py`
- `tutor/observability.py`
- `tutor/prompts.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
