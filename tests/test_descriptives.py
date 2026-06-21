from __future__ import annotations

import statistics

from tkstatistics.stats import descriptives


def test_describe_basic_values():
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = descriptives.describe(data)
    assert result["n"] == 5
    assert result["missing"] == 0
    assert result["mean"] == statistics.mean(data)
    assert result["median"] == statistics.median(data)
    assert result["min"] == 1.0
    assert result["max"] == 5.0
    assert result["range"] == 4.0
    assert result["iqr"] is not None
    assert set(result["quantiles"]) == {"25% (Q1)", "50% (Median)", "75% (Q3)"}


def test_describe_handles_missing_and_nonfinite():
    data = [1.0, None, 3.0, float("nan"), float("inf"), 5.0]
    result = descriptives.describe(data)
    assert result["n"] == 6  # n reports the raw input length
    assert result["missing"] == 3  # None, nan, inf are dropped


def test_describe_single_value_does_not_crash():
    # Regression guard: statistics.quantiles raises on n<2.
    result = descriptives.describe([42.0])
    assert result["n"] == 1
    assert result["mean"] == 42.0
    assert result["stdev"] == 0.0
    assert result["iqr"] is None
    assert result["quantiles"] == {}


def test_describe_all_missing():
    result = descriptives.describe([None, None])
    assert result["mean"] is None
    assert result["missing"] == 2


def test_frequency_table_counts():
    table = descriptives.frequency_table(["a", "b", "a", None, "b", "a"])
    assert table["a"] == 3
    assert table["b"] == 2
    assert table["Missing"] == 1
