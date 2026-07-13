# analyst/runner.py
from __future__ import annotations

import os
import threading

import duckdb
import pandas as pd

ROW_CAP = int(os.getenv("ROW_CAP", "5000"))
TIMEOUT_S = float(os.getenv("QUERY_TIMEOUT_S", "8"))


class SandboxError(Exception):
    """Raised when a query is rejected or fails."""


def execute(
        con: duckdb.DuckDBPyConnection, sql: str,
        row_cap: int = ROW_CAP,
        timeout_s: float = TIMEOUT_S) -> pd.DataFrame:
    """Run one vetted SELECT under a hard timeout."""
    slot: dict = {}

    def _run() -> None:
        try:
            slot["df"] = con.execute(sql).fetchdf()
        except Exception as exc:  # noqa: BLE001
            slot["error"] = exc

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    t.join(timeout_s)
    if t.is_alive():
        con.interrupt()
        raise SandboxError(
            f"Query ran past {timeout_s}s and was "
            "cancelled.")
    if "error" in slot:
        raise SandboxError(str(slot["error"]))

    df = slot["df"]
    if len(df) > row_cap:
        df = df.head(row_cap).copy()
        df.attrs["truncated"] = True
    return df
