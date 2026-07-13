# Project 08 — Multi-Agent Code Review & Security Audit

**Tier:** Intermediate  ·  **Frameworks:** LangGraph

Parallel specialist reviewers, adversarially verified, gating a PR.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 08** of _Building AI Agents_. This folder is the complete code.

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
- `evals/run_evals.py`
- `requirements.txt`
- `review/app.py`
- `review/diff_utils.py`
- `review/github_stub.py`
- `review/graph.py`
- `review/nodes/consolidate.py`
- `review/nodes/gate.py`
- `review/nodes/gather.py`
- `review/nodes/reviewers.py`
- `review/nodes/verify.py`
- `review/prompts.py`
- `review/state.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
