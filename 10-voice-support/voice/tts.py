# voice/tts.py
from __future__ import annotations

import os
from collections.abc import Iterator

import httpx

TTS_API_KEY = os.environ["TTS_API_KEY"]
TTS_VOICE = os.getenv("TTS_VOICE", "aria")
TTS_URL = (
    "https://api.elevenlabs.io/v1/text-to-speech/"
    f"{TTS_VOICE}/stream")


def synthesize(text: str) -> Iterator[bytes]:
    """Stream PCM16 audio chunks for one sentence."""
    headers = {
        "xi-api-key": TTS_API_KEY,
        "accept": "audio/pcm",
    }
    payload = {
        "text": text,
        "model_id": "eleven_flash_v2_5",
        "output_format": "pcm_16000",
    }
    with httpx.stream(
        "POST", TTS_URL, headers=headers,
        json=payload, timeout=10.0,
    ) as resp:
        resp.raise_for_status()
        for chunk in resp.iter_bytes(chunk_size=1024):
            if chunk:
                yield chunk
