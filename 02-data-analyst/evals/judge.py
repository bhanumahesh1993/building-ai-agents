# evals/judge.py
from __future__ import annotations

import os

import duckdb
import pandas as pd
from pydantic_ai import Agent

JUDGE_MODEL = os.getenv(
    "JUDGE_MODEL", "anthropic:claude-opus-4-5")

judge = Agent(JUDGE_MODEL, output_type=dict)

FAITHFULNESS = """Grade whether NARRATION is faithful
to RESULT. Score 1-5 (5 = fully faithful and honest
about uncertainty; 1 = invents or overstates). Return
JSON only: {{"faithfulness": n, "notes": "..."}}

Result (first rows):
{result}

Narration:
{narration}"""


def sql_correct(
        con: duckdb.DuckDBPyConnection,
        agent_sql: str, reference_sql: str,
        tol: float = 0.05) -> bool:
    """Compare the agent's result to a reference query."""
    got = con.execute(agent_sql).fetchdf()
    want = con.execute(reference_sql).fetchdf()
    if got.shape != want.shape:
        return False
    got = got.sort_values(
        got.columns[0]).reset_index(drop=True)
    want = want.sort_values(
        want.columns[0]).reset_index(drop=True)
    num_got = got.select_dtypes(include="number")
    num_want = want.select_dtypes(include="number")
    if num_got.empty:
        return got.equals(want)
    scale = num_want.abs().clip(lower=1e-9)
    diff = (num_got - num_want.values).abs()
    return bool((diff / scale <= tol).all().all())


def faithfulness(
        result: pd.DataFrame, narration: str) -> dict:
    prompt = FAITHFULNESS.format(
        result=result.head(10).to_string(index=False),
        narration=narration)
    return judge.run_sync(prompt).output
