# Project 18 — Clinical Diagnostic Debate Panel

**Tier:** Advanced  ·  **Frameworks:** LangGraph

Chain-of-debate differential reasoning with bias checks. Research reproduction only.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 18** of _Building AI Agents_. This folder is the complete code.

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
- `panel/app.py`
- `panel/graph.py`
- `panel/nodes/analyze.py`
- `panel/nodes/bias_check.py`
- `panel/nodes/debate.py`
- `panel/nodes/intake.py`
- `panel/nodes/order_tests.py`
- `panel/nodes/steward.py`
- `panel/prompts.py`
- `panel/state.py`
- `requirements.txt`
- `tests/test_debate.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
