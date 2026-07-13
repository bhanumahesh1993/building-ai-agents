# Project 24 — Full-Stack App Builder Agent

**Tier:** Advanced  ·  **Frameworks:** Claude Agent SDK

Spec→plan→parallel build→verify→deploy. The book's spec-driven method, executable.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 24** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `.env.example`
- `Dockerfile`
- `builder/agent.py`
- `builder/app.py`
- `builder/deploy.py`
- `builder/integrate.py`
- `builder/planner.py`
- `builder/scaffold.py`
- `builder/spec.py`
- `builder/telemetry.py`
- `builder/verify.py`
- `builder/workers.py`
- `docker-compose.yml`
- `evals/dataset.jsonl`
- `evals/judge.py`
- `evals/run_evals.py`
- `requirements.txt`
- `skills/scaffold-conventions/SKILL.md`
- `tests/test_gate.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
