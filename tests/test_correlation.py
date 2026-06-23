from __future__ import annotations

import math

import pytest

from tkstatistics.stats import correlation

scipy_stats = pytest.importorskip("scipy.stats")


def test_pearson_matrix_matches_scipy():
    a = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    b = [2.1, 3.9, 6.2, 7.8, 10.1, 12.2]
    c = [5.0, 3.0, 6.0, 2.0, 8.0, 1.0]

    res = correlation.correlation_matrix([a, b, c], names=["a", "b", "c"], method="pearson")

    series = [a, b, c]
    for i in range(3):
        for j in range(3):
            if i == j:
                assert res["correlations"][i][j] == pytest.approx(1.0)
                continue
            ref = scipy_stats.pearsonr(series[i], series[j])
            assert math.isclose(res["correlations"][i][j], float(ref.statistic), rel_tol=1e-9)
            assert math.isclose(res["p_values"][i][j], float(ref.pvalue), rel_tol=1e-7, abs_tol=1e-12)


def test_spearman_matrix_matches_scipy():
    a = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    b = [2.0, 1.0, 4.0, 3.0, 6.0, 5.0, 8.0]

    res = correlation.correlation_matrix([a, b], method="spearman")

    ref = scipy_stats.spearmanr(a, b)
    assert math.isclose(res["correlations"][0][1], float(ref.correlation), rel_tol=1e-9)
    assert math.isclose(res["p_values"][0][1], float(ref.pvalue), rel_tol=1e-6, abs_tol=1e-10)


def test_matrix_is_symmetric_and_labelled():
    res = correlation.correlation_matrix([[1.0, 2.0, 3.0], [3.0, 2.0, 1.0]])
    assert res["names"] == ["var1", "var2"]
    assert res["correlations"][0][1] == res["correlations"][1][0]
    assert res["correlations"][0][1] == pytest.approx(-1.0)


def test_correlation_validates_inputs():
    assert "error" in correlation.correlation_matrix([[1.0, 2.0]])
    assert "error" in correlation.correlation_matrix([[1.0], [2.0]], method="kendall")
    assert "error" in correlation.correlation_matrix([[1.0], [2.0]], names=["only_one"])


def test_pairwise_complete_handles_missing():
    a = [1.0, 2.0, None, 4.0, 5.0]
    b = [2.0, None, 6.0, 8.0, 10.0]
    res = correlation.correlation_matrix([a, b])
    # Only indices 0, 3, 4 are complete for both -> n = 3.
    assert res["n"][0][1] == 3
