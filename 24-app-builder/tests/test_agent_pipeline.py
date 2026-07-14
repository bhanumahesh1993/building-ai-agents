# tests/test_agent_pipeline.py
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from builder.agent import run_build
from builder.planner import BuildPlan, Contract, ComponentTask
from builder.spec import AcceptanceCriterion, AppSpec
from builder.verify import VerifyResult


def _spec(max_iterations: int = 2) -> AppSpec:
    return AppSpec(
        name="classpoll", goal="in-class polling app",
        max_iterations=max_iterations,
        acceptance_criteria=[AcceptanceCriterion(
            id="AC-1", pattern="ubiquitous",
            response="persist the primary entity")])


def _plan() -> BuildPlan:
    return BuildPlan(
        contract=Contract(
            entities={"Poll": {"id": "int"}},
            endpoints=[{
                "method": "POST", "path": "/polls",
                "summary": "create"}]),
        tasks=[
            ComponentTask(component=c, instructions="do it")
            for c in ("schema", "api", "frontend", "tests")
        ])


def _verify(passing: bool) -> VerifyResult:
    v = VerifyResult()
    v.passed = {"AC-1": passing}
    if not passing:
        v.details["AC-1"] = "unexpected response"
    return v


def _patched(**overrides):
    defaults = dict(
        make_plan=AsyncMock(return_value=_plan()),
        scaffold_project=MagicMock(),
        build_all_components=AsyncMock(return_value=[
            "schema", "api", "frontend", "tests"]),
        integrate_project=MagicMock(),
        start_sandbox_app=MagicMock(return_value="http://fake"),
        check_classpoll=AsyncMock(),
        retry_component=AsyncMock(),
    )
    defaults.update(overrides)
    return defaults


def test_pipeline_runs_plan_scaffold_build_before_the_verify_loop():
    """plan -> scaffold -> build must happen exactly once,
    before verify/retry ever run."""
    mocks = _patched(
        check_classpoll=AsyncMock(return_value=_verify(True)))
    with patch.multiple("builder.agent", **mocks):
        result = asyncio.run(run_build(_spec()))

    mocks["make_plan"].assert_awaited_once()
    mocks["scaffold_project"].assert_called_once()
    mocks["build_all_components"].assert_awaited_once()
    assert result.ready is True
    assert result.iterations == 0
    mocks["retry_component"].assert_not_called()


def test_pipeline_stops_at_the_iteration_cap_when_unfixable():
    """Never deploy without passing tests: if verify never
    passes, the loop must stop at max_iterations rather than
    spin forever, and the result must honestly report failure."""
    mocks = _patched(
        check_classpoll=AsyncMock(return_value=_verify(False)))
    with patch.multiple("builder.agent", **mocks):
        result = asyncio.run(run_build(_spec(max_iterations=2)))

    assert result.ready is False
    assert result.iterations == 2
    assert mocks["check_classpoll"].await_count == 3  # 0, 1, 2
    # Retried after iterations 0 and 1, not after the final one.
    assert mocks["retry_component"].await_count == 2


def test_pipeline_stops_early_once_verify_passes():
    """A fixable failure must not burn through every iteration:
    the loop stops the moment all criteria pass."""
    results = [_verify(False), _verify(True)]
    mocks = _patched(
        check_classpoll=AsyncMock(side_effect=results))
    with patch.multiple("builder.agent", **mocks):
        result = asyncio.run(run_build(_spec(max_iterations=2)))

    assert result.ready is True
    assert result.iterations == 1
    mocks["retry_component"].assert_awaited_once()
    args, _ = mocks["retry_component"].await_args
    # (root, plan, component, feedback) -- component must map
    # from the failing criterion via CRITERION_OWNER.
    assert args[2] == "schema"
    assert "AC-1" in args[3]


def test_integrate_and_sandbox_run_once_per_iteration():
    mocks = _patched(
        check_classpoll=AsyncMock(side_effect=[
            _verify(False), _verify(False), _verify(True)]))
    with patch.multiple("builder.agent", **mocks):
        asyncio.run(run_build(_spec(max_iterations=5)))

    assert mocks["integrate_project"].call_count == 3
    assert mocks["start_sandbox_app"].call_count == 3
