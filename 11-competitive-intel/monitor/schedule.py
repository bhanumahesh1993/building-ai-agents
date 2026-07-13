# monitor/schedule.py
from __future__ import annotations

import logging
import uuid

from apscheduler.schedulers.asyncio import (
    AsyncIOScheduler)
from apscheduler.triggers.cron import CronTrigger

from .graph import build_graph

logger = logging.getLogger("competi-watch.schedule")

CRON_EXPR = "0 7 * * *"   # 7 a.m. daily, server time


def run_once(min_score: int = 3) -> dict:
    """Run the full graph once, synchronously."""
    graph = build_graph()
    run_id = str(uuid.uuid4())
    cfg = {"configurable": {"thread_id": run_id}}
    state = graph.invoke(
        {"run_id": run_id, "min_score": min_score,
         "max_targets": 25},
        config=cfg,
    )
    logger.info(
        "run %s produced digest of %d chars",
        run_id, len(state.get("digest", "")))
    return state


def start_scheduler() -> AsyncIOScheduler:
    """Wire the daily cron trigger. Call once at
    process startup; keep the scheduler object alive
    for the life of the process."""
    scheduler = AsyncIOScheduler()
    trigger = CronTrigger.from_crontab(CRON_EXPR)
    scheduler.add_job(
        run_once, trigger=trigger,
        id="daily-competitor-scan",
        max_instances=1,
        misfire_grace_time=3600,
    )
    scheduler.start()
    return scheduler
