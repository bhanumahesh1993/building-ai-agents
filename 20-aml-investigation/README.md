# Project 20 — Financial-Crime & AML Investigation

**Tier:** Advanced  ·  **Frameworks:** OpenAI Agents SDK

Monitor, investigate, score, and draft a SAR — a human files it. Decision support only.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 20** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys (see below)
uv run --no-project pytest -q
```

All modules import with **no environment variables set** — the OpenAI
Agents SDK `Agent`s (investigator, SAR drafter) are built lazily behind
`get_*()` helpers in `aml/investigate.py` and `aml/sar_draft.py`, and the
embedding client `aml/kyc.py` uses for entity resolution is likewise
built lazily behind `_get_client()`. `aml/app.py` reads `DATABASE_URL`
lazily inside `_get_db_url()`, never at import time.

Running the service for real (not just the offline test suite)
additionally requires:

- `OPENAI_API_KEY` — the investigator and SAR-drafter agents
  (`INVESTIGATE_MODEL` / `DRAFT_MODEL`, default `gpt-5.1`) and
  `aml/kyc.py`'s embedding client (`EMBED_MODEL`) all call the OpenAI
  API.
- `DATABASE_URL` — a Postgres instance with `pgvector` for KYC entity
  resolution (`aml/kyc.py`); see `docker-compose.yml`.
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` / `LANGFUSE_HOST` are
  optional tracing config for the `docker-compose.yml` stack.

```bash
uv run uvicorn aml.app:app --host 0.0.0.0 --port 8000
```

**This system is decision support, not compliance or legal advice.**
It monitors, investigates, scores, and drafts a SAR narrative — it never
files one. A human compliance officer reads the draft and makes that
call; nothing in this codebase can act in their place.

### The never-auto-file-a-SAR gate

The design implements the filing stop as an **absence of capability**,
not a prompt instruction, exactly like the payment gate in Project 15:
there is no `CaseStatus.FILED` value anywhere in `aml/state.py`, no
function anywhere in the `aml` package files or submits a SAR, and
`POST /cases/{id}/review` — the only exit from `PENDING_REVIEW` — is a
plain FastAPI route that a human calls, never an agent tool and never
something an agent can reach. `tests/test_no_sar_filing_guard.py`
asserts that absence directly (enum inspection, an AST scan of the
whole package, tool-set inspection on every agent, plus the
`no_filing_claim_guardrail`'s regex), rather than trusting a prompt.

## Files

- `.env.example`
- `Dockerfile`
- `pyproject.toml` / `.python-version` / `uv.lock`
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
- `requirements.txt`
- `tests/test_no_sar_filing_guard.py` — the never-auto-file-a-SAR gate:
  no `FILED` state, no filing/submission function or tool anywhere in
  the package, `/review` is a plain human-only route
- `tests/test_guardrails.py` — memo sanitization, case-intake size
  cap, explainability (every claim cites transaction ids), PII redaction
- `tests/test_typology_matching.py` — structuring/layering/anomaly
  detection and typology-to-evidence mapping (every risk score traces
  back to real transaction ids)
- `tests/test_live_smoke.py` — end-to-end smoke tests against the real
  Agents SDK `Runner`, skipped unless `OPENAI_API_KEY` is set

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
