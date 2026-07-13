# Project 03 — Marketing Content Pipeline Crew

**Tier:** Starter  ·  **Frameworks:** CrewAI · Langfuse

A five-role crew that turns one brief into a full campaign kit.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 03** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

The package imports without any API keys set — `crew/agents.py` and
`evals/judge.py` build CrewAI `LLM`/`Agent` objects from `os.getenv(...)`
with defaults, so construction never requires a key; a key is only needed
once you actually `kickoff()` a crew or call the judge. `crewai[anthropic]`
is pinned in `pyproject.toml` so the native Anthropic provider import
succeeds even without `ANTHROPIC_API_KEY` set.

Run the deterministic test suite offline (no API keys, no network):

```bash
uv run --no-project pytest -q
```

`tests/test_context_chain.py` only inspects `Task.context` wiring and makes
no LLM calls, so it runs green with no keys present.

## Files

- `.env.example`
- `Dockerfile`
- `crew/__init__.py`
- `crew/agents.py`
- `crew/app.py`
- `crew/crew.py`
- `crew/models.py`
- `crew/tasks.py`
- `crew/tools.py`
- `evals/judge.py`
- `evals/run_evals.py`
- `pyproject.toml`
- `.python-version`
- `uv.lock`
- `requirements.txt`
- `tests/__init__.py`
- `tests/test_context_chain.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
