# crew/ranking.py
from __future__ import annotations

EXPLOIT_WEIGHTS = {
    "kev_listed": 1.0,
    "active_exploitation": 0.85,
    "poc_public": 0.5,
}
EXPLOIT_FLOOR = 0.2  # no known exploitation signal

EXPOSURE_WEIGHTS = {
    "internet-facing": 1.0,
    "internal": 0.55,
    "isolated": 0.2,
}
CRITICALITY_WEIGHTS = {
    "high": 1.0, "medium": 0.65, "low": 0.35,
}


def exploit_factor(signals: dict) -> float:
    """Highest-confidence exploitation signal wins; no
    signal at all floors the factor, it never zeros it -
    an unknown CVE could still be exploited quietly."""
    for key in ("kev_listed", "active_exploitation",
                "poc_public"):
        if signals.get(key):
            return EXPLOIT_WEIGHTS[key]
    return EXPLOIT_FLOOR


def exposure_factor(matched_assets: list[dict]) -> float:
    """Worst-case exposure and criticality across every
    asset that actually runs this product. No match at
    all means the score is driven straight to zero -
    if we don't run it, it cannot hurt us."""
    if not matched_assets:
        return 0.0
    exposure = max(
        EXPOSURE_WEIGHTS.get(a["exposure"], 0.0)
        for a in matched_assets)
    criticality = max(
        CRITICALITY_WEIGHTS.get(a["criticality"], 0.0)
        for a in matched_assets)
    return exposure * criticality


def score_advisory(
    cvss_v3: float,
    exploit_signals: dict,
    matched_assets: list[dict],
) -> float:
    """severity x exploit x exposure, scaled to 0-100.
    Multiplicative on purpose: a CVE that does not touch
    our fleet scores exactly zero, no matter how severe;
    one with no known exploitation is dampened hard, not
    silently ranked by CVSS alone."""
    severity = cvss_v3 / 10.0
    exploit = exploit_factor(exploit_signals)
    exposure = exposure_factor(matched_assets)
    return round(severity * exploit * exposure * 100, 1)
