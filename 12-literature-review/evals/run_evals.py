# evals/run_evals.py
from __future__ import annotations

import json

from lit_review.tools import validate_citations
from lit_review.workflow import run_review
from lit_review.corpus import get_known_ids
from evals.judge import grade_faithfulness


def retrieval_relevance(papers: list[dict], topic: str) -> float:
    """Cheap proxy: fraction of hits above a distance bar."""
    if not papers:
        return 0.0
    good = sum(1 for p in papers if p["dist"] < 0.35)
    return good / len(papers)


def contradiction_precision(
    found: list[dict], labeled: list[tuple[str, str]],
) -> float:
    """Of the pairs flagged, how many are known-real?"""
    if not found:
        return 1.0
    flagged = {
        (c["dispute"]["paper_a"], c["dispute"]["paper_b"])
        for c in found
    }
    hits = sum(1 for pair in flagged if pair in labeled)
    return hits / len(flagged)


async def run_one(topic: str, labeled_pairs) -> dict:
    result = await run_review(topic)
    guard = validate_citations(
        json.dumps(result["hypotheses"]), get_known_ids())
    precision = contradiction_precision(
        result["contradictions"], labeled_pairs)
    return {
        "topic": topic,
        "citation_validity": guard["clean"],
        "contradiction_precision": precision,
        "n_hypotheses": len(result["hypotheses"]),
    }
