# tests/test_fetch_tool.py — robots.txt + rate-limit guard, no network
from __future__ import annotations

import os

import pytest

import monitor.fetch_tool as ft
from monitor.fetch_tool import (
    RobotsDisallowed, USER_AGENT, _get_robot_parser, fetch_page,
    is_allowed, seconds_until_allowed,
)


class _FakeParser:
    """Stand-in for urllib.robotparser.RobotFileParser
    that never touches the network."""

    def __init__(self, allowed: bool):
        self._allowed = allowed

    def can_fetch(self, user_agent, url):
        return self._allowed


def test_is_allowed_true_when_robots_permits(monkeypatch):
    monkeypatch.setitem(
        ft._robots_cache, "allowed.example.com", _FakeParser(True))
    assert is_allowed("https://allowed.example.com/pricing") is True


def test_is_allowed_false_when_robots_forbids(monkeypatch):
    monkeypatch.setitem(
        ft._robots_cache, "blocked.example.com", _FakeParser(False))
    assert is_allowed("https://blocked.example.com/pricing") is False


def test_is_allowed_fails_open_when_robots_unreachable(monkeypatch):
    monkeypatch.setitem(
        ft._robots_cache, "unreachable.example.com", None)
    assert is_allowed("https://unreachable.example.com/pricing") is True


def test_fetch_page_raises_when_robots_forbids(monkeypatch):
    monkeypatch.setitem(
        ft._robots_cache, "blocked.example.com", _FakeParser(False))
    with pytest.raises(RobotsDisallowed):
        fetch_page("https://blocked.example.com/pricing", "main")


def test_seconds_until_allowed_is_zero_for_a_new_domain():
    assert seconds_until_allowed(
        "never-seen.example.com", now=1000.0) == 0.0


def test_seconds_until_allowed_waits_out_the_remaining_interval(
        monkeypatch):
    # Directly exercise the pure throttle math: a
    # domain fetched 0.5s ago with a 2s minimum
    # interval should report 1.5s remaining.
    monkeypatch.setitem(
        ft._last_fetch_at, "throttled.example.com", 100.0)
    remaining = seconds_until_allowed(
        "throttled.example.com", now=100.5, min_interval=2.0)
    assert remaining == pytest.approx(1.5)


def test_seconds_until_allowed_is_zero_once_interval_elapsed(
        monkeypatch):
    monkeypatch.setitem(
        ft._last_fetch_at, "elapsed.example.com", 100.0)
    remaining = seconds_until_allowed(
        "elapsed.example.com", now=103.0, min_interval=2.0)
    assert remaining == 0.0


def test_seconds_until_allowed_never_negative(monkeypatch):
    monkeypatch.setitem(
        ft._last_fetch_at, "far-future.example.com", 100.0)
    remaining = seconds_until_allowed(
        "far-future.example.com", now=999.0, min_interval=2.0)
    assert remaining == 0.0


def test_default_user_agent_identifies_the_bot_and_contact():
    assert "competi-watch" in USER_AGENT
    assert "contact:" in USER_AGENT


@pytest.mark.skipif(
    not os.environ.get("CI_LIVE_NETWORK_TESTS"),
    reason="hits the live network; opt in with CI_LIVE_NETWORK_TESTS=1",
)
def test_get_robot_parser_reads_a_real_robots_txt():
    parser = _get_robot_parser("https://www.google.com/search")
    assert parser is not None
