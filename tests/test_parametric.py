from __future__ import annotations

from tkstatistics.stats import parametric


def test_ttest_1samp_returns_expected_null_result_for_centered_data():
    result = parametric.ttest_1samp([8, 9, 10, 11, 12], null_mean=10)

    assert result["test"] == "One-Sample Student t-test"
    assert result["n"] == 5
    assert result["df"] == 4
    assert abs(result["t_statistic"]) < 1e-12
    assert abs(result["p_value"] - 1.0) < 1e-12


def test_ttest_1samp_one_sided_p_value_is_reasonable():
    result = parametric.ttest_1samp([10, 11, 12, 13, 14], null_mean=10, alternative="greater")

    assert result["t_statistic"] > 2.8
    assert 0.02 < result["p_value"] < 0.03
