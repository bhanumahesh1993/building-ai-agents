# tests/test_ranking.py
from __future__ import annotations

from crew.ranking import score_advisory

HIGH_CVSS_NO_EXPOSURE = {
    "cvss_v3": 9.8,
    "exploit_signals": {},
    "matched_assets": [
        {"exposure": "isolated", "criticality": "low"}],
}
LOWER_CVSS_EXPLOITED_EXPOSED = {
    "cvss_v3": 7.5,
    "exploit_signals": {"kev_listed": True},
    "matched_assets": [
        {"exposure": "internet-facing",
         "criticality": "high"}],
}


def test_context_beats_raw_severity():
    quiet = score_advisory(**HIGH_CVSS_NO_EXPOSURE)
    urgent = score_advisory(
        **LOWER_CVSS_EXPLOITED_EXPOSED)
    # Lower CVSS, but KEV-listed and internet-facing,
    # must outrank a higher CVSS nobody is exploiting.
    assert urgent > quiet


def test_no_matched_assets_scores_zero():
    score = score_advisory(
        cvss_v3=10.0,
        exploit_signals={"kev_listed": True},
        matched_assets=[])
    assert score == 0.0
