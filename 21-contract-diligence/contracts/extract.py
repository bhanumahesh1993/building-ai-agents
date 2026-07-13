# contracts/extract.py
from __future__ import annotations

import json
import os

from langchain_anthropic import ChatAnthropic

from .ingest import split_candidates
from .state import Clause, ContractDoc, DDState

EXTRACT_MODEL = os.getenv(
    "EXTRACT_MODEL", "claude-sonnet-4-5")

TYPES = (
    "indemnification", "liability_cap", "termination",
    "ip_assignment", "confidentiality", "governing_law",
    "other",
)

EXTRACT_SYSTEM = """Classify this contract section into
exactly ONE of: {types}. Return ONLY JSON:
{{"clause_type": "...", "text": "verbatim section
text, unedited"}}
If it is boilerplate with no legal substance
(signature blocks, page numbers, table of contents),
return "other".

Heading: {heading}
Section:
{body}"""

_llm = ChatAnthropic(model=EXTRACT_MODEL, temperature=0)


def extract_clauses(doc: ContractDoc) -> list[Clause]:
    """Classify every candidate block into a typed clause."""
    out: list[Clause] = []
    for i, (heading, body) in enumerate(
        split_candidates(doc["text"])
    ):
        if len(body) < 40:
            continue
        prompt = EXTRACT_SYSTEM.format(
            types=", ".join(TYPES), heading=heading,
            body=body[:2000])
        resp = _llm.invoke(prompt)
        parsed = json.loads(resp.content)
        out.append({
            "clause_id": f"{doc['contract_id']}-{i}",
            "contract_id": doc["contract_id"],
            "clause_type": parsed["clause_type"],
            "heading": heading,
            "text": parsed["text"],
        })
    return out


def extract_node(state: DDState) -> dict:
    """Typed extraction across the whole document set."""
    clauses: list[Clause] = []
    for doc in state["contracts"]:
        clauses.extend(extract_clauses(doc))
    return {"clauses": clauses}
