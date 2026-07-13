# Project 14 — Ambient Clinical Documentation Assistant

**Tier:** Intermediate  ·  **Frameworks:** Pydantic AI

Transcript→SOAP note with provenance and mandatory clinician sign-off. Research only.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 14** of _Building AI Agents_. This folder is the complete code.

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
- `scribe/app.py`
- `scribe/coding.py`
- `scribe/extract.py`
- `scribe/models.py`
- `scribe/observability.py`
- `scribe/prompts.py`
- `scribe/verify.py`
- `tests/test_verify.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
