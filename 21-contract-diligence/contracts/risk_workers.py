# contracts/risk_workers.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from .state import Clause, RiskFlag, RiskWorkerState

WORKER_MODEL = os.getenv(
    "WORKER_MODEL", "claude-sonnet-4-5")

RUBRIC = {
    "indemnification": "uncapped or one-sided "
        "indemnity obligations",
    "liability_cap": "a cap set below likely exposure, "
        "or missing entirely",
    "termination": "no for-convenience exit, or a "
        "notice period under 30 days",
    "ip_assignment": "work product not assigned to "
        "the paying party",
    "confidentiality": "perpetual or one-way "
        "confidentiality duties",
    "governing_law": "an inconvenient or unfamiliar "
        "forum for this client",
    "other": "anything a specialist would flag on "
        "first read",
}

RISK_SYSTEM = """You are a {ctype} specialist reviewer.
Flag risk in the clauses below, watching specifically
for: {rubric}

Do NOT decide enforceability and do NOT give legal
advice -- only flag and explain what a human should
look at. For every flag, quote the exact clause text
you relied on, copied verbatim, never paraphrased.

Return ONLY JSON:
{{"flags": [
  {{"clause_id": "...", "severity": "low|medium|high",
    "quote": "verbatim text from the clause",
    "rationale": "why this needs attorney attention"}}
]}}

Clauses:
{clauses}"""

_llm = ChatAnthropic(model=WORKER_MODEL, temperature=0)


def _norm(s: str) -> str:
    return " ".join(s.split()).lower()


def _verify_quotes(
    flags: list[dict], clauses: list[Clause],
) -> list[RiskFlag]:
    """Guardrail: drop any flag whose quote is not
    actually present in its clause's own text."""
    by_id = {c["clause_id"]: c["text"] for c in clauses}
    out: list[RiskFlag] = []
    for f in flags:
        src = by_id.get(f["clause_id"], "")
        if _norm(f["quote"]) in _norm(src):
            out.append(f)
        # else: silently dropped. A fabricated quote
        # is worse than a missing flag.
    return out


def risk_node(state: RiskWorkerState) -> dict:
    """One clause-type specialist, batched over every
    instance of that type in the whole document set."""
    ctype = state["clause_type"]
    clauses = state["clauses"]
    body = "\n\n".join(
        f"[{c['clause_id']}] {c['text']}" for c in clauses)
    prompt = RISK_SYSTEM.format(
        ctype=ctype, rubric=RUBRIC.get(ctype, RUBRIC["other"]),
        clauses=body)
    resp = _llm.invoke(prompt)
    parsed = json.loads(resp.content)
    verified = _verify_quotes(parsed["flags"], clauses)
    flags: list[RiskFlag] = [{
        "clause_id": f["clause_id"], "clause_type": ctype,
        "severity": f["severity"], "quote": f["quote"],
        "rationale": f["rationale"],
    } for f in verified]
    return {"flags": flags}
