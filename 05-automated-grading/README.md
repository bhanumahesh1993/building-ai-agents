# Project 05 — Automated Grading & Feedback

**Tier:** Starter  ·  **Frameworks:** LangGraph

Rubric scoring with an evaluator-optimizer pass and mandatory human sign-off.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 05** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `.env.example`
- `Dockerfile`
- `docker-compose.yml`
- `evals/calibrate.py`
- `evals/fairness.py`
- `grading/app.py`
- `grading/graph.py`
- `grading/nodes/feedback.py`
- `grading/nodes/review_gate.py`
- `grading/nodes/score.py`
- `grading/nodes/similarity.py`
- `grading/rubric.py`
- `grading/state.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
