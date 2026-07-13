# Project 20 — Financial-Crime & AML Investigation

**Tier:** Advanced  ·  **Frameworks:** OpenAI Agents SDK

Monitor, investigate, score, and draft a SAR — a human files it. Decision support only.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 20** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `.env.example`
- `Dockerfile`
- `aml/app.py`
- `aml/guardrails.py`
- `aml/investigate.py`
- `aml/kyc.py`
- `aml/monitor.py`
- `aml/sar_draft.py`
- `aml/scoring.py`
- `aml/state.py`
- `docker-compose.yml`
- `evals/run_evals.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
