# tests/test_session.py
from __future__ import annotations

from voice.session import Session, Turn


def test_new_session_starts_listening():
    session = Session()
    assert session.state == Turn.LISTENING
    assert session.generation == 0


def test_start_turn_advances_state_and_generation():
    session = Session()
    gen = session.start_turn(Turn.THINKING)
    assert session.state == Turn.THINKING
    assert gen == 1
    assert session.generation == 1


def test_start_turn_twice_keeps_bumping_generation():
    session = Session()
    first = session.start_turn(Turn.THINKING)
    second = session.start_turn(Turn.SPEAKING)
    assert second == first + 1
    assert session.state == Turn.SPEAKING


def test_barge_in_resets_to_listening_and_bumps_generation():
    session = Session()
    session.start_turn(Turn.SPEAKING)
    gen_before = session.generation
    new_gen = session.barge_in()
    assert session.state == Turn.LISTENING
    assert new_gen == gen_before + 1
    assert session.generation == new_gen


def test_is_current_only_true_for_latest_generation():
    session = Session()
    gen1 = session.start_turn(Turn.THINKING)
    assert session.is_current(gen1)

    gen2 = session.start_turn(Turn.SPEAKING)
    # The stale generation from the prior turn is no longer current.
    assert not session.is_current(gen1)
    assert session.is_current(gen2)


def test_barge_in_invalidates_in_flight_generation():
    """A stale TTS/agent task from before the barge-in must see
    is_current() go False so it stops writing audio."""
    session = Session()
    gen = session.start_turn(Turn.SPEAKING)
    assert session.is_current(gen)

    session.barge_in()
    assert not session.is_current(gen)
