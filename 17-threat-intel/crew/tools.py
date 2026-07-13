# crew/tools.py
from __future__ import annotations

import os

import psycopg
from crewai.tools import tool
from openai import OpenAI
from pgvector.psycopg import register_vector

EMBED_MODEL = "text-embedding-3-small"
DB_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://pg:pg@localhost:5432/threat")
SIM_THRESHOLD = float(
    os.getenv("DEDUP_SIMILARITY_THRESHOLD", "0.92"))

_openai: OpenAI | None = None


def _get_openai() -> OpenAI:
    """Lazily build the client so the module imports
    without a key present (tests, offline use)."""
    global _openai
    if _openai is None:
        _openai = OpenAI()
    return _openai

_FEED = [
    {"cve_id": "CVE-2026-1001", "published": "2026-07-06",
     "cvss_v3": 9.8, "vendor_product": "libimage 1.2",
     "summary": "Heap overflow in libimage's thumbnail "
                 "decoder allows remote code execution.",
     "source": "NVD-mock",
     "source_url": "https://nvd.example/CVE-2026-1001"},
    {"cve_id": "CVE-2026-1042", "published": "2026-07-07",
     "cvss_v3": 7.5, "vendor_product": "Ivanti Connect "
                 "Secure 22.7",
     "summary": "Auth bypass in the VPN gateway's admin "
                 "portal via a crafted session cookie.",
     "source": "Vendor-bulletin-mock",
     "source_url": "https://vendor.example/adv/1042"},
    {"cve_id": "CVE-2026-1042-R", "published": "2026-07-08",
     "cvss_v3": 7.5, "vendor_product": "Ivanti Connect "
                 "Secure 22.7",
     "summary": "Reissued advisory: auth bypass in the VPN "
                 "gateway admin portal via session cookie.",
     "source": "NVD-mock",
     "source_url": "https://nvd.example/CVE-2026-1042-R"},
    {"cve_id": "CVE-2026-1077", "published": "2026-07-08",
     "cvss_v3": 8.1, "vendor_product": "PostgreSQL 15.4",
     "summary": "Privilege escalation via a crafted "
                 "extension load path.",
     "source": "NVD-mock",
     "source_url": "https://nvd.example/CVE-2026-1077"},
    {"cve_id": "CVE-2026-1090", "published": "2026-07-09",
     "cvss_v3": 9.1, "vendor_product": "Apache HTTP "
                 "Server 2.4.58",
     "summary": "Request-smuggling flaw allows cache "
                 "poisoning and auth-header leakage.",
     "source": "Vendor-bulletin-mock",
     "source_url": "https://vendor.example/adv/1090"},
]

_EXPLOIT_INTEL = {
    "CVE-2026-1001": {"kev_listed": False,
                       "poc_public": False,
                       "active_exploitation": False,
                       "confidence": "low",
                       "source": "vendor telemetry, mock"},
    "CVE-2026-1042": {"kev_listed": True,
                       "poc_public": True,
                       "active_exploitation": True,
                       "confidence": "high",
                       "source": "CISA KEV, mock"},
    "CVE-2026-1077": {"kev_listed": False,
                       "poc_public": True,
                       "active_exploitation": False,
                       "confidence": "medium",
                       "source": "exploit-db, mock"},
    "CVE-2026-1090": {"kev_listed": False,
                       "poc_public": False,
                       "active_exploitation": True,
                       "confidence": "medium",
                       "source": "ISAC bulletin, mock"},
}

_ASSETS = [
    {"asset_id": "web-01", "product": "Apache HTTP Server",
     "version": "2.4.58", "exposure": "internet-facing",
     "criticality": "high", "count": 12},
    {"asset_id": "vpn-gw", "product": "Ivanti Connect "
     "Secure", "version": "22.7",
     "exposure": "internet-facing", "criticality": "high",
     "count": 3},
    {"asset_id": "batch-db", "product": "PostgreSQL",
     "version": "15.4", "exposure": "internal",
     "criticality": "medium", "count": 6},
    {"asset_id": "legacy-lab", "product": "libimage",
     "version": "1.2", "exposure": "isolated",
     "criticality": "low", "count": 3},
]


def _embed(text: str) -> list[float]:
    resp = _get_openai().embeddings.create(
        model=EMBED_MODEL, input=text)
    return resp.data[0].embedding


def _to_pgvector(vec: list[float]) -> str:
    return "[" + ",".join(str(x) for x in vec) + "]"


@tool("CVE Feed Lookup")
def cve_feed_stub(days: int = 7) -> list[dict]:
    """Return raw advisories published in the window - a
    stand-in for a real NVD/vendor feed. Includes at
    least one deliberately reissued duplicate."""
    return _FEED


@tool("Exploit Intel Lookup")
def exploit_db_stub(cve_id: str) -> dict:
    """Return known exploitation signals for one CVE:
    KEV listing, public PoC, and reported active
    exploitation. Unknown CVEs return all-False with
    low confidence - absence of evidence, not evidence
    of safety."""
    return _EXPLOIT_INTEL.get(cve_id, {
        "kev_listed": False, "poc_public": False,
        "active_exploitation": False,
        "confidence": "low", "source": "no intel found"})


@tool("Asset Inventory Lookup")
def asset_inventory(vendor_product: str) -> list[dict]:
    """Return our assets whose product name appears in
    the advisory's vendor_product string. Empty list
    means we do not run the affected product."""
    words = vendor_product.lower().split()
    return [a for a in _ASSETS
            if any(w in a["product"].lower()
                   for w in words if len(w) > 3)]


@tool("Advisory Dedup Check")
def dedup_check(cve_id: str, summary: str) -> dict:
    """Embed this advisory's summary and search pgvector
    for a prior advisory above the similarity threshold.
    Returns is_duplicate, duplicate_of, and similarity."""
    vec = _embed(summary)
    with psycopg.connect(DB_URL) as conn:
        register_vector(conn)
        row = conn.execute(
            "SELECT cve_id, 1 - (embedding <=> %s) AS sim "
            "FROM advisories ORDER BY embedding <=> %s "
            "LIMIT 1",
            (_to_pgvector(vec), _to_pgvector(vec)),
        ).fetchone()
        is_dup = bool(row) and row[1] >= SIM_THRESHOLD
        conn.execute(
            "INSERT INTO advisories (cve_id, summary, "
            "embedding) VALUES (%s, %s, %s) "
            "ON CONFLICT (cve_id) DO NOTHING",
            (cve_id, summary, _to_pgvector(vec)),
        )
    return {
        "cve_id": cve_id,
        "is_duplicate": is_dup,
        "duplicate_of": row[0] if is_dup else None,
        "similarity": round(row[1], 4) if row else 0.0,
    }
