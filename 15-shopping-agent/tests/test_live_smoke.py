# tests/test_live_smoke.py — end-to-end smoke test against the
# real OpenAI Agents SDK Runner. Skipped unless OPENAI_API_KEY
# is set, so the offline suite stays deterministic and free.
from __future__ import annotations

import asyncio
import os

import pytest
from agents import Runner

from shopping.agents import all_agents, get_concierge
from shopping.tools import CALLED_TOOLS


@pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="requires a live OPENAI_API_KEY to run the agent chain",
)
def test_live_run_never_calls_confirm_order():
    CALLED_TOOLS.clear()

    async def _run():
        result = await Runner.run(
            get_concierge(),
            "ANC headphones under $150 for flights",
        )
        return result.final_output

    proposal = asyncio.run(_run())
    assert proposal
    assert "confirm_order" not in CALLED_TOOLS
    for agent in all_agents():
        assert "confirm_order" not in {t.name for t in agent.tools}
