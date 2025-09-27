# tkstatistics/stats/regression.py

"""
Simple and Multiple Linear Regression using Ordinary Least Squares (OLS).
Includes a from-scratch implementation for multiple regression and a wrapper
for the stdlib's simple linear regression function.
"""
from __future__ import annotations

import math
import statistics
from typing import Any, Dict, List

from . import linalg_small


def stdlib_simple_regression(x: List[float], y: List[float]) -> Dict[str, Any]:
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
    residuals = [yi - y_hat for yi, y_hat in zip(y, y_pred)]
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

        t_intercept = intercept / se_intercept if se_intercept not in (0, float("inf")) else 0.0
        t_slope = slope / se_slope if se_slope not in (0, float("inf")) else 0.0
    else:
        se_intercept, se_slope, t_intercept, t_slope = (None, None, None, None)

    return {
        "coefficients": [intercept, slope],
        "std_errors": [se_intercept, se_slope],
        "t_statistics": [t_intercept, t_slope],
        "r_squared": r_squared,
        "adj_r_squared": adj_r_squared,
        "n": n,
        "df_model": p - 1,
        "df_residual": n - p,
        "notes": "Uses statistics.linear_regression. P-values require a t-distribution CDF.",
    }


def ols(X: List[List[float]], y: List[float], add_intercept: bool = True) -> Dict[str, Any]:
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
    residuals = [y_true - y_hat for y_true, y_hat in zip(y, y_pred)]

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
    mse = ss_residual / (n - p)  # Mean Squared Error
    se_coeffs = [math.sqrt(mse * XTX_inv[i][i]) for i in range(p)]
    # t_stats = [coeffs[i] / se_coeffs[i] if se_coeffs[i] > 0 else 0.0 for i in range(p)]
    t_stats = [coeffs[i] / se_coeffs[i] if se_coeffs[i] > 1e-12 else 0.0 for i in range(p)]

    return {
        "coefficients": coeffs,
        "std_errors": se_coeffs,
        "t_statistics": t_stats,
        "r_squared": r_squared,
        "adj_r_squared": adj_r_squared,
        "n": n,
        "df_model": p - 1,
        "df_residual": n - p,
        "notes": "P-values and confidence intervals require a t-distribution CDF, not available in stdlib.",
    }
