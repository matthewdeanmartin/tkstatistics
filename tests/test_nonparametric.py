from __future__ import annotations

import math

import pytest

from tkstatistics.stats import nonparametric

scipy_stats = pytest.importorskip("scipy.stats")


def test_mann_whitney_u_statistic_matches_scipy():
    x = [1.0, 3.0, 5.0, 7.0, 9.0, 11.0]
    y = [2.0, 4.0, 6.0, 8.0, 10.0]

    ours = nonparametric.mann_whitney_u(x, y)
    # scipy's U corresponds to the first sample; ours reports min(U1, U2).
    ref = scipy_stats.mannwhitneyu(x, y, alternative="two-sided")
    ref_u_min = min(float(ref.statistic), len(x) * len(y) - float(ref.statistic))

    assert ours["u_statistic"] == pytest.approx(ref_u_min)


def test_wilcoxon_statistic_matches_scipy():
    x = [125.0, 115.0, 130.0, 140.0, 140.0, 115.0, 140.0, 125.0, 140.0, 135.0]
    y = [110.0, 122.0, 125.0, 120.0, 140.0, 124.0, 123.0, 137.0, 135.0, 145.0]

    ours = nonparametric.wilcoxon_signed_rank(x, y)
    ref = scipy_stats.wilcoxon(x, y)
    assert ours["w_statistic"] == pytest.approx(float(ref.statistic))


def test_fisher_exact_2x2_matches_scipy():
    table = [[8, 2], [1, 5]]
    ours = nonparametric.fisher_exact_2x2(table)
    _, ref_p = scipy_stats.fisher_exact(table, alternative="two-sided")
    assert math.isclose(ours["p_value_exact"], float(ref_p), rel_tol=1e-9, abs_tol=1e-12)


def test_mann_whitney_drops_missing_and_nonfinite():
    x = [1.0, None, 3.0, float("nan"), 5.0]
    y = [2.0, 4.0, None, 6.0]
    ours = nonparametric.mann_whitney_u(x, y)
    assert ours["n1"] == 3
    assert ours["n2"] == 3


def test_wilcoxon_drops_incomplete_pairs():
    x = [1.0, None, 3.0, 4.0]
    y = [2.0, 5.0, None, 6.0]
    ours = nonparametric.wilcoxon_signed_rank(x, y)
    # Only the (1,2) and (4,6) pairs survive.
    assert ours["n_pairs"] == 2


def test_mann_whitney_empty_after_cleaning():
    assert "error" in nonparametric.mann_whitney_u([None, float("nan")], [1.0])
