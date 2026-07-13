# Project 09 — IaC Generation & Drift-Detection Crew

**Tier:** Intermediate  ·  **Frameworks:** CrewAI · Terraform

Generates HCL, policy-checks it, estimates cost, detects drift — plan-only, never applies.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 09** of _Building AI Agents_. This folder is the complete code.

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
- `crew/policies.py`
- `crew/tasks.py`
- `crew/tools.py`
- `evals/run_evals.py`
- `main.tf`
- `requirements.txt`
- `tests/test_policies.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
