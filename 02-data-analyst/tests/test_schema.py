# tests/test_schema.py
from __future__ import annotations

import duckdb
import pytest

from analyst import schema


@pytest.fixture
def con():
    """An in-memory connection with a tiny rides table."""
    c = duckdb.connect(":memory:")
    c.execute(
        "CREATE TABLE rides AS SELECT * FROM "
        "(VALUES (1, 'e-bike', 300), "
        "(2, 'classic', 900)) "
        "AS t(ride_id, bike_type, duration_s)"
    )
    yield c
    c.close()


def test_describe_schema_lists_table_and_row_count(con):
    out = schema.describe_schema(con)
    assert "rides" in out
    assert "2" in out


def test_describe_schema_lists_columns(con):
    out = schema.describe_schema(con)
    for col in ("ride_id", "bike_type", "duration_s"):
        assert col in out


def test_describe_schema_includes_sample_rows(con):
    out = schema.describe_schema(con)
    assert "Sample rows:" in out
    assert "e-bike" in out
