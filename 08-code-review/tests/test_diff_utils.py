# tests/test_diff_utils.py
from __future__ import annotations

from review.diff_utils import parse_diff, render_hunks

from .fixtures import (
    CLEAN_DIFF, SEEDED_BUG_DIFF, SEEDED_BUG_EVIDENCE, SEEDED_BUG_PATH,
)


def test_parse_diff_extracts_path_and_start_line():
    hunks = parse_diff(SEEDED_BUG_DIFF)
    assert len(hunks) == 1
    hunk = hunks[0]
    assert hunk["path"] == SEEDED_BUG_PATH
    assert hunk["start_line"] == 8
    assert SEEDED_BUG_EVIDENCE in hunk["patch"]


def test_render_hunks_includes_path_header_and_patch_text():
    hunks = parse_diff(SEEDED_BUG_DIFF)
    rendered = render_hunks(hunks)
    assert SEEDED_BUG_PATH in rendered
    assert SEEDED_BUG_EVIDENCE in rendered


def test_parse_diff_handles_multiple_hunks():
    combo = SEEDED_BUG_DIFF + CLEAN_DIFF
    hunks = parse_diff(combo)
    assert len(hunks) == 2
    assert {h["path"] for h in hunks} == {"app.py"}


def test_empty_diff_produces_no_hunks():
    assert parse_diff("") == []
