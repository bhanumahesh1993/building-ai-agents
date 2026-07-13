# tests/test_critic.py
from __future__ import annotations

import pandas as pd

from analyst import critic


def test_empty_result_warns():
    report = critic.check(pd.DataFrame())
    assert not report.clean
    assert "zero rows" in report.warnings[0]


def test_truncated_result_warns():
    df = pd.DataFrame({"a": [1, 2, 3]})
    df.attrs["truncated"] = True
    report = critic.check(df)
    assert any("truncated" in w for w in report.warnings)


def test_high_null_fraction_warns():
    df = pd.DataFrame({"value": [1, None, None, None]})
    report = critic.check(df)
    assert any("null" in w for w in report.warnings)


def test_seconds_over_a_day_warns():
    df = pd.DataFrame({"trip_s": [10, 20, 100_000]})
    report = critic.check(df)
    assert any("check the units" in w for w in report.warnings)


def test_minutes_over_a_day_warns():
    df = pd.DataFrame({"trip_min": [10, 20, 2_000]})
    report = critic.check(df)
    assert any("check the units" in w for w in report.warnings)


def test_clean_data_has_no_warnings():
    df = pd.DataFrame({"trip_s": [10, 20, 30], "count": [1, 2, 3]})
    report = critic.check(df)
    assert report.clean
    assert report.warnings == []
