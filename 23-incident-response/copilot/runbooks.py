# copilot/runbooks.py
from __future__ import annotations

import os

import numpy as np
import voyageai

EMBED_MODEL = os.getenv(
    "EMBED_MODEL", "voyage-3.5")

_client: voyageai.Client | None = None


def _get_client() -> voyageai.Client:
    """Lazily build so the module imports without a key present
    (tests, offline use)."""
    global _client
    if _client is None:
        _client = voyageai.Client(
            api_key=os.environ["VOYAGE_API_KEY"])
    return _client

RUNBOOKS = [
    {
        "id": "rb-014",
        "title": "Recent deploy regression - "
                  "roll back",
        "text": (
            "error rate or latency spike beginning "
            "within minutes of a deploy; rollback "
            "the last release and confirm recovery"),
        "action": "rollback_deploy",
        "blast_radius": (
            "medium - reverts all traffic on this "
            "service to the prior deploy; brief "
            "connection blip during the swap"),
        "steps": [
            "Confirm the previous stable deploy id",
            "Roll back the service to that deploy",
            "Watch error rate for five minutes",
            "If stable, close; else escalate",
        ],
    },
    {
        "id": "rb-021",
        "title": "Resource exhaustion - scale out",
        "text": (
            "CPU, memory, or connection-pool "
            "saturation with no recent deploy; add "
            "capacity rather than change code"),
        "action": "scale_service",
        "blast_radius": (
            "low - adds replicas; does not touch "
            "existing traffic or code"),
        "steps": [
            "Confirm no recent deploy correlates",
            "Scale the service to +50% replicas",
            "Watch saturation metric for five minutes",
            "If stable, close; else escalate",
        ],
    },
    {
        "id": "rb-033",
        "title": "Dependency outage - failover or "
                  "wait",
        "text": (
            "a downstream dependency reports "
            "degraded health; failover if a replica "
            "exists, otherwise notify and wait"),
        "action": "notify_only",
        "blast_radius": (
            "none - this runbook never changes the "
            "service itself"),
        "steps": [
            "Confirm the dependency's own status page",
            "Failover to a healthy replica if one "
            "exists",
            "Notify the owning team",
            "Re-check dependency health every 5 min",
        ],
    },
    {
        "id": "rb-045",
        "title": "Traffic spike - scale and shed",
        "text": (
            "legitimate demand spike, not an attack "
            "or a bug; scale out and shed low-"
            "priority load if saturation persists"),
        "action": "scale_service",
        "blast_radius": (
            "low - adds replicas; sheds only "
            "low-priority traffic if configured"),
        "steps": [
            "Confirm the spike matches a known "
            "traffic pattern",
            "Scale the service to +100% replicas",
            "Enable load shedding if still saturated",
            "Scale back down once traffic normalizes",
        ],
    },
    {
        "id": "rb-099",
        "title": "Unclear cause - page and observe",
        "text": (
            "the signals do not cleanly match a "
            "known pattern; escalate to a human "
            "with the evidence gathered so far"),
        "action": "notify_only",
        "blast_radius": (
            "none - this runbook never changes the "
            "service itself"),
        "steps": [
            "Page the on-call engineer with the "
            "full case file",
            "Attach every investigation finding "
            "as-is",
            "Take no automated action",
        ],
    },
]

_corpus_vectors: list[list[float]] | None = None


def _corpus() -> list[list[float]]:
    """Embed the runbook corpus once, then cache it."""
    global _corpus_vectors
    if _corpus_vectors is None:
        texts = [
            r["title"] + " - " + r["text"]
            for r in RUNBOOKS]
        resp = _get_client().embed(
            texts, model=EMBED_MODEL,
            input_type="document")
        _corpus_vectors = resp.embeddings
    return _corpus_vectors


def _cosine(a: list[float], b: list[float]) -> float:
    va, vb = np.array(a), np.array(b)
    return float(
        va @ vb
        / (np.linalg.norm(va) * np.linalg.norm(vb)))


def retrieve(query: str) -> dict:
    """Return the best-matching runbook for a query."""
    qvec = _get_client().embed(
        [query], model=EMBED_MODEL,
        input_type="query").embeddings[0]
    vectors = _corpus()
    scores = [_cosine(qvec, v) for v in vectors]
    best = scores.index(max(scores))
    return RUNBOOKS[best]
