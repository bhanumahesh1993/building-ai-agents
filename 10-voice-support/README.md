# Project 10 — Voice-Enabled Support Agent

**Tier:** Intermediate  ·  **Frameworks:** Whisper · FastAPI WS

Cascaded STT→agent→TTS with turn management and a latency budget.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 10** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv sync
cp .env.example .env    # add your keys
# entry point varies by project — see the book chapter's "Deployment" section
```

## Files

- `Dockerfile`
- `evals/calls.jsonl`
- `evals/run_evals.py`
- `voice/agent.py`
- `voice/app.py`
- `voice/session.py`
- `voice/stt.py`
- `voice/tools.py`
- `voice/tts.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
