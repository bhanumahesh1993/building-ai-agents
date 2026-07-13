# lit_review/workflow.py
from __future__ import annotations

import json

from google.adk.agents import ParallelAgent
from google.adk.runners import InMemoryRunner
from google.genai import types

from . import agents
from .corpus import get_known_ids
from .tools import check_hedging, search_corpus
from .tools import validate_citations

APP_NAME = "lit-review"


async def _run_agent(agent, message: str) -> dict:
    """Run one ADK agent to completion; return its state."""
    runner = InMemoryRunner(agent=agent, app_name=APP_NAME)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id="reviewer")
    turn = types.Content(
        role="user", parts=[types.Part(text=message)])
    async for _ in runner.run_async(
        user_id="reviewer", session_id=session.id,
        new_message=turn,
    ):
        pass
    final = await runner.session_service.get_session(
        app_name=APP_NAME, user_id="reviewer",
        session_id=session.id)
    return final.state


async def run_review(topic: str) -> dict:
    """The five-role pipeline, start to finish."""
    known_ids = get_known_ids()

    # 1. Retrieval — dynamic query planning, then a
    #    plain deterministic fetch. Not every model
    #    decision needs to happen inside a tool call.
    state = await _run_agent(agents.make_query_agent(), topic)
    queries = json.loads(state["queries"])["queries"]
    papers = search_corpus(queries, k=10)

    # 2. Summarize — one worker per cluster, in parallel.
    clusters: dict[int, list[dict]] = {}
    for p in papers:
        clusters.setdefault(p["cluster_id"], []).append(p)
    fanout = ParallelAgent(
        name="summarize_fanout",
        sub_agents=[
            agents.make_summarizer(cid, ps)
            for cid, ps in clusters.items()
        ],
    )
    state = await _run_agent(fanout, "summarize your cluster")
    summaries = {
        k: v for k, v in state.items()
        if k.startswith("summary_")
    }

    # 3. Scout for contradictions, then debate the real ones.
    scout = agents.make_contradiction_agent()
    state = await _run_agent(scout, "\n".join(summaries.values()))
    contradictions = json.loads(
        state["contradictions"])["contradictions"]

    debate_loop = agents.make_debate_loop()
    verdicts = []
    for c in contradictions:
        message = (
            f"Question: {c['question']}\n"
            f"Paper A ({c['paper_a']}): {c['claim_a']}\n"
            f"Paper B ({c['paper_b']}): {c['claim_b']}")
        dstate = await _run_agent(debate_loop, message)
        verdict = json.loads(dstate["verdict"])
        verdict["dispute"] = c
        verdicts.append(verdict)

    # 4 & 5. Gaps, then hypotheses — one fixed tail.
    tail = agents.make_tail()
    tail_msg = json.dumps({
        "summaries": summaries, "verdicts": verdicts,
        "allow_list": sorted(known_ids),
    })
    tstate = await _run_agent(tail, tail_msg)
    gaps = json.loads(tstate["gaps"])["gaps"]
    raw_hypotheses = tstate["hypotheses"]

    # Guardrails run in code, after the model, always.
    citation_check = validate_citations(
        raw_hypotheses, known_ids)
    hedge_check = check_hedging(raw_hypotheses)

    return {
        "topic": topic,
        "summaries": summaries,
        "contradictions": verdicts,
        "gaps": gaps,
        "hypotheses": json.loads(raw_hypotheses)["hypotheses"],
        "citation_guard": citation_check,
        "hedge_guard": hedge_check,
    }
