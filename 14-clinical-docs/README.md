# Project 14 — Ambient Clinical Documentation Assistant

**Tier:** Intermediate  ·  **Frameworks:** Pydantic AI

Transcript→SOAP note with provenance and mandatory clinician sign-off. Research only.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 14** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
uv run uvicorn scribe.app:app --reload --port 8000
```

Live use needs `ANTHROPIC_API_KEY` (the extract/verify/coding agents in
`scribe/` and the hallucination judge in `evals/judge.py` all call
`anthropic:claude-*` models via Pydantic AI). `LANGFUSE_PUBLIC_KEY` /
`LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` are optional — tracing self-disables
with a warning if unset.

Run the offline, deterministic test suite (no keys needed) with:

```bash
uv run pytest -q
```

This covers the mandatory clinician sign-off gate, the traceability
verifier, ICD-suggestion structure, and the hallucination-check contract.
A handful of `@pytest.mark.skipif`-gated tests in `tests/test_live_api.py`
exercise the real model calls end-to-end and only run when
`ANTHROPIC_API_KEY` is set.

## Files

- `.env.example`
- `Dockerfile`
- `evals/judge.py`
- `evals/run_evals.py`
- `pyproject.toml`
- `requirements.txt`
- `scribe/app.py`
- `scribe/coding.py`
- `scribe/extract.py`
- `scribe/models.py`
- `scribe/observability.py`
- `scribe/prompts.py`
- `scribe/verify.py`
- `tests/test_coding.py`
- `tests/test_hallucination.py`
- `tests/test_live_api.py`
- `tests/test_signoff.py`
- `tests/test_verify.py`

## Safety

**This project is research and educational only. It is NOT for clinical
use, is not a medical device, and must never be pointed at real patient
data or a real EHR.** Every draft note is explicitly labeled "DRAFT ONLY —
not a medical record" until a licensed clinician (MD/DO/NP/PA) signs off.

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it: `scribe/app.py`
only ever returns a note as final from `GET /visits/{id}` after
`POST /visits/{id}/signoff` has recorded a named clinician, a credential, and
an explicit attestation, and only once every traceability flag on that note
has been either edited out or explicitly listed as resolved.
