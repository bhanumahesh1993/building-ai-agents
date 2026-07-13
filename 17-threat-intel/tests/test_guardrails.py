# tests/test_guardrails.py
from __future__ import annotations

import pytest

from crew.crew import _reject_invented_cves


def test_ranked_cves_within_known_set_pass():
    """Every CVE the ranker touched was seen by the
    Ingest Analyst - no exception raised."""
    _reject_invented_cves(
        ranked_ids={"CVE-2026-1001", "CVE-2026-1042"},
        known_ids={"CVE-2026-1001", "CVE-2026-1042",
                   "CVE-2026-1077"})


def test_ranked_cves_can_be_a_strict_subset():
    """The ranker need not rank every ingested CVE - it
    may only need to fail on IDs it never saw."""
    _reject_invented_cves(
        ranked_ids={"CVE-2026-1001"},
        known_ids={"CVE-2026-1001", "CVE-2026-1042"})


def test_invented_cve_raises():
    """A CVE ID absent from the ingest result must never
    reach the brief - this is the hallucination guard the
    book calls out explicitly."""
    with pytest.raises(ValueError, match="invented"):
        _reject_invented_cves(
            ranked_ids={"CVE-2026-9999"},
            known_ids={"CVE-2026-1001"})


def test_invented_cve_error_names_the_culprit():
    """The error should name exactly the invented ID(s),
    not just fail generically - so an operator can see
    what the ranker hallucinated."""
    with pytest.raises(ValueError, match="CVE-2026-4242"):
        _reject_invented_cves(
            ranked_ids={"CVE-2026-1001", "CVE-2026-4242"},
            known_ids={"CVE-2026-1001"})
