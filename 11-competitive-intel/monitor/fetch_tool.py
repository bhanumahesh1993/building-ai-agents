# monitor/fetch_tool.py
from __future__ import annotations

import httpx
from selectolax.parser import HTMLParser

USER_AGENT = (
    "competi-watch/1.0 "
    "(+https://example.com/bot; "
    "contact: ci-team@example.com)"
)

_TIMEOUT = httpx.Timeout(15.0, connect=5.0)


def fetch_page(url: str, selector: str) -> str:
    """Fetch one URL and return its cleaned text."""
    headers = {"User-Agent": USER_AGENT}
    with httpx.Client(
            timeout=_TIMEOUT, headers=headers,
            follow_redirects=True) as client:
        resp = client.get(url)
        resp.raise_for_status()

    tree = HTMLParser(resp.text)
    for tag in tree.css(
            "script, style, nav, footer, noscript"):
        tag.decompose()

    node = tree.css_first(selector) or tree.body
    text = node.text(separator=" ", strip=True) \
        if node else ""
    return " ".join(text.split())
