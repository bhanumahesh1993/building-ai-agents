# tests/test_sql_agent.py
from __future__ import annotations

import pytest
from pydantic import ValidationError

from analyst.sql_agent import SQLQuery


def test_select_is_allowed():
    q = SQLQuery(sql="SELECT 1", intent="sanity check")
    assert q.sql == "SELECT 1"


def test_with_select_is_allowed():
    q = SQLQuery(
        sql="WITH t AS (SELECT 1 AS n) SELECT * FROM t",
        intent="cte sanity check",
    )
    assert q.sql.lower().startswith("with")


@pytest.mark.parametrize("bad_sql", [
    "DROP TABLE rides",
    "DELETE FROM rides",
    "UPDATE rides SET x = 1",
    "ALTER TABLE rides ADD COLUMN x INT",
    "PRAGMA table_info(rides)",
    "COPY rides TO 'out.csv'",
])
def test_ddl_dml_is_rejected(bad_sql):
    with pytest.raises(ValidationError):
        SQLQuery(sql=bad_sql, intent="malicious")


def test_non_select_head_is_rejected():
    with pytest.raises(ValidationError):
        SQLQuery(sql="EXPLAIN SELECT 1", intent="not a select")


@pytest.mark.parametrize("bad_sql", [
    "SELECT * FROM read_csv('secrets.csv')",
    "SELECT * FROM read_parquet('s3://bucket/x.parquet')",
    "ATTACH 'other.duckdb' AS other",
    "SELECT * FROM glob('*.csv')",
])
def test_banned_file_functions_are_rejected(bad_sql):
    with pytest.raises(ValidationError):
        SQLQuery(sql=bad_sql, intent="tries to read files")


def test_default_chart_kind_is_none():
    q = SQLQuery(sql="SELECT 1", intent="sanity check")
    assert q.chart_kind == "none"
