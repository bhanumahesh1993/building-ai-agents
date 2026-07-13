# monitor/fetch_tool.py
from __future__ import annotations

import os
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx
from selectolax.parser import HTMLParser

USER_AGENT = (
    "competi-watch/1.0 "
    "(+https://example.com/bot; "
    "contact: ci-team@example.com)"
)

_TIMEOUT = httpx.Timeout(15.0, connect=5.0)

# Minimum seconds between two fetches of the same
# domain -- keeps a scheduled scan from hammering a
# competitor's site even if the registry lists many
# pages on it.
MIN_INTERVAL_SECONDS = float(
    os.getenv("MIN_FETCH_INTERVAL_SECONDS", "2.0"))

_robots_cache: dict[str, RobotFileParser | None] = {}
_last_fetch_at: dict[str, float] = {}


class RobotsDisallowed(RuntimeError):
    """Raised when robots.txt forbids fetching a URL."""


def _robots_url(url: str) -> str:
    parts = urlparse(url)
    return f"{parts.scheme}://{parts.netloc}/robots.txt"


def _get_robot_parser(url: str) -> RobotFileParser | None:
    """Fetch and cache robots.txt per domain.

    Returns None when robots.txt could not be read at
    all (network error, timeout, etc.) so callers can
    fail open rather than block a scheduled scan on an
    unrelated outage.
    """
    domain = urlparse(url).netloc
    if domain not in _robots_cache:
        parser: RobotFileParser | None = RobotFileParser()
        parser.set_url(_robots_url(url))
        try:
            parser.read()
        except OSError:
            parser = None
        _robots_cache[domain] = parser
    return _robots_cache[domain]


def is_allowed(url: str, user_agent: str = USER_AGENT) -> bool:
    """robots.txt gate for one URL.

    Fails open (allows the fetch) when robots.txt is
    unreachable -- an outage of the robots.txt endpoint
    itself shouldn't block a page we'd otherwise be
    allowed to read.
    """
    parser = _get_robot_parser(url)
    if parser is None:
        return True
    return parser.can_fetch(user_agent, url)


def seconds_until_allowed(
        domain: str, now: float,
        min_interval: float = MIN_INTERVAL_SECONDS) -> float:
    """Pure: how long to wait before hitting `domain`
    again, given the last fetch time recorded for it.

    Kept side-effect free (no sleeping, no wall clock
    reads) so the throttling math is unit-testable.
    """
    last = _last_fetch_at.get(domain)
    if last is None:
        return 0.0
    return max(0.0, min_interval - (now - last))


def _throttle(url: str) -> None:
    domain = urlparse(url).netloc
    wait = seconds_until_allowed(domain, time.monotonic())
    if wait > 0:
        time.sleep(wait)
    _last_fetch_at[domain] = time.monotonic()


def fetch_page(url: str, selector: str) -> str:
    """Fetch one URL and return its cleaned text."""
    if not is_allowed(url):
        raise RobotsDisallowed(
            f"robots.txt disallows fetching {url}")
    _throttle(url)

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
