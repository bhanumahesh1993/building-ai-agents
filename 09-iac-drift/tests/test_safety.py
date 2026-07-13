# tests/test_safety.py
from __future__ import annotations

import pytest

from crew.tools import _run_terraform


def test_plan_is_allowed():
    # "plan" is on the allow-list, so the guard must
    # not raise before subprocess is even attempted -
    # we only assert it gets past the ValueError gate.
    with pytest.raises(FileNotFoundError):
        # No real terraform binary / cwd in the test
        # environment - the point is *which* error
        # surfaces. A ValueError here would mean the
        # allow-list rejected "plan"; it must not.
        _run_terraform(["plan"], cwd="/nonexistent-dir")


@pytest.mark.parametrize("verb", ["apply", "destroy"])
def test_apply_and_destroy_are_never_allowed(verb):
    # The structural safety gate: no code path in this
    # project may ever run terraform apply or destroy,
    # no matter what an agent asks for.
    with pytest.raises(ValueError, match=verb):
        _run_terraform([verb], cwd=".")


def test_unknown_subcommand_is_rejected():
    with pytest.raises(ValueError):
        _run_terraform(["taint"], cwd=".")
