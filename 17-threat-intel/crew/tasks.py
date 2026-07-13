# crew/tasks.py
from __future__ import annotations

from crewai import Task

from .agents import (
    ingest_analyst, threat_correlator, exposure_ranker,
    briefing_writer,
)
from .models import (
    IngestResult, CorrelationResult, RankedList,
    ThreatBrief,
)

ingest_task = Task(
    description=(
        "Pull advisories published in the last {days} "
        "days from the CVE Feed Lookup tool. For each "
        "one, call Advisory Dedup Check. Return the "
        "clean advisory list and the duplicates you "
        "flagged, with what each duplicates."
    ),
    expected_output=(
        "An IngestResult: deduplicated advisories plus "
        "a list of DedupVerdict entries."
    ),
    agent=ingest_analyst,
    output_pydantic=IngestResult,
)

correlate_task = Task(
    description=(
        "For every advisory in the ingest result, call "
        "Exploit Intel Lookup and write a hedged "
        "ExploitVerdict. State confidence honestly - "
        "'no intel found' is a valid, low-confidence "
        "answer, not a reason to guess."
    ),
    expected_output=(
        "A CorrelationResult: one ExploitVerdict per "
        "unique CVE."
    ),
    agent=threat_correlator,
    context=[ingest_task],
    output_pydantic=CorrelationResult,
)

rank_task = Task(
    description=(
        "For every CVE, call Asset Inventory Lookup, "
        "then compute its risk score with the Exposure "
        "Score tool using that CVE's cvss_v3, the "
        "correlator's exploit signals, and the matched "
        "assets. Sort descending by score and write a "
        "one-sentence rationale per item."
    ),
    expected_output=(
        "A RankedList: one RankedItem per CVE, sorted "
        "by risk_score descending."
    ),
    agent=exposure_ranker,
    context=[ingest_task, correlate_task],
    output_pydantic=RankedList,
)

brief_task = Task(
    description=(
        "Using only the ranked list and its rationale, "
        "write a weekly threat brief for {week_of}: a "
        "one-line headline, a ranked action list of the "
        "top items, and a short body. Cite each claim's "
        "source CVE ID. Hedge exploitation claims exactly "
        "as the ranked list hedges them."
    ),
    expected_output=(
        "A ThreatBrief: week_of, headline, "
        "ranked_actions, and body_markdown."
    ),
    agent=briefing_writer,
    context=[rank_task],
    output_pydantic=ThreatBrief,
)
