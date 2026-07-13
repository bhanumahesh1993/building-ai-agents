# tests/test_live_integrations.py
"""Tests that need a live model download, a live API key, or a real
audio device. These are skipped by default and only run when the
relevant environment variable / opt-in flag is present, so the
offline suite (`uv run --no-project pytest -q`) never needs network
access, an API key, or heavy audio dependencies installed."""
from __future__ import annotations

import os

import numpy as np
import pytest


@pytest.mark.skipif(
    os.getenv("RUN_AUDIO_MODEL_TESTS") != "1",
    reason=(
        "downloads faster-whisper model weights on first use; "
        "set RUN_AUDIO_MODEL_TESTS=1 to run"
    ),
)
def test_transcribe_runs_the_real_whisper_model():
    from voice.stt import transcribe

    silence = np.zeros(16_000, dtype=np.int16).tobytes()
    text, elapsed_ms = transcribe(silence)
    assert isinstance(text, str)
    assert elapsed_ms >= 0


@pytest.mark.skipif(
    os.getenv("RUN_VAD_DEVICE_TESTS") != "1",
    reason=(
        "requires the webrtcvad native extension; "
        "set RUN_VAD_DEVICE_TESTS=1 to run"
    ),
)
def test_voice_detected_runs_the_real_vad():
    from voice.stt import FRAME_MS, SAMPLE_RATE, voice_detected

    frame_len = int(SAMPLE_RATE * FRAME_MS / 1000) * 2  # 16-bit PCM
    silence = b"\x00" * frame_len
    assert voice_detected(silence) in (True, False)


@pytest.mark.skipif(
    not os.getenv("TTS_API_KEY"),
    reason="requires a live TTS_API_KEY and network access",
)
def test_synthesize_streams_real_audio():
    from voice.tts import synthesize

    chunks = list(synthesize("hello there"))
    assert chunks and all(isinstance(c, bytes) for c in chunks)


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="requires a live ANTHROPIC_API_KEY",
)
def test_run_turn_against_the_real_model():
    from voice.agent import run_turn

    sentences = []
    text, _ = run_turn(
        [{"role": "user", "content": "what is your return policy?"}],
        on_sentence=sentences.append,
    )
    assert text
