# aml/app.py
from __future__ import annotations

import os
import uuid

import psycopg
from agents import Runner
from fastapi import FastAPI
from pydantic import BaseModel

from . import investigate as inv_mod
from .guardrails import redact_pii
from .investigate import investigator
from .kyc import resolve_entity
from .monitor import sweep
from .sar_draft import sar_drafter
from .scoring import match_typologies, score_case
from .state import Case, CaseStatus, Transaction

DB_URL = os.environ["DATABASE_URL"]

app = FastAPI(title="AML Investigation API")
CASES: dict[str, Case] = {}


class ScanReq(BaseModel):
    transactions: list[dict]


class ReviewReq(BaseModel):
    reviewer: str
    approved: bool
    notes: str = ""


@app.post("/cases/scan")
def scan(req: ScanReq):
    """Run the overnight sweep; open one case per
    account with at least one fired alert."""
    txns = [Transaction(**d) for d in req.transactions]
    alerts = sweep(txns, history={})
    by_account: dict[str, list] = {}
    for a in alerts:
        acct = next(
            t.account_id for t in txns
            if t.txn_id in a.txn_ids)
        by_account.setdefault(acct, []).append(a)

    opened = []
    for acct, acct_alerts in by_account.items():
        case_id = f"case_{uuid.uuid4().hex[:10]}"
        case = Case(
            case_id=case_id, subject_account=acct,
            alerts=acct_alerts)
        case.log(f"opened from {len(acct_alerts)} alert(s)")
        inv_mod.TXN_DB[acct] = [
            t.__dict__ for t in txns
            if t.account_id == acct]
        CASES[case_id] = case
        opened.append(case_id)
    return {"opened": opened}


@app.post("/cases/{case_id}/process")
async def process(case_id: str):
    """Run kyc -> investigate -> score -> draft, in
    that fixed order -- no model chooses the sequence."""
    case = CASES[case_id]
    case.status = CaseStatus.INVESTIGATING

    with psycopg.connect(DB_URL) as conn:
        names = {case.subject_account} | {
            t["counterparty"]
            for t in inv_mod.TXN_DB[case.subject_account]}
        for name in names:
            entity = resolve_entity(conn, name, "unknown")
            case.entities.append(entity)
            inv_mod.KYC_DB[name] = entity.__dict__
    case.log(f"kyc resolved {len(case.entities)} entity")

    result = await Runner.run(
        investigator,
        f"Investigate account {case.subject_account}. "
        f"Alerts: {[a.reason for a in case.alerts]}")
    case.narrative = result.final_output
    case.log("investigation narrative recorded")

    case.typologies = match_typologies(case.alerts)
    case.risk_score = score_case(case)
    case.status = CaseStatus.SCORED

    draft = await Runner.run(
        sar_drafter,
        f"Narrative: {case.narrative}\n"
        f"Typologies: {case.typologies}\n"
        f"Risk score: {case.risk_score:.1f}")
    case.sar_draft = draft.final_output
    case.status = CaseStatus.PENDING_REVIEW
    case.log("SAR draft ready, awaiting human review")
    return {
        "status": case.status.value,
        "sar_draft": redact_pii(case.sar_draft),
    }


@app.post("/cases/{case_id}/review")
def review(case_id: str, req: ReviewReq):
    """The only exit from PENDING_REVIEW. No function
    anywhere in this codebase files a SAR -- a human
    does that, outside this system, after reading
    exactly the draft this endpoint returns."""
    case = CASES[case_id]
    case.status = (
        CaseStatus.APPROVED if req.approved
        else CaseStatus.REJECTED)
    verdict = "approved" if req.approved else "rejected"
    case.log(
        f"reviewed by {req.reviewer}: {verdict} "
        f"-- {req.notes}")
    return {"status": case.status.value}
