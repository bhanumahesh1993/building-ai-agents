# Project 17 — Threat-Intel Briefing & Vuln Prioritization

**Tier:** Advanced  ·  **Frameworks:** CrewAI

Risk-based CVE prioritization (severity × exploit × exposure) and exec briefings.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 17** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `.env.example`
- `Dockerfile`
- `crew/agents.py`
- `crew/app.py`
- `crew/crew.py`
- `crew/models.py`
- `crew/ranking.py`
- `crew/tasks.py`
- `crew/tools.py`
- `docker-compose.yml`
- `evals/dedup_check_eval.py`
- `evals/judge.py`
- `evals/ranking_check.py`
- `requirements.txt`
- `schema.sql`
- `tests/test_ranking.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
