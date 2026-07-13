# tests/test_context_chain.py
from __future__ import annotations

from crew.tasks import (
    strategy_task, copy_task, seo_task, editor_task,
)


def test_editor_sees_three_upstream_tasks():
    assert editor_task.context == [
        strategy_task, copy_task, seo_task]


def test_copy_only_sees_strategy():
    # If this list ever grows by accident, the
    # Copywriter starts seeing context it was never
    # designed to use - a silent scope creep bug.
    assert copy_task.context == [strategy_task]
