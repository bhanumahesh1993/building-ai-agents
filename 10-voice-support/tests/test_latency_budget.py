# tests/test_latency_budget.py
"""Deterministic tests for the turn-timing math: how many silent
frames it takes to close a turn, and how elapsed time is measured.
Neither test touches the real VAD model or the wall clock, so they
run with no audio device, model weights, or API keys present."""
from __future__ import annotations

import math
import time as time_module

import pytest

import voice.stt as stt
from voice.session import Session, Turn


def _frames_to_close_turn(silence_ms: int, frame_ms: int) -> int:
    """Minimum number of trailing silent frames needed to close
    a turn, given the module's silence-detection budget."""
    return math.ceil(silence_ms / frame_ms)


def test_turn_closes_exactly_at_the_silence_budget(monkeypatch):
    """TurnBuffer must not close a turn before SILENCE_MS_END_TURN
    of trailing silence has elapsed, and must close it once it has."""
    speech_then_silence = iter(
        [True] + [False] * 100)  # one voiced frame, then silence
    monkeypatch.setattr(
        stt, "voice_detected",
        lambda frame: next(speech_then_silence))

    buf = stt.TurnBuffer()
    assert buf.push(b"\x00" * 2) is False  # the voiced frame

    needed = _frames_to_close_turn(
        stt.SILENCE_MS_END_TURN, stt.FRAME_MS)
    ended = False
    frames_pushed = 0
    for _ in range(needed + 5):  # generous upper bound
        ended = buf.push(b"\x00" * 2)
        frames_pushed += 1
        if ended:
            break

    assert ended, "turn never closed within the silence budget"
    assert frames_pushed == needed
    assert buf.silence_ms >= stt.SILENCE_MS_END_TURN


def test_turn_does_not_close_before_the_silence_budget(monkeypatch):
    silence_only = iter([True] + [False] * 3)  # short silence, no close
    monkeypatch.setattr(
        stt, "voice_detected", lambda frame: next(silence_only))

    buf = stt.TurnBuffer()
    buf.push(b"\x00" * 2)  # speak once
    ended = False
    for _ in range(3):
        ended = buf.push(b"\x00" * 2)
    assert not ended
    assert buf.silence_ms < stt.SILENCE_MS_END_TURN


def test_reset_clears_timing_state():
    buf = stt.TurnBuffer(
        frames=[b"a", b"b"], silence_ms=250, speaking=True)
    audio = buf.reset()
    assert audio == b"ab"
    assert buf.frames == []
    assert buf.silence_ms == 0
    assert buf.speaking is False


def test_session_elapsed_ms_uses_monotonic_clock(monkeypatch):
    """The latency budget the app reports (session.elapsed_ms) must
    reflect wall-clock time since the turn started, not turn count."""
    clock = iter([100.0, 100.35])  # turn start, then +350ms later
    monkeypatch.setattr(
        time_module, "monotonic", lambda: next(clock))

    session = Session()
    session.start_turn(Turn.THINKING)
    elapsed = session.elapsed_ms()

    assert elapsed == pytest.approx(350.0)


def test_barge_in_does_not_reset_the_latency_clock(monkeypatch):
    """barge_in() changes state/generation but intentionally does
    not touch turn_started -- elapsed_ms keeps measuring from the
    original turn start."""
    clock = iter([0.0, 0.2])
    monkeypatch.setattr(
        time_module, "monotonic", lambda: next(clock))

    session = Session()
    session.start_turn(Turn.SPEAKING)
    session.barge_in()
    assert session.elapsed_ms() == pytest.approx(200.0)
