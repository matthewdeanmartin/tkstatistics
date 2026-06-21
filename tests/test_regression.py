from __future__ import annotations

import math

import pytest

from tkstatistics.stats import regression

scipy_stats = pytest.importorskip("scipy.stats")


def test_simple_regression_matches_scipy_linregress():
    x = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    y = [2.1, 3.9, 6.2, 7.8, 10.1, 12.2, 13.8]

    ours = regression.stdlib_simple_regression(x, y)
    ref = scipy_stats.linregress(x, y)

    intercept, slope = ours["coefficients"]
    assert math.isclose(slope, float(ref.slope), rel_tol=1e-9)
    assert math.isclose(intercept, float(ref.intercept), rel_tol=1e-9)
    assert math.isclose(ours["r_squared"], float(ref.rvalue) ** 2, rel_tol=1e-9)
    # scipy reports the two-sided p-value for the slope.
    assert math.isclose(ours["p_values"][1], float(ref.pvalue), rel_tol=1e-7, abs_tol=1e-9)
    assert math.isclose(ours["std_errors"][1], float(ref.stderr), rel_tol=1e-7)


def test_ols_matches_statsmodels():
    statsmodels_api = pytest.importorskip("statsmodels.api")

    rows = [
        [1.0, 2.0],
        [2.0, 1.0],
        [3.0, 4.0],
        [4.0, 3.0],
        [5.0, 5.0],
        [6.0, 4.0],
        [7.0, 8.0],
    ]
    y = [3.0, 4.0, 8.0, 9.0, 12.0, 13.0, 18.0]

    ours = regression.ols(rows, y, add_intercept=True)

    X_design = statsmodels_api.add_constant(rows)
    ref = statsmodels_api.OLS(y, X_design).fit()

    for ours_c, ref_c in zip(ours["coefficients"], ref.params, strict=True):
        assert math.isclose(ours_c, float(ref_c), rel_tol=1e-7, abs_tol=1e-9)
    for ours_se, ref_se in zip(ours["std_errors"], ref.bse, strict=True):
        assert math.isclose(ours_se, float(ref_se), rel_tol=1e-6, abs_tol=1e-9)
    for ours_p, ref_p in zip(ours["p_values"], ref.pvalues, strict=True):
        assert math.isclose(ours_p, float(ref_p), rel_tol=1e-6, abs_tol=1e-9)
    assert math.isclose(ours["r_squared"], float(ref.rsquared), rel_tol=1e-9)


def test_ols_pvalues_match_scipy_oracle():
    """Verify OLS coefficient inference against scipy without needing statsmodels.

    Builds the OLS solution with a hand-checked computation and compares the
    two-sided coefficient p-values to scipy's Student-t survival function.
    """
    rows = [[x] for x in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]]
    y = [2.0, 4.1, 5.9, 8.2, 9.8, 12.1, 13.9, 16.2]

    ours = regression.ols(rows, y, add_intercept=True)
    df_resid = ours["df_residual"]

    for coef, se, p in zip(ours["coefficients"], ours["std_errors"], ours["p_values"], strict=True):
        t_stat = coef / se
        expected_p = 2.0 * scipy_stats.t.sf(abs(t_stat), df_resid)
        assert math.isclose(p, float(expected_p), rel_tol=1e-8, abs_tol=1e-10)


def test_simple_regression_validates_lengths():
    assert "error" in regression.stdlib_simple_regression([1.0], [1.0, 2.0])
    assert "error" in regression.stdlib_simple_regression([1.0], [1.0])
