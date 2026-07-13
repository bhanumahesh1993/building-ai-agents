# evals/run_evals.py
from __future__ import annotations

import json

import duckdb

from analyst import schema
from analyst.app import narrate, run_pipeline
from analyst.sql_agent import AnalystDeps
from .judge import faithfulness, sql_correct

DB_PATH = "data/bikeshare.duckdb"


def run() -> None:
    con = duckdb.connect(DB_PATH, read_only=True)
    deps = AnalystDeps(
        schema_context=schema.describe_schema(con))

    with open("evals/dataset.jsonl") as fh:
        cases = [json.loads(line) for line in fh]

    n_correct = 0
    for case in cases:
        pr = run_pipeline(con, deps, case["question"])
        text = narrate(case["question"], pr)
        ok = pr.query is not None and sql_correct(
            con, pr.query.sql, case["reference_sql"])
        n_correct += int(ok)
        f = faithfulness(pr.df, text)
        print(case["question"])
        print(f"  sql_correct={ok} "
              f"faithfulness={f['faithfulness']}")

    print(f"\n{n_correct}/{len(cases)} SQL-correct")
