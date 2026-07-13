# crew/models.py
from __future__ import annotations

from pydantic import BaseModel


class Advisory(BaseModel):
    cve_id: str
    published: str
    cvss_v3: float
    vendor_product: str
    summary: str
    source: str
    source_url: str


class DedupVerdict(BaseModel):
    cve_id: str
    is_duplicate: bool
    duplicate_of: str | None = None
    similarity: float = 0.0


class IngestResult(BaseModel):
    advisories: list[Advisory]
    duplicates: list[DedupVerdict]


class ExploitVerdict(BaseModel):
    cve_id: str
    kev_listed: bool
    poc_public: bool
    active_exploitation: bool
    confidence: str
    rationale: str


class CorrelationResult(BaseModel):
    verdicts: list[ExploitVerdict]


class RankedItem(BaseModel):
    cve_id: str
    risk_score: float
    matched_assets: list[str]
    rationale: str


class RankedList(BaseModel):
    items: list[RankedItem]


class ThreatBrief(BaseModel):
    week_of: str
    headline: str
    ranked_actions: list[str]
    body_markdown: str
