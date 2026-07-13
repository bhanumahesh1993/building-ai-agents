# Project 22 — Autonomous Coding & PR Agent

**Tier:** Advanced  ·  **Frameworks:** Claude Agent SDK · Docker

Issue→plan→implement in a sandbox→test→open a PR. Never merges autonomously.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 22** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `.env.example`
- `Dockerfile`
- `agent/agent.py`
- `agent/app.py`
- `agent/context.py`
- `agent/github_stub.py`
- `agent/implement.py`
- `agent/loop.py`
- `agent/plan.py`
- `agent/pr.py`
- `agent/prompts.py`
- `agent/sandbox.py`
- `agent/test_runner.py`
- `evals/judge.py`
- `requirements.txt`
- `tests/test_self_correct.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
