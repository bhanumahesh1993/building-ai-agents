# workflow.py — the agentic RAG pipeline as events
from __future__ import annotations

import json
import os

from anthropic import Anthropic
from workflows import Workflow, step, Context
from workflows.events import (
    Event, StartEvent, StopEvent)

from .index import PgVectorStore
from .rerank import rerank
from .synthesize import answer_with_citations
from .citations import check

ANALYZE_MODEL = os.getenv(
    "ANALYZE_MODEL", "claude-haiku-4-5")
MAX_LOOPS = int(os.getenv("MAX_LOOPS", "2"))

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _client
    if _client is None:
        _client = Anthropic()
    return _client

ANALYZE_PROMPT = """Break this question into 1-4
independent, searchable sub-questions. A simple
question needs just one. Return JSON only.

Question: {question}

JSON: {{"sub_queries": ["...", ...]}}"""


class SubQuery(Event):
    question: str
    text: str
    loop: int


class Retrieved(Event):
    question: str
    chunks: list[dict]
    loop: int


class Draft(Event):
    question: str
    answer: str
    chunks: list[dict]
    loop: int


class RAGWorkflow(Workflow):

    @step
    async def analyze(
        self, ctx: Context, ev: StartEvent,
    ) -> None:
        """Decompose the question, fan out searches."""
        store = PgVectorStore(ev.conn)
        await ctx.store.set("store", store)
        await ctx.store.set("acl", ev.acl)
        prompt = ANALYZE_PROMPT.format(
            question=ev.question)
        resp = _get_client().messages.create(
            model=ANALYZE_MODEL, max_tokens=300,
            messages=[
                {"role": "user", "content": prompt}],
        )
        plan = json.loads(resp.content[0].text)
        subs = plan["sub_queries"][:4]
        await ctx.store.set("n_subs", len(subs))
        for text in subs:
            ctx.send_event(SubQuery(
                question=ev.question, text=text,
                loop=0))

    @step(num_workers=4)
    async def retrieve(
        self, ctx: Context, ev: SubQuery,
    ) -> Retrieved:
        """One sub-query: hybrid search, own context."""
        store = await ctx.store.get("store")
        acl = await ctx.store.get("acl")
        chunks = store.hybrid_search(
            ev.text, k=20, acl=acl)
        return Retrieved(
            question=ev.question, chunks=chunks,
            loop=ev.loop)

    @step
    async def rerank_and_synthesize(
        self, ctx: Context, ev: Retrieved,
    ) -> Draft | StopEvent | None:
        """Fan-in, dedupe, rerank, write a draft."""
        n = await ctx.store.get("n_subs")
        gathered = ctx.collect_events(
            ev, [Retrieved] * n)
        if gathered is None:
            return None
        question = gathered[0].question
        pool, seen = [], set()
        for r in gathered:
            for c in r.chunks:
                if c["id"] not in seen:
                    seen.add(c["id"])
                    pool.append(c)
        top = rerank(question, pool, k=6)
        if not top:
            return StopEvent(result={
                "answer": "No grounded source found "
                          "for this question.",
                "sources": []})
        out = answer_with_citations(question, top)
        return Draft(
            question=question, answer=out["answer"],
            chunks=top, loop=gathered[0].loop)

    @step
    async def self_check(
        self, ctx: Context, ev: Draft,
    ) -> SubQuery | StopEvent:
        """Verify claims are sourced; loop on gaps."""
        result = check(ev.answer, len(ev.chunks))
        if result["grounded"] or ev.loop >= MAX_LOOPS:
            return StopEvent(result={
                "answer": ev.answer,
                "sources": ev.chunks,
                "citation_check": result})
        await ctx.store.set("n_subs", 1)
        return SubQuery(
            question=ev.question,
            text=result["gaps"][0],
            loop=ev.loop + 1)


workflow = RAGWorkflow(timeout=90)
