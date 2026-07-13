# evals/backtest.py
from __future__ import annotations

import json

from firm.data import get_ohlcv
from firm.graph import build_graph
from langgraph.types import Command


def _next_return(symbol: str, as_of: str) -> float:
    """One bar past as_of, for a synthetic mark-to-market.
    Research diagnostic only — see the chapter's caveats."""
    bars = get_ohlcv(symbol, as_of, lookback=2)
    if len(bars) < 2:
        return 0.0
    a, b = bars[-2]["close"], bars[-1]["close"]
    return (b - a) / a


def run_backtest(symbol: str, dates: list[str]) -> dict:
    """Research-only walk over historical dates. NOT a live
    strategy evaluation — see the chapter's caveats."""
    graph = build_graph()
    fills = []
    for i, as_of in enumerate(dates):
        cfg = {"configurable": {"thread_id": f"{symbol}-{i}"}}
        state = graph.invoke({
            "symbol": symbol, "as_of": as_of,
            "debate_round": 0, "max_debate_rounds": 2,
            "risk_revisions": 0, "max_risk_revisions": 1,
        }, config=cfg)
        if "__interrupt__" in state:
            state = graph.invoke(
                Command(resume={"confirmed": True}),
                config=cfg)
        fill = state["paper_fill"]
        r = _next_return(symbol, as_of)
        signed = r if fill["action"] == "BUY" else (
            -r if fill["action"] == "SELL" else 0.0)
        fills.append({
            **fill, "as_of": as_of, "next_bar_return": signed,
        })
    return {"symbol": symbol, "fills": fills}


if __name__ == "__main__":
    dates = ["2026-01-05", "2026-02-05", "2026-03-05"]
    print(json.dumps(run_backtest("SYNTH", dates), indent=2))
