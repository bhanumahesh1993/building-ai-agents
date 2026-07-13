# evals/dedup_check_eval.py
from __future__ import annotations

from crew.tools import dedup_check

KNOWN_DUPLICATE_PAIRS = [
    ("CVE-2026-1042", "CVE-2026-1042-R"),
]


def dedup_accuracy() -> dict:
    """Deterministic check: does the dedup tool catch
    a known-duplicate pair fed through it in sequence?"""
    hits = 0
    for original, reissue in KNOWN_DUPLICATE_PAIRS:
        summary = ("Auth bypass in the VPN gateway's "
                    "admin portal via session cookie.")
        dedup_check(original, summary)
        result = dedup_check(reissue, summary)
        if result["is_duplicate"]:
            hits += 1
    return {
        "pairs_tested": len(KNOWN_DUPLICATE_PAIRS),
        "pairs_caught": hits,
        "accuracy": hits / len(KNOWN_DUPLICATE_PAIRS),
    }
