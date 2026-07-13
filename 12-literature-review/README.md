# Project 12 — Scientific Literature Review Agent

**Tier:** Intermediate  ·  **Frameworks:** Google ADK

Multi-agent review with contradiction detection and grounded hypothesis generation.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 12** of _Building AI Agents_. This folder is the complete code.

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
- `lit_review/agents.py`
- `lit_review/app.py`
- `lit_review/corpus.py`
- `lit_review/tools.py`
- `lit_review/workflow.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
