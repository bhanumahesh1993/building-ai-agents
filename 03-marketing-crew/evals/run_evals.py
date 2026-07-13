# evals/run_evals.py
from __future__ import annotations

import json

from crew.crew import run_campaign
from evals.judge import grade


def seo_checklist(kit) -> dict:
    """Deterministic SEO checks - no model call."""
    meta_len = len(kit.seo.meta_description)
    body = kit.copy.blog_body.lower()
    kw_hits = sum(
        1 for kw in kit.seo.keywords
        if kw.lower() in body)
    return {
        "meta_len_ok": 120 <= meta_len <= 160,
        "keyword_count": len(kit.seo.keywords),
        "keywords_used_in_body": kw_hits,
    }


def revision_trajectory_ok(kit) -> dict:
    """Did the capped loop behave? No model call."""
    return {
        "revisions_used": kit.revisions_used,
        "within_cap": kit.revisions_used <= 2,
        "shipped_clean": (
            kit.editor.approved
            or "cap reached" in kit.editor.notes),
    }


def run_one(brief: dict) -> dict:
    kit = run_campaign(brief)
    return {
        **seo_checklist(kit),
        **revision_trajectory_ok(kit),
        **grade(brief, kit.copy.blog_body),
    }


if __name__ == "__main__":
    with open("evals/briefs.jsonl") as fh:
        for line in fh:
            brief = json.loads(line)
            print(brief["product_name"],
                  run_one(brief))
