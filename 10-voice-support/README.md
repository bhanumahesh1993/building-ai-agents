# Project 10 — Voice-Enabled Support Agent

**Tier:** Intermediate  ·  **Frameworks:** Whisper · FastAPI WS

Cascaded STT→agent→TTS with turn management and a latency budget.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 10** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
uv run uvicorn voice.app:app --reload --port 8000
```

Live use needs `ANTHROPIC_API_KEY` (the turn agent in `voice/agent.py` calls
`claude-sonnet-4-5` by default; override with `AGENT_MODEL`) and `TTS_API_KEY`
(ElevenLabs; `TTS_VOICE` defaults to `aria`). All three external clients --
the Anthropic client, the ElevenLabs TTS client, and the faster-whisper STT
model -- are built lazily on first use behind `_get_*()` helpers, so every
`voice.*` module imports cleanly with no keys set and without downloading
any model weights.

Run the offline, deterministic test suite (no keys, no model download, no
audio device needed) with:

```bash
uv run pytest -q
```

That suite covers the turn/barge-in state machine (`voice/session.py`) and
the turn-timing / latency-budget math (silence-frame accounting in
`voice/stt.py`, `Session.elapsed_ms`) with mocked clocks and a mocked VAD --
no real audio ever needed. Tests that require a live model, a live API key,
or a real audio device (real Whisper transcription, real webrtcvad, real
TTS synthesis, a real Claude call) live in `tests/test_live_integrations.py`
and are skipped by default via `@pytest.mark.skipif`; opt in with
`RUN_AUDIO_MODEL_TESTS=1`, `RUN_VAD_DEVICE_TESTS=1`, `TTS_API_KEY=...`, or
`ANTHROPIC_API_KEY=...` respectively.

**Audio dependency note:** `faster-whisper` and `webrtcvad` installed
cleanly via `uv pip install -e ".[dev]"` on this machine (Apple Silicon
macOS, Python 3.12) -- `faster-whisper` pulls in `ctranslate2` (no torch
required) and `webrtcvad` builds its small C extension from source. If
either fails to build on your machine (missing C compiler, unsupported
platform wheel), the rest of the package -- `voice.agent`, `voice.app`,
`voice.session`, `voice.tools`, `voice.tts` -- still imports and the
deterministic test suite still passes, since `voice/stt.py` only imports
`faster_whisper`/`webrtcvad` lazily inside `_get_model()`/`_get_vad()`,
not at module import time.

## Files

- `.env.example`
- `Dockerfile`
- `evals/calls.jsonl`
- `evals/run_evals.py`
- `pyproject.toml`
- `requirements.txt`
- `tests/test_imports.py`
- `tests/test_latency_budget.py`
- `tests/test_live_integrations.py`
- `tests/test_session.py`
- `tests/test_tools.py`
- `voice/agent.py`
- `voice/app.py`
- `voice/session.py`
- `voice/stt.py`
- `voice/tools.py`
- `voice/tts.py`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
