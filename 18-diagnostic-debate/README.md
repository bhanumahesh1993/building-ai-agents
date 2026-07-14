# Project 18 — Clinical Diagnostic Debate Panel

**Tier:** Advanced  ·  **Frameworks:** LangGraph

Chain-of-debate differential reasoning with bias checks. Research reproduction only.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 18** of _Building AI Agents_. This folder is the complete code.

> **This is a research reproduction, not a clinical or diagnostic tool.**
> It explores the chain-of-debate + independent bias-check pattern popularized
> by research systems like Microsoft's MAI-DxO ("MAI Diagnostic Orchestrator").
> Any MAI-DxO accuracy/cost figures referenced in the book chapter are
> **research-reported by that paper**, not numbers this toy codebase
> reproduces or validates — this project is for studying the *architecture*,
> not for benchmarking against it. There is no clinical-action path anywhere
> in this graph: it never prescribes, never recommends treatment, and every
> run ends at a structural human-review gate (`clinician_review`), never at
> an automated decision. Use only synthetic vignettes. **Never point this at
> a real patient or real EHR data.**

## Run it

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys (see below)
uv run --no-project pytest -q
```

All modules import with **no environment variables set** — every
`ChatAnthropic` client (intake, analyze, order-tests, advocate, moderate,
bias-check, cost-steward, and the eval judge) is built lazily behind a
`_get_llm()` helper on first use, not at import time. The offline test
suite exercises this directly: it fakes each `_get_llm()` and never
touches the network.

Running the service for real (not just the offline test suite)
additionally requires:

- `ANTHROPIC_API_KEY` — every reasoning node in the panel (intake through
  the cost steward) calls Claude.
- `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` — optional; without them
  `langfuse.langchain.CallbackHandler()` logs an authentication warning
  and disables itself rather than failing import or the run.

```bash
uvicorn panel.app:app --host 0.0.0.0 --port 8000
```

`tests/test_live.py` exercises the real model end to end (intake,
analyze, and a full graph run that pauses at `clinician_review`); it is
marked `@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), ...)`
so it stays skipped until a key is present.

## Files

- `.env.example`
- `.python-version`
- `Dockerfile`
- `pyproject.toml` / `uv.lock`
- `evals/__init__.py`
- `evals/judge.py`
- `evals/run_evals.py`
- `panel/__init__.py`
- `panel/app.py`
- `panel/graph.py`
- `panel/nodes/__init__.py`
- `panel/nodes/analyze.py`
- `panel/nodes/bias_check.py`
- `panel/nodes/debate.py`
- `panel/nodes/intake.py`
- `panel/nodes/order_tests.py`
- `panel/nodes/steward.py`
- `panel/prompts.py`
- `panel/state.py`
- `requirements.txt`
- `tests/__init__.py`
- `tests/test_debate.py` — debate argue/critique loop caps (confidence-gap
  stop, max-rounds cap, single bounded bias recheck)
- `tests/test_guardrails.py` — the research-only guard: no clinical-action
  vocabulary in any node, only `clinician_review` can reach `END`, only it
  ever calls `interrupt()`, and its payload always carries the
  not-a-diagnosis / not-a-treatment-plan notice
- `tests/test_bias_check.py` — bias-auditor recheck logic (fires once on
  anchoring against the leader, never twice, no-op on a clean read)
- `tests/test_steward.py` — cost-steward logic (top-3 active differential
  by confidence, retired hypotheses excluded, never orders tests or edits
  confidence itself)
- `tests/test_live.py` — opt-in live-model checks, skipped without a real
  `ANTHROPIC_API_KEY`

## Dependency notes

`requirements.txt`'s illustrative `==` pins all resolved cleanly as
`pyproject.toml` ranges (`>=<pin>,<NEXTMAJOR>`) with `uv pip install
-e ".[dev]"` and `uv lock` — no fictional or unpublishable version was
found. `langchain` was added explicitly as a direct dependency (beyond
`langchain-core` / `langchain-anthropic`) because `panel/app.py` imports
`langfuse.langchain.CallbackHandler`, which lives in the `langchain`
package.

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
