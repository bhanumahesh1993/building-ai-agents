# analyst/charts.py
from __future__ import annotations

import uuid
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

OUT_DIR = Path("charts")
OUT_DIR.mkdir(exist_ok=True)


def _bar(df: pd.DataFrame, ax) -> None:
    x, y = df.columns[0], df.columns[1]
    ax.bar(df[x].astype(str), df[y])
    ax.tick_params(axis="x", rotation=45)


def _line(df: pd.DataFrame, ax) -> None:
    x, y = df.columns[0], df.columns[1]
    ax.plot(df[x], df[y], marker="o")


def _hist(df: pd.DataFrame, ax) -> None:
    ax.hist(df[df.columns[0]].dropna(), bins=30)


def _scatter(df: pd.DataFrame, ax) -> None:
    x, y = df.columns[0], df.columns[1]
    ax.scatter(df[x], df[y], alpha=0.5, s=8)


_KINDS = {
    "bar": _bar, "line": _line,
    "hist": _hist, "scatter": _scatter,
}


def render(
        df: pd.DataFrame, kind: str,
        title: str) -> str | None:
    """Draw one of four fixed chart shapes to a file."""
    fn = _KINDS.get(kind)
    if fn is None or df.empty:
        return None
    fig, ax = plt.subplots(figsize=(6, 4))
    fn(df, ax)
    ax.set_title(title, fontsize=10)
    fig.tight_layout()
    path = OUT_DIR / f"{uuid.uuid4().hex[:8]}.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return str(path)
