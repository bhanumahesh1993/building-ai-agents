# voice/stt.py
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np

SAMPLE_RATE = 16_000
FRAME_MS = 30
SILENCE_MS_END_TURN = 400

_model: Any | None = None
_vad: Any | None = None


def _get_model() -> Any:
    """Lazily load the Whisper model so the module imports
    without downloading model weights (tests, offline use)."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel(
            "distil-large-v3", device="auto",
            compute_type="int8")
    return _model


def _get_vad() -> Any:
    """Lazily build the VAD so the module imports without
    requiring the webrtcvad extension to be importable."""
    global _vad
    if _vad is None:
        import webrtcvad
        _vad = webrtcvad.Vad(2)  # 0-3, higher = stricter
    return _vad


def voice_detected(frame: bytes) -> bool:
    """Cheap VAD check, reused by the server for barge-in."""
    return _get_vad().is_speech(frame, SAMPLE_RATE)


@dataclass
class TurnBuffer:
    """Buffers PCM16 audio until the caller stops talking."""
    frames: list[bytes] = field(default_factory=list)
    silence_ms: int = 0
    speaking: bool = False

    def push(self, frame: bytes) -> bool:
        """Add one frame; return True if the turn ended."""
        if voice_detected(frame):
            self.speaking = True
            self.silence_ms = 0
            self.frames.append(frame)
            return False
        if self.speaking:
            self.frames.append(frame)
            self.silence_ms += FRAME_MS
            return self.silence_ms >= SILENCE_MS_END_TURN
        return False

    def reset(self) -> bytes:
        """Flush the buffered turn and clear state."""
        audio = b"".join(self.frames)
        self.frames.clear()
        self.speaking = False
        self.silence_ms = 0
        return audio


def transcribe(pcm16: bytes) -> tuple[str, float]:
    """Transcribe one finished turn. Returns (text, ms)."""
    start = time.monotonic()
    audio = np.frombuffer(pcm16, dtype=np.int16)
    audio = audio.astype(np.float32) / 32768.0
    segments, _ = _get_model().transcribe(
        audio, language="en", vad_filter=False,
        beam_size=1)
    text = " ".join(s.text.strip() for s in segments)
    elapsed_ms = (time.monotonic() - start) * 1000
    return text.strip(), elapsed_ms
