# tkstatistics/stats/regression.py

"""
Simple and Multiple Linear Regression using Ordinary Least Squares (OLS).
Includes a from-scratch implementation for multiple regression and a wrapper
for the stdlib's simple linear regression function.
"""
from __future__ import annotations

import math
import statistics
from typing import Any

from . import linalg_small
from .distributions import student_t_cdf, student_t_ppf


def _coef_inference(
    coeffs: list[float],
    se_coeffs: list[float | None],
    df_residual: int,
    conf_level: float = 0.95,
) -> tuple[list[float | None], list[float | None], list[list[float] | None]]:
    """Compute two-sided p-values, t-statistics, and CIs for coefficients.

    Returns ``(t_statistics, p_values, conf_intervals)``. Entries are ``None``
    when the standard error is unavailable or the residual dof is non-positive.
    """
    t_stats: list[float | None] = []
    p_values: list[float | None] = []
    conf_intervals: list[list[float] | None] = []

    t_crit = None
    if df_residual > 0:
        t_crit = student_t_ppf(1.0 - (1.0 - conf_level) / 2.0, df_residual)

    for coef, se in zip(coeffs, se_coeffs, strict=False):
        if se is None or se <= 0.0 or not math.isfinite(se) or df_residual <= 0:
            t_stats.append(None)
            p_values.append(None)
            conf_intervals.append(None)
            continue
        t_stat = coef / se
        cdf = student_t_cdf(t_stat, df_residual)
        p_value = 2.0 * min(cdf, 1.0 - cdf)
        p_value = max(0.0, min(1.0, p_value))
        margin = t_crit * se if t_crit is not None else None
        t_stats.append(t_stat)
        p_values.append(p_value)
        conf_intervals.append([coef - margin, coef + margin] if margin is not None else None)

    return t_stats, p_values, conf_intervals


def stdlib_simple_regression(x: list[float], y: list[float]) -> dict[str, Any]:
    """
    Performs Simple Linear Regression using `statistics.linear_regression`.

    This function is limited to a single independent variable. It calculates
    additional statistics (R-squared, SE, t-stats) to provide an output
    consistent with the main `ols` function.

    Args:
        x: A list of the independent (predictor) variable.
        y: A list of the dependent (response) variable.

    Returns:
        A dictionary with regression results.
    """
    if len(x) != len(y):
        return {"error": "Input lists x and y must have the same length."}
    if len(x) < 2:
        return {"error": "At least two data points are required for regression."}

    try:
        slope, intercept = statistics.linear_regression(x, y)
    except statistics.StatisticsError as e:
        return {"error": "Could not compute regression.", "details": str(e)}

    n = len(y)
    p = 2  # Number of parameters (intercept, slope)

    # Calculate R-squared
    y_pred = [(intercept + slope * xi) for xi in x]
    residuals = [yi - y_hat for yi, y_hat in zip(y, y_pred, strict=False)]
    ss_residual = sum(r**2 for r in residuals)
    y_mean = statistics.mean(y)
    ss_total = sum((yi - y_mean) ** 2 for yi in y)
    r_squared = 1 - (ss_residual / ss_total) if ss_total > 1e-12 else 1.0
    adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p) if (n - p) > 0 else 0.0

    # Calculate standard errors and t-stats
    if n > p:
        mse = ss_residual / (n - p)
        x_mean = statistics.mean(x)
        ss_x = sum((xi - x_mean) ** 2 for xi in x)

        se_intercept = math.sqrt(mse * (1 / n + x_mean**2 / ss_x)) if ss_x > 1e-12 else float("inf")
        se_slope = math.sqrt(mse / ss_x) if ss_x > 1e-12 else float("inf")
    else:
        se_intercept, se_slope = (None, None)

    df_residual = n - p
    t_stats, p_values, conf_intervals = _coef_inference(
        [intercept, slope], [se_intercept, se_slope], df_residual
    )

    return {
        "coefficients": [intercept, slope],
        "std_errors": [se_intercept, se_slope],
        "t_statistics": t_stats,
        "p_values": p_values,
        "conf_level": 0.95,
        "confidence_intervals": conf_intervals,
        "r_squared": r_squared,
        "adj_r_squared": adj_r_squared,
        "n": n,
        "df_model": p - 1,
        "df_residual": df_residual,
        "notes": "Uses statistics.linear_regression with a from-scratch t-distribution for inference.",
    }


def ols(X: list[list[float]], y: list[float], add_intercept: bool = True) -> dict[str, Any]:
    """
    Performs Ordinary Least Squares (OLS) regression.

    Args:
        X: A list of lists, where each inner list is a row of predictor variables.
        y: A list of the response variable.
        add_intercept: If True, a constant term (intercept) is added to the model.

    Returns:
        A dictionary with regression results including coefficients, standard errors,
        t-statistics, and R-squared. P-values and confidence intervals are noted
        as requiring a t-distribution CDF, which is beyond stdlib.
    """
    if len(X) != len(y):
        return {"error": "Number of rows in X must equal length of y."}

    n = len(y)
    X_design = [list(row) for row in X]  # Create a mutable copy

    if add_intercept:
        for i in range(n):
            X_design[i].insert(0, 1.0)

    p = len(X_design[0])
    if n <= p:
        return {"error": "Number of observations must be greater than number of predictors."}

    try:
        # Core OLS calculation: beta = (X'X)^-1 * X'y
        XT = linalg_small.transpose(X_design)
        XTX = linalg_small.matmul(XT, X_design)
        XTX_inv = linalg_small.invert(XTX)
        XTy = linalg_small.matvec_mul(XT, y)
        coeffs = linalg_small.matvec_mul(XTX_inv, XTy)
    except ValueError as e:
        return {
            "error": "Failed to solve regression.",
            "details": str(e),
            "notes": "This may be due to perfect multicollinearity in predictors.",
        }

    # Predictions and residuals
    y_pred = linalg_small.matvec_mul(X_design, coeffs)
    residuals = [y_true - y_hat for y_true, y_hat in zip(y, y_pred, strict=False)]

    # Sums of squares and R-squared
    ss_residual = sum(r**2 for r in residuals)
    y_mean = statistics.mean(y)
    ss_total = sum((yi - y_mean) ** 2 for yi in y)
    # which is correct?!
    # r_squared = 1 - (ss_residual / ss_total) if ss_total > 0 else 0.0
    r_squared = 1 - (ss_residual / ss_total) if ss_total > 1e-12 else 1.0
    # adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p)
    adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - p) if (n - p) > 0 else 0.0

    # Standard errors and t-statistics
    df_residual = n - p
    mse = ss_residual / df_residual  # Mean Squared Error
    se_coeffs = [math.sqrt(mse * XTX_inv[i][i]) for i in range(p)]
    t_stats, p_values, conf_intervals = _coef_inference(coeffs, se_coeffs, df_residual)

    return {
        "coefficients": coeffs,
        "std_errors": se_coeffs,
        "t_statistics": t_stats,
        "p_values": p_values,
        "conf_level": 0.95,
        "confidence_intervals": conf_intervals,
        "r_squared": r_squared,
        "adj_r_squared": adj_r_squared,
        "n": n,
        "df_model": p - 1,
        "df_residual": df_residual,
        "notes": "Coefficient inference uses a from-scratch Student-t distribution (stdlib only).",
    }
