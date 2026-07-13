# voice/session.py
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum


class Turn(Enum):
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"


@dataclass
class Session:
    """Per-call turn state and barge-in control."""
    thread_id: str = field(
        default_factory=lambda: str(uuid.uuid4()))
    state: Turn = Turn.LISTENING
    history: list[dict] = field(default_factory=list)
    generation: int = 0
    turn_started: float = 0.0

    def start_turn(self, kind: Turn) -> int:
        """Advance to a new state; bump generation."""
        self.state = kind
        self.generation += 1
        self.turn_started = time.monotonic()
        return self.generation

    def barge_in(self) -> int:
        """Caller spoke over the agent. Cancel + reset."""
        self.state = Turn.LISTENING
        self.generation += 1
        return self.generation

    def is_current(self, generation: int) -> bool:
        """True if `generation` is still the live turn."""
        return generation == self.generation

    def elapsed_ms(self) -> float:
        return (time.monotonic() - self.turn_started) * 1000
