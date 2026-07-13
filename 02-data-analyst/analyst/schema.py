# analyst/schema.py
from __future__ import annotations

import sys

import duckdb

TABLE = "rides"


def build_db(csv_path: str, db_path: str) -> None:
    """One-time ETL: load a CSV into a real table."""
    con = duckdb.connect(db_path)
    con.execute(
        f"CREATE OR REPLACE TABLE {TABLE} AS "
        "SELECT * FROM read_csv_auto(?, "
        "sample_size=-1)", [csv_path])
    n = con.execute(
        f"SELECT count(*) FROM {TABLE}").fetchone()[0]
    con.close()
    print(f"Loaded {n:,} rows into {db_path}::{TABLE}")


def describe_schema(
        con: duckdb.DuckDBPyConnection) -> str:
    """Build a compact, prompt-ready schema summary."""
    cols = con.execute(f"DESCRIBE {TABLE}").fetchall()
    n_rows = con.execute(
        f"SELECT count(*) FROM {TABLE}").fetchone()[0]
    sample = con.execute(
        f"SELECT * FROM {TABLE} LIMIT 3").fetchdf()

    lines = [f"Table `{TABLE}` ({n_rows:,} rows)."]
    lines.append("Columns:")
    for name, col_type, *_ in cols:
        lines.append(f"  - {name}: {col_type}")
    lines.append("Sample rows:")
    lines.append(sample.to_string(index=False))
    return "\n".join(lines)


if __name__ == "__main__":
    build_db(sys.argv[1], sys.argv[2])
