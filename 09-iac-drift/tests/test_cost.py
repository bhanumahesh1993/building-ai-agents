# tests/test_cost.py
from __future__ import annotations

import json

import pytest

from crew.tools import cost_table

RESOURCES = [
    {"type": "aws_instance", "name": "web-1",
     "attrs": {"instance_type": "t3.medium"}},
    {"type": "aws_instance", "name": "web-2",
     "attrs": {"instance_type": "t3.medium"}},
    {"type": "aws_db_instance", "name": "staging-db",
     "attrs": {"instance_class": "db.t3.medium",
               "allocated_storage": 50}},
]


def test_cost_table_sums_known_instance_types():
    out = json.loads(cost_table.func(json.dumps(RESOURCES)))
    assert len(out["lines"]) == 3
    # 2 x t3.medium (30.37) + db.t3.medium (49.64) +
    # 50 GB storage (0.115/GB)
    expected = (2 * 30.37) + (49.64 + 50 * 0.115)
    assert out["total_monthly_usd"] == pytest.approx(
        expected, rel=1e-6)


def test_unknown_instance_type_falls_back_to_default():
    resources = [{"type": "aws_instance", "name": "x",
                  "attrs": {"instance_type": "bogus.type"}}]
    out = json.loads(cost_table.func(json.dumps(resources)))
    assert out["lines"][0]["monthly_usd"] == 30.0
