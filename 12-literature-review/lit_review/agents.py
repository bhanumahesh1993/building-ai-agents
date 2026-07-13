# lit_review/agents.py
from __future__ import annotations

import os

from google.adk.agents import (
    LlmAgent, LoopAgent, ParallelAgent, SequentialAgent,
)
from google.adk.tools import ToolContext

LEAD_MODEL = os.getenv("LEAD_MODEL", "gemini-2.5-pro")
WORKER_MODEL = os.getenv(
    "WORKER_MODEL", "gemini-2.5-flash")
MAX_DEBATE_ROUNDS = int(
    os.getenv("MAX_DEBATE_ROUNDS", "2"))

RETRIEVAL_INSTRUCTION = """You are a literature-search
assistant. The user's message is a research topic.
Expand it into 3-5 short, diverse search queries that
together cover its methods, applications, and known
critiques. Return ONLY JSON:
{"queries": ["q1", "q2", "..."]}."""


def make_query_agent() -> LlmAgent:
    """Dynamic step: the model decides where to look."""
    return LlmAgent(
        name="query_planner",
        model=WORKER_MODEL,
        instruction=RETRIEVAL_INSTRUCTION,
        output_key="queries",
    )


def make_summarizer(
    cluster_id: int, papers: list[dict],
) -> LlmAgent:
    """One reporter, one cluster, one context window."""
    body = "\n\n".join(
        f"[{p['id']}] {p['title']}\n{p['abstract']}"
        for p in papers
    )
    instruction = f"""You are a research summarizer for
one topic cluster. Read ONLY the abstracts below and
write a 120-180 word summary of what they collectively
find. Name papers by their bracketed ID when you
attribute a claim. Never state a finding that is not
in the text below.

Abstracts:
{body}"""
    return LlmAgent(
        name=f"summarizer_{cluster_id}",
        model=WORKER_MODEL,
        instruction=instruction,
        output_key=f"summary_{cluster_id}",
    )


CONTRADICTION_INSTRUCTION = """You are a contradiction
scout. The user's message contains cluster summaries
from a literature review. Find every pair of papers
that reach opposite conclusions on the same underlying
question. Return ONLY JSON: {"contradictions": [
{"paper_a": "id", "claim_a": "...", "paper_b": "id",
"claim_b": "...", "question": "..."}]}. If there are
none, return an empty list."""


def make_contradiction_agent() -> LlmAgent:
    return LlmAgent(
        name="contradiction_scout",
        model=LEAD_MODEL,
        instruction=CONTRADICTION_INSTRUCTION,
        output_key="contradictions",
    )

# lit_review/agents.py (continued)

PROPONENT_A_INSTRUCTION = """You argue FOR "Paper A" in
the dispute described in the user's message. Use only
Paper A's claim to make the strongest honest case for
it. If state['argument_b'] already exists, rebut it
directly. If Paper A's claim is genuinely the weaker
read of the evidence, say so plainly — do not bluff."""

PROPONENT_B_INSTRUCTION = """You argue FOR "Paper B" in
the dispute described in the user's message. Use only
Paper B's claim to make the strongest honest case for
it. If state['argument_a'] already exists, rebut it
directly. If Paper B's claim is genuinely the weaker
read of the evidence, say so plainly — do not bluff."""

JUDGE_INSTRUCTION = """Read state['argument_a'] and
state['argument_b']. Decide: does the evidence clearly
favor one side, or is this a difference in scope,
method, or population rather than a true contradiction?
Call the escalate tool with resolved=true once you can
render a verdict either way. Call it with resolved=
false if this is a genuine deadlock and one more round
might help. Return ONLY JSON: {"resolved": bool,
"verdict": "...", "confidence": 0-1}."""


def _escalate(
    resolved: bool, tool_context: ToolContext,
) -> dict:
    """Judge calls this; ends the loop once resolved."""
    if resolved:
        tool_context.actions.escalate = True
    return {"resolved": resolved}


def make_debate_loop() -> LoopAgent:
    """Capped debate: built once, reused per dispute."""
    proponent_a = LlmAgent(
        name="proponent_a", model=WORKER_MODEL,
        instruction=PROPONENT_A_INSTRUCTION,
        output_key="argument_a")
    proponent_b = LlmAgent(
        name="proponent_b", model=WORKER_MODEL,
        instruction=PROPONENT_B_INSTRUCTION,
        output_key="argument_b")
    debate_round = ParallelAgent(
        name="debate_round",
        sub_agents=[proponent_a, proponent_b])
    judge = LlmAgent(
        name="judge", model=LEAD_MODEL,
        instruction=JUDGE_INSTRUCTION,
        tools=[_escalate], output_key="verdict")
    return LoopAgent(
        name="debate_loop",
        sub_agents=[debate_round, judge],
        max_iterations=MAX_DEBATE_ROUNDS,
    )

# lit_review/agents.py (continued)

GAP_INSTRUCTION = """You are a gap analyst. The user's
message holds cluster summaries and resolved debate
verdicts from a literature review. List 3-5 sub-
questions the corpus barely touches: topics one paper
mentions in passing, ones flagged as future work, or
ones a debate left genuinely unresolved. Return ONLY
JSON: {"gaps": [{"topic": "...", "why": "...",
"evidence": ["id1", "id2"]}]}."""

HYPOTHESIS_INSTRUCTION = """You are a research
assistant, NOT a scientist. Read state['gaps']. The
user's message also lists the allow-list of citable
paper IDs. For each gap propose ONE testable research
question. Every hypothesis MUST: (1) use hedge language
(may, could, suggests, warrants investigation) and
NEVER claim proof, (2) cite only IDs from the allow-
list, in brackets like [2501.01234], (3) name a
concrete test or dataset. Drop any gap you cannot
ground in a cited paper. Return ONLY JSON:
{"hypotheses": [{"question": "...", "rationale": "...",
"citations": ["id"], "test": "..."}]}."""


def make_tail() -> SequentialAgent:
    """Deterministic tail: gaps first, hypotheses next."""
    gap_agent = LlmAgent(
        name="gap_analyst", model=LEAD_MODEL,
        instruction=GAP_INSTRUCTION,
        output_key="gaps")
    hyp_agent = LlmAgent(
        name="hypothesis_writer", model=LEAD_MODEL,
        instruction=HYPOTHESIS_INSTRUCTION,
        output_key="hypotheses")
    return SequentialAgent(
        name="gaps_to_hypotheses",
        sub_agents=[gap_agent, hyp_agent])
