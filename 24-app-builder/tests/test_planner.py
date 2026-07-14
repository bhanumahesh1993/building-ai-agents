# tests/test_planner.py
from __future__ import annotations

import importlib.util
import json
import os

import pytest

from builder.planner import _parse_plan_response
from builder.spec import AcceptanceCriterion, AppSpec

HAS_SDK = importlib.util.find_spec("claude_agent_sdk") is not None
HAS_KEY = bool(os.environ.get("ANTHROPIC_API_KEY"))
requires_live_api = pytest.mark.skipif(
    not (HAS_SDK and HAS_KEY),
    reason="requires claude-agent-sdk installed and "
    "ANTHROPIC_API_KEY set for a live model call",
)

SAMPLE_RESPONSE = json.dumps({
    "contract": {
        "entities": {"Poll": {"id": "int", "question": "str"}},
        "endpoints": [
            {"method": "POST", "path": "/polls",
             "summary": "create a poll"},
            {"method": "GET", "path": "/polls/{id}",
             "summary": "read a poll"},
        ],
    },
    "tasks": [
        {"component": "schema", "instructions": "build the model"},
        {"component": "api", "instructions": "build the routes"},
        {"component": "frontend", "instructions": "build the UI"},
        {"component": "tests", "instructions": "build the tests"},
    ],
})


def test_parses_contract_and_one_task_per_component():
    plan = _parse_plan_response(SAMPLE_RESPONSE)
    assert set(plan.contract.entities) == {"Poll"}
    assert len(plan.contract.endpoints) == 2
    components = {t.component for t in plan.tasks}
    assert components == {"schema", "api", "frontend", "tests"}


def test_rejects_a_response_missing_the_contract():
    bad = json.loads(SAMPLE_RESPONSE)
    del bad["contract"]
    with pytest.raises(Exception):
        _parse_plan_response(json.dumps(bad))


def test_rejects_non_json_text():
    with pytest.raises(json.JSONDecodeError):
        _parse_plan_response("not json at all")


@requires_live_api
def test_make_plan_live():
    """End-to-end plan decomposition through the real Claude
    Agent SDK. Skipped unless claude-agent-sdk is installed
    and ANTHROPIC_API_KEY is set."""
    import anyio
    from builder.planner import make_plan

    spec = AppSpec(
        name="classpoll", goal="in-class polling app",
        acceptance_criteria=[AcceptanceCriterion(
            id="AC-1", pattern="ubiquitous",
            response="persist the primary entity")])
    plan = anyio.run(make_plan, spec)
    assert plan.contract.entities
    assert plan.tasks
