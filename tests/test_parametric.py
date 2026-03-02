from __future__ import annotations

import math

import pytest

from tkstatistics.stats import parametric

scipy_stats = pytest.importorskip("scipy.stats")


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


def test_student_t_cdf_matches_scipy_reference_points():
    points = [
        (0.0, 1.0),
        (0.25, 2.0),
        (-1.75, 5.0),
        (2.5, 10.0),
        (4.0, 30.0),
    ]

    for t_value, df in points:
        expected = float(scipy_stats.t.cdf(t_value, df))
        actual = parametric._student_t_cdf(t_value, df)
        assert math.isclose(actual, expected, rel_tol=1e-8, abs_tol=1e-8)


def test_student_t_ppf_matches_scipy_reference_points():
    points = [
        (0.75, 3.0),
        (0.9, 5.0),
        (0.975, 10.0),
        (0.99, 40.0),
    ]

    for prob, df in points:
        expected = float(scipy_stats.t.ppf(prob, df))
        actual = parametric._student_t_ppf(prob, df)
        assert math.isclose(actual, expected, rel_tol=1e-8, abs_tol=1e-8)


def test_ttest_1samp_matches_scipy_for_statistic_and_pvalue():
    data = [9.0, 10.5, 11.2, 8.8, 9.7, 10.1, 10.9]
    null_mean = 10.0

    ours = parametric.ttest_1samp(data, null_mean=null_mean, alternative="two-sided")
    ref = scipy_stats.ttest_1samp(data, popmean=null_mean, alternative="two-sided")

    assert math.isclose(ours["t_statistic"], float(ref.statistic), rel_tol=1e-8, abs_tol=1e-8)
    assert math.isclose(ours["p_value"], float(ref.pvalue), rel_tol=1e-8, abs_tol=1e-8)


def test_ttest_ind_welch_matches_scipy():
    x = [2.1, 2.5, 2.8, 3.0, 2.2, 2.6]
    y = [1.0, 1.2, 1.6, 1.4, 1.1]

    ours = parametric.ttest_ind(x, y, variance_assumption="welch")
    ref = scipy_stats.ttest_ind(x, y, equal_var=False, alternative="two-sided")

    assert math.isclose(ours["t_statistic"], float(ref.statistic), rel_tol=1e-8, abs_tol=1e-8)
    assert math.isclose(ours["p_value"], float(ref.pvalue), rel_tol=1e-8, abs_tol=1e-8)


def test_ttest_ind_pooled_matches_scipy():
    x = [5.0, 5.2, 4.9, 5.3, 5.1, 5.4]
    y = [4.4, 4.5, 4.6, 4.3, 4.7]

    ours = parametric.ttest_ind(x, y, variance_assumption="pooled")
    ref = scipy_stats.ttest_ind(x, y, equal_var=True, alternative="two-sided")

    assert ours["variant"] == "pooled"
    assert math.isclose(ours["t_statistic"], float(ref.statistic), rel_tol=1e-8, abs_tol=1e-8)
    assert math.isclose(ours["p_value"], float(ref.pvalue), rel_tol=1e-8, abs_tol=1e-8)
