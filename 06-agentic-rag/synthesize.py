# synthesize.py — grounded answer, inline [n] cites
from __future__ import annotations

import os

from anthropic import Anthropic

SYNTH_MODEL = os.getenv(
    "SYNTH_MODEL", "claude-sonnet-4-5")

_client = Anthropic()

SYNTH_PROMPT = """Answer using ONLY the numbered
sources below. Cite every non-obvious claim inline
like [2]. If the sources do not contain the answer,
say so plainly instead of guessing.

Question: {question}

Sources:
{sources}"""


def _source_block(chunks: list[dict]) -> str:
    lines = []
    for i, c in enumerate(chunks, start=1):
        lines.append(
            f"[{i}] ({c['doc_id']} §{c['section']}) "
            f"{c['body']}")
    return "\n\n".join(lines)


def answer_with_citations(
    question: str, chunks: list[dict],
) -> dict:
    """Write a grounded answer citing numbered chunks."""
    sources = _source_block(chunks)
    prompt = SYNTH_PROMPT.format(
        question=question, sources=sources)
    resp = _client.messages.create(
        model=SYNTH_MODEL, max_tokens=900,
        messages=[
            {"role": "user", "content": prompt}],
    )
    return {
        "answer": resp.content[0].text,
        "sources": chunks}
