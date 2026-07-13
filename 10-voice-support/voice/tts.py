# voice/tts.py
from __future__ import annotations

import os
from collections.abc import Iterator

import httpx


def _get_config() -> tuple[str, str]:
    """Lazily read the API key and build the URL so the
    module imports without a key present (tests, offline use)."""
    api_key = os.environ["TTS_API_KEY"]
    voice = os.getenv("TTS_VOICE", "aria")
    url = (
        "https://api.elevenlabs.io/v1/text-to-speech/"
        f"{voice}/stream")
    return api_key, url


def synthesize(text: str) -> Iterator[bytes]:
    """Stream PCM16 audio chunks for one sentence."""
    api_key, tts_url = _get_config()
    headers = {
        "xi-api-key": api_key,
        "accept": "audio/pcm",
    }
    payload = {
        "text": text,
        "model_id": "eleven_flash_v2_5",
        "output_format": "pcm_16000",
    }
    with httpx.stream(
        "POST", tts_url, headers=headers,
        json=payload, timeout=10.0,
    ) as resp:
        resp.raise_for_status()
        for chunk in resp.iter_bytes(chunk_size=1024):
            if chunk:
                yield chunk
