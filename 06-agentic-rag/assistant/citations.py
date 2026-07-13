# citations.py — verify every claim has a source
from __future__ import annotations

import json
import os
import re

from anthropic import Anthropic

CHECK_MODEL = os.getenv(
    "CHECK_MODEL", "claude-haiku-4-5")

_client: Anthropic | None = None


def _get_client() -> Anthropic:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _client
    if _client is None:
        _client = Anthropic()
    return _client


CHECK_PROMPT = """You are a fact-checker. List every
claim in this answer that has NO bracketed citation
attached. Return JSON only.

Answer:
{answer}

JSON: {{"gaps": ["claim text", ...],
"grounded": true|false}}"""

CITE_RE = re.compile(r"\[(\d+)\]")


def find_out_of_range_citations(
    answer: str, n_sources: int,
) -> list[int]:
    """Pure, deterministic range check: which [n]
    markers point past the numbered source list."""
    cited = {int(n) for n in CITE_RE.findall(answer)}
    return sorted(
        n for n in cited
        if n < 1 or n > n_sources)


def check(answer: str, n_sources: int) -> dict:
    """Mechanical range check, then an LLM gap check."""
    out_of_range = find_out_of_range_citations(
        answer, n_sources)
    prompt = CHECK_PROMPT.format(answer=answer)
    resp = _get_client().messages.create(
        model=CHECK_MODEL, max_tokens=400,
        messages=[
            {"role": "user", "content": prompt}],
    )
    result = json.loads(resp.content[0].text)
    result["out_of_range_cites"] = out_of_range
    result["grounded"] = (
        result.get("grounded", False)
        and not out_of_range)
    return result
