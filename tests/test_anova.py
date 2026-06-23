from __future__ import annotations

import math

import pytest

from tkstatistics.stats import parametric

scipy_stats = pytest.importorskip("scipy.stats")


def test_one_way_anova_matches_scipy():
    g1 = [25.0, 30.0, 28.0, 36.0, 29.0]
    g2 = [45.0, 55.0, 29.0, 56.0, 40.0]
    g3 = [30.0, 29.0, 33.0, 37.0, 27.0]

    ours = parametric.one_way_anova([g1, g2, g3])
    ref = scipy_stats.f_oneway(g1, g2, g3)

    assert math.isclose(ours["f_statistic"], float(ref.statistic), rel_tol=1e-9)
    assert math.isclose(ours["p_value"], float(ref.pvalue), rel_tol=1e-8, abs_tol=1e-12)
    assert ours["df_between"] == 2
    assert ours["df_within"] == 12


def test_one_way_anova_two_groups_matches_pooled_ttest_squared():
    # With two groups, F equals the square of the pooled-variance t statistic.
    x = [5.1, 4.9, 6.2, 5.5, 5.8]
    y = [6.1, 6.8, 7.0, 6.5, 7.2]

    anova = parametric.one_way_anova([x, y])
    ref = scipy_stats.f_oneway(x, y)

    assert math.isclose(anova["f_statistic"], float(ref.statistic), rel_tol=1e-9)
    assert math.isclose(anova["p_value"], float(ref.pvalue), rel_tol=1e-8, abs_tol=1e-12)


def test_one_way_anova_drops_missing_and_validates():
    assert "error" in parametric.one_way_anova([[1.0, 2.0]])
    assert "error" in parametric.one_way_anova([[1.0], []])
    # None/non-finite values are dropped per group.
    res = parametric.one_way_anova([[1.0, None, 2.0], [3.0, float("nan"), 4.0]])
    assert res["n_total"] == 4


def test_one_way_anova_skips_non_numeric_values():
    # Strings and other non-coercible values are dropped, not crashed on.
    res = parametric.one_way_anova([[1.0, "x", 2.0], [3.0, None, 4.0]])
    assert res["n_total"] == 4
    # A group left empty after cleaning yields an error, not an exception.
    err = parametric.one_way_anova([[1.0, 2.0], ["a", "b"]])
    assert "error" in err


def test_one_way_anova_eta_squared_in_unit_interval():
    res = parametric.one_way_anova([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]])
    assert 0.0 <= res["eta_squared"] <= 1.0
