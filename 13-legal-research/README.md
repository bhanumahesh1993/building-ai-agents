# Project 13 — Legal Research Deep-Dive Agent

**Tier:** Intermediate  ·  **Frameworks:** Claude Agent SDK

Orchestrator + subagents + a separate citation-verification pass. Not legal advice.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 13** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `.env.example`
- `Dockerfile`
- `evals/run_evals.py`
- `requirements.txt`
- `research/app.py`
- `research/citations.py`
- `research/corpus.py`
- `research/issues.py`
- `research/memo.py`
- `research/orchestrator.py`
- `research/prompts.py`
- `research/retrieval_subagent.py`
- `research/synthesize.py`
- `tests/test_citations.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
