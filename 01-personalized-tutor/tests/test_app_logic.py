# tests/test_app_logic.py
from __future__ import annotations

import pytest

from tutor.app import LADDER, _shift_difficulty


@pytest.mark.parametrize("current,direction,expected", [
    ("easy", "harder", "medium"),
    ("medium", "harder", "hard"),
    ("hard", "harder", "hard"),   # already at the ceiling
    ("hard", "easier", "medium"),
    ("medium", "easier", "easy"),
    ("easy", "easier", "easy"),   # already at the floor
    ("medium", "same", "medium"),
])
def test_shift_difficulty(current, direction, expected):
    assert _shift_difficulty(current, direction) == expected


def test_ladder_order():
    assert LADDER == ["easy", "medium", "hard"]
