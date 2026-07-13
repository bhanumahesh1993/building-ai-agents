# citations.py — verify every claim has a source
from __future__ import annotations

import json
import os
import re

from anthropic import Anthropic

CHECK_MODEL = os.getenv(
    "CHECK_MODEL", "claude-haiku-4-5")

_client = Anthropic()

CHECK_PROMPT = """You are a fact-checker. List every
claim in this answer that has NO bracketed citation
attached. Return JSON only.

Answer:
{answer}

JSON: {{"gaps": ["claim text", ...],
"grounded": true|false}}"""

CITE_RE = re.compile(r"\[(\d+)\]")


def check(answer: str, n_sources: int) -> dict:
    """Mechanical range check, then an LLM gap check."""
    cited = {int(n) for n in CITE_RE.findall(answer)}
    out_of_range = [
        n for n in cited
        if n < 1 or n > n_sources]
    prompt = CHECK_PROMPT.format(answer=answer)
    resp = _client.messages.create(
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
