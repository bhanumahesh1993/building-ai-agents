# tests/test_runner.py
from __future__ import annotations

import duckdb
import pytest

from analyst import runner


@pytest.fixture
def con():
    c = duckdb.connect(":memory:")
    c.execute(
        "CREATE TABLE rides AS SELECT * FROM "
        "range(10) AS t(n)"
    )
    yield c
    c.close()


def test_execute_returns_dataframe(con):
    df = runner.execute(con, "SELECT * FROM rides")
    assert len(df) == 10
    assert not df.attrs.get("truncated")


def test_execute_truncates_to_row_cap(con):
    df = runner.execute(con, "SELECT * FROM rides", row_cap=3)
    assert len(df) == 3
    assert df.attrs.get("truncated") is True


def test_execute_raises_sandbox_error_on_bad_sql(con):
    with pytest.raises(runner.SandboxError):
        runner.execute(con, "SELECT * FROM no_such_table")
