# tests/test_agent_card.py -- Agent Card structure.
#
# The Agent Card is the public contract a peer org's agent uses
# to decide whether (and how) to delegate work across the trust
# boundary. inventory_agent.AGENT_CARD is validated against the
# real a2a-sdk AgentCard schema -- not a hand-rolled shape check
# -- and procurement_agent's auto-generated card is checked the
# same way by actually hitting the served endpoint.
from __future__ import annotations

import importlib.util

import pytest

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("a2a") is None
    or importlib.util.find_spec("google.adk") is None,
    reason="a2a-sdk / google-adk not installed",
)

from a2a.types import AgentCard  # noqa: E402
from pydantic import ValidationError  # noqa: E402

from inventory_agent.agent import AGENT_CARD  # noqa: E402


def test_inventory_agent_card_validates_against_a2a_schema():
    card = AgentCard(**AGENT_CARD)
    assert card.name == "Inventory Agent"
    assert card.protocol_version == "1.0"
    assert card.default_input_modes == ["text"]
    assert card.default_output_modes == ["text"]


def test_inventory_agent_card_advertises_its_skill():
    card = AgentCard(**AGENT_CARD)
    skill_ids = {s.id for s in card.skills}
    assert "report_stock_status" in skill_ids


@pytest.mark.parametrize("required_field", [
    "name", "description", "url", "version",
    "capabilities", "skills",
])
def test_agent_card_rejects_missing_required_field(
        required_field):
    poisoned = dict(AGENT_CARD)
    del poisoned[required_field]
    with pytest.raises(ValidationError):
        AgentCard(**poisoned)


def test_procurement_agent_serves_a_valid_agent_card():
    """procurement_agent doesn't pass an explicit AGENT_CARD --
    to_a2a() auto-builds one from the ADK workflow. Confirm the
    live endpoint actually serves something that parses as a
    real AgentCard, keylessly (no model call is involved in
    serving this route)."""
    from starlette.testclient import TestClient

    import procurement_agent.agent as procurement_agent_mod

    with TestClient(procurement_agent_mod.app) as client:
        resp = client.get("/.well-known/agent-card.json")

    assert resp.status_code == 200
    card = AgentCard(**resp.json())
    assert card.name  # non-empty
    assert card.url.startswith("http://localhost:8001")
