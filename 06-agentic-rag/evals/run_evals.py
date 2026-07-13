# evals/run_evals.py — the full RAG eval suite
from __future__ import annotations

import json

from assistant.workflow import workflow

JUDGE_PROMPT = """Grade this answer 1-5 on each
axis. Return JSON only.

- faithfulness: is every claim backed by a source?
- relevance: does it answer the actual question?

Question: {question}
Answer: {answer}

JSON: {{"faithfulness": n, "relevance": n}}"""


def hit_rate(gold_chunk_id: int, chunks: list[dict],
             k: int = 6) -> bool:
    """Did the true chunk land in the top k?"""
    return gold_chunk_id in [
        c["id"] for c in chunks[:k]]


async def run_one(item: dict) -> dict:
    result = await workflow.run(
        question=item["question"], conn=None,
        acl=["public"])
    hit = hit_rate(
        item["gold_chunk_id"], result["sources"])
    return {
        "question": item["question"],
        "hit": hit,
        "citation_check": result["citation_check"],
    }


if __name__ == "__main__":
    with open("evals/dataset.jsonl") as fh:
        items = [json.loads(line) for line in fh]
    for item in items:
        import asyncio
        print(asyncio.run(run_one(item)))
