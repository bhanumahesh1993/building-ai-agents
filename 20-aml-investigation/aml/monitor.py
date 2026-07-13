# aml/monitor.py
from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import timedelta

from .state import Alert, Transaction

CTR_THRESHOLD = 10_000.0
STRUCTURING_MARGIN = 0.92   # "just under" the CTR line
STRUCTURING_WINDOW_DAYS = 5
STRUCTURING_MIN_COUNT = 3
LAYERING_WINDOW_HOURS = 2
LAYERING_MIN_HOPS = 4
ANOMALY_Z = 3.0


def check_structuring(
    txns: list[Transaction],
) -> list[Alert]:
    """Several sub-threshold deposits, one account, a
    tight window -- the textbook smurfing pattern."""
    by_account: dict[str, list[Transaction]] = (
        defaultdict(list))
    for t in txns:
        near_line = (
            STRUCTURING_MARGIN * CTR_THRESHOLD
            <= t.amount < CTR_THRESHOLD)
        if near_line:
            by_account[t.account_id].append(t)

    alerts = []
    for acct, group in by_account.items():
        group.sort(key=lambda t: t.ts)
        start = group[0].ts
        window = timedelta(days=STRUCTURING_WINDOW_DAYS)
        in_window = [
            t for t in group if t.ts - start <= window]
        if len(in_window) >= STRUCTURING_MIN_COUNT:
            ids = [t.txn_id for t in in_window]
            alerts.append(Alert(
                rule="structuring",
                reason=(
                    f"{len(in_window)} deposits just "
                    f"under ${CTR_THRESHOLD:,.0f} on "
                    f"{acct} within "
                    f"{STRUCTURING_WINDOW_DAYS} days"),
                txn_ids=ids,
            ))
    return alerts


def check_layering(
    txns: list[Transaction],
) -> list[Alert]:
    """Funds arrive, then fan out to many counterparties
    within a short dwell time -- classic layering."""
    by_account: dict[str, list[Transaction]] = (
        defaultdict(list))
    for t in txns:
        by_account[t.account_id].append(t)

    alerts = []
    for acct, group in by_account.items():
        group.sort(key=lambda t: t.ts)
        for i, inbound in enumerate(group):
            if inbound.amount <= 0:
                continue
            end = inbound.ts + timedelta(
                hours=LAYERING_WINDOW_HOURS)
            hops = [
                t for t in group[i + 1:]
                if t.ts <= end and t.amount < 0]
            distinct = {t.counterparty for t in hops}
            if len(distinct) >= LAYERING_MIN_HOPS:
                ids = (
                    [inbound.txn_id]
                    + [t.txn_id for t in hops])
                alerts.append(Alert(
                    rule="layering",
                    reason=(
                        f"{len(distinct)} outbound hops "
                        f"within {LAYERING_WINDOW_HOURS}h "
                        f"of inbound {inbound.txn_id}"),
                    txn_ids=ids,
                ))
    return alerts


def check_anomaly(
    txns: list[Transaction],
    history: dict[str, list[float]],
) -> list[Alert]:
    """Flag amounts far outside an account's own past
    pattern -- a cheap, explainable z-score, no model
    training required."""
    alerts = []
    for t in txns:
        past = history.get(t.account_id, [])
        if len(past) < 5:
            continue
        mean = statistics.mean(past)
        stdev = statistics.pstdev(past) or 1.0
        z = (t.amount - mean) / stdev
        if abs(z) >= ANOMALY_Z:
            alerts.append(Alert(
                rule="anomaly",
                reason=(
                    f"amount {t.amount:,.0f} is z={z:.1f} "
                    f"against this account's own history"),
                txn_ids=[t.txn_id],
            ))
    return alerts


def sweep(
    txns: list[Transaction],
    history: dict[str, list[float]],
) -> list[Alert]:
    """Run every rule and the anomaly check, in order."""
    return (
        check_structuring(txns)
        + check_layering(txns)
        + check_anomaly(txns, history)
    )
