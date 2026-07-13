# Project 08 — Multi-Agent Code Review & Security Audit

**Tier:** Intermediate  ·  **Frameworks:** LangGraph

Parallel specialist reviewers, adversarially verified, gating a PR.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 08** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
uv run uvicorn review.app:app --reload
```

No API key or running service is needed to import the package or run its
deterministic test suite:

```bash
uv run --no-project pytest -q
```

`ANTHROPIC_API_KEY` is only required at call time (`review.nodes.reviewers`,
`review.nodes.verify`) — the `ChatAnthropic` clients are built lazily behind
`_get_llm()` on first use, so every module imports cleanly without it.
`LANGFUSE_*` keys are optional and only needed if you want tracing sent to
Langfuse; without them the callback handler self-disables with a warning.

## Files

- `.env.example`
- `.python-version`
- `Dockerfile`
- `docker-compose.yml`
- `evals/run_evals.py`
- `pyproject.toml`
- `requirements.txt`
- `review/__init__.py`
- `review/app.py`
- `review/diff_utils.py`
- `review/github_stub.py`
- `review/graph.py`
- `review/nodes/__init__.py`
- `review/nodes/consolidate.py`
- `review/nodes/gate.py`
- `review/nodes/gather.py`
- `review/nodes/reviewers.py`
- `review/nodes/verify.py`
- `review/prompts.py`
- `review/state.py`
- `tests/__init__.py`
- `tests/fixtures.py`
- `tests/test_consolidate.py`
- `tests/test_diff_utils.py`
- `tests/test_gate.py`
- `tests/test_graph_pipeline.py`
- `tests/test_live_smoke.py`
- `uv.lock`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
