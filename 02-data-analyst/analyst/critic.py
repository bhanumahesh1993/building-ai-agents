# analyst/critic.py
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

DAY_SECONDS = 86_400
DAY_MINUTES = 1_440


@dataclass
class CriticReport:
    warnings: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.warnings


def _unit_issue(col: str, mx: float) -> str | None:
    lc = col.lower()
    if lc.endswith(("_s", "seconds")) and (
            mx > DAY_SECONDS):
        return (f"`{col}` has values over a day's "
                "worth of seconds — check the units.")
    if lc.endswith(("_min", "minutes")) and (
            mx > DAY_MINUTES):
        return (f"`{col}` has values over a day's "
                "worth of minutes — check the units.")
    return None


def check(df: pd.DataFrame) -> CriticReport:
    """Cheap, deterministic sanity checks. No LLM call."""
    report = CriticReport()
    if df.empty:
        report.warnings.append(
            "Query returned zero rows.")
        return report

    if df.attrs.get("truncated"):
        report.warnings.append(
            f"Result truncated to {len(df)} rows — the "
            "full answer may cover more data than shown.")

    numeric = df.select_dtypes(include="number")
    for col in numeric.columns:
        null_frac = df[col].isna().mean()
        if null_frac > 0.3:
            report.warnings.append(
                f"`{col}` is {null_frac:.0%} null — any "
                "average here rests on thin data.")
        mx = numeric[col].max()
        if pd.notna(mx):
            issue = _unit_issue(col, float(mx))
            if issue:
                report.warnings.append(issue)
    return report
