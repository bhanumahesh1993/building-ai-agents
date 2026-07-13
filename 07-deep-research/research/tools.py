# research/tools.py
from __future__ import annotations

import os

from tavily import TavilyClient

_client = TavilyClient(
    api_key=os.environ["TAVILY_API_KEY"])

TRUSTED = (
    ".gov", ".edu", ".org", "reuters.com",
    "nature.com", "iea.org", "who.int",
)


def web_search(query: str, k: int = 6) -> list[dict]:
    """Search the web, return normalized results."""
    resp = _client.search(
        query=query,
        max_results=k,
        search_depth="advanced",
    )
    out: list[dict] = []
    for r in resp.get("results", []):
        out.append({
            "url": r["url"],
            "title": r.get("title", ""),
            "snippet": r.get("content", "")[:1200],
            "score": r.get("score", 0.0),
        })
    return out


def is_trusted(url: str) -> bool:
    """Cheap source-quality heuristic."""
    return any(t in url for t in TRUSTED)
