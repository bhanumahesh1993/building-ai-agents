# crew/crew.py
from __future__ import annotations

import os

from crewai import Crew, Process
from crewai.tools import tool

from .agents import (
    ingest_analyst, threat_correlator, exposure_ranker,
    briefing_writer,
)
from .tasks import (
    ingest_task, correlate_task, rank_task, brief_task,
)
from .models import ThreatBrief
from .ranking import score_advisory
from .tools import asset_inventory

COST_CAP_USD = float(os.getenv("COST_CAP_USD", "1.0"))
_PRICE = {"claude-sonnet-4-5": (3.0, 15.0),
          "claude-opus-4-5": (15.0, 75.0)}


@tool("Exposure Score")
def compute_exposure_score(
    cvss_v3: float, kev_listed: bool,
    active_exploitation: bool, poc_public: bool,
    vendor_product: str,
) -> dict:
    """Deterministic risk score: severity x exploit x
    exposure, scaled 0-100. Wraps ranking.py so the
    Exposure Ranking Analyst never computes this by
    hand."""
    assets = asset_inventory(vendor_product)
    score = score_advisory(
        cvss_v3,
        {"kev_listed": kev_listed,
         "active_exploitation": active_exploitation,
         "poc_public": poc_public},
        assets)
    return {"risk_score": score,
            "matched_assets": [a["asset_id"]
                               for a in assets]}


exposure_ranker.tools = (
    exposure_ranker.tools + [compute_exposure_score])


def _usd(usage) -> float:
    """Rough per-run cost - assumes one dominant model
    tier; see 'What it costs' for the real breakdown."""
    p_in, p_out = _PRICE["claude-sonnet-4-5"]
    return (usage.prompt_tokens * p_in
            + usage.completion_tokens * p_out) / 1e6


def _reject_invented_cves(
    ranked_ids: set[str], known_ids: set[str],
) -> None:
    """Guardrail: the ranker may never introduce a CVE
    the Ingest Analyst never saw."""
    invented = ranked_ids - known_ids
    if invented:
        raise ValueError(
            f"Ranker invented unknown CVE IDs: "
            f"{sorted(invented)}")


def run_weekly_brief(
    days: int = 7, week_of: str = "",
) -> ThreatBrief:
    """Run the four-stage pipeline and return the brief."""
    crew = Crew(
        agents=[ingest_analyst, threat_correlator,
                exposure_ranker, briefing_writer],
        tasks=[ingest_task, correlate_task, rank_task,
               brief_task],
        process=Process.sequential,
        verbose=True,
    )
    crew.kickoff(inputs={"days": days,
                          "week_of": week_of})

    ingested = ingest_task.output.pydantic
    ranked = rank_task.output.pydantic
    known_ids = {a.cve_id for a in ingested.advisories}
    ranked_ids = {i.cve_id for i in ranked.items}
    _reject_invented_cves(ranked_ids, known_ids)

    spent = _usd(crew.usage_metrics)
    if spent > COST_CAP_USD:
        raise RuntimeError(
            f"Run cost ${spent:.2f} exceeded cap "
            f"${COST_CAP_USD:.2f}")

    return brief_task.output.pydantic
