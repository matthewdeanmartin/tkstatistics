# tkstatistics/stats/correlation.py

"""
Correlation matrices (Pearson and Spearman) with per-pair p-values.

Both methods use the Student-t distribution from
:mod:`tkstatistics.stats.distributions` to turn each pairwise correlation
coefficient into a two-sided p-value, so no external dependency is required.
Spearman's rho is computed as the Pearson correlation of the rank-transformed
data, which matches scipy's default (average-rank) behaviour.
"""

from __future__ import annotations

import math
import statistics
from typing import Any

from .distributions import student_t_cdf
from .nonparametric import _rank_data

Numeric = int | float


def _pairwise_complete(a: list[Numeric | None], b: list[Numeric | None]) -> tuple[list[float], list[float]]:
    """Keep only index positions where both series are present and finite."""
    out_a: list[float] = []
    out_b: list[float] = []
    for xi, yi in zip(a, b, strict=False):
        if xi is None or yi is None:
            continue
        fx, fy = float(xi), float(yi)
        if math.isfinite(fx) and math.isfinite(fy):
            out_a.append(fx)
            out_b.append(fy)
    return out_a, out_b


def _pearson_r(x: list[float], y: list[float]) -> float | None:
    """Pearson correlation coefficient, or None if undefined (zero variance)."""
    n = len(x)
    if n < 2:
        return None
    mean_x = statistics.mean(x)
    mean_y = statistics.mean(y)
    sxy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y, strict=True))
    sxx = sum((xi - mean_x) ** 2 for xi in x)
    syy = sum((yi - mean_y) ** 2 for yi in y)
    denom = math.sqrt(sxx * syy)
    if denom <= 0.0:
        return None
    r = sxy / denom
    # Guard against tiny floating-point excursions beyond [-1, 1].
    return max(-1.0, min(1.0, r))


def _r_to_p(r: float, n: int) -> float | None:
    """Two-sided p-value for a correlation r from n observations (t-test)."""
    df = n - 2
    if df <= 0:
        return None
    if abs(r) >= 1.0:
        return 0.0
    t_stat = r * math.sqrt(df / (1.0 - r * r))
    cdf = student_t_cdf(t_stat, df)
    p = 2.0 * min(cdf, 1.0 - cdf)
    return max(0.0, min(1.0, p))


def correlation_matrix(
    columns: list[list[Numeric | None]],
    names: list[str] | None = None,
    method: str = "pearson",
) -> dict[str, Any]:
    """Compute a Pearson or Spearman correlation matrix with p-values.

    Args:
        columns: A list of numeric series, one per variable.
        names: Optional variable names; defaults to ``var1``, ``var2``, ...
        method: ``"pearson"`` or ``"spearman"``.

    Returns:
        A dictionary with the symmetric ``correlations`` matrix, the matching
        ``p_values`` matrix (diagonal p-values are ``None``), the pairwise
        complete sample size ``n`` per cell, and the variable ``names``.
    """
    if method not in {"pearson", "spearman"}:
        return {"error": "method must be one of: pearson, spearman."}
    if not isinstance(columns, (list, tuple)) or len(columns) < 2:
        return {"error": "At least two variables are required for a correlation matrix."}

    m = len(columns)
    if names is None:
        names = [f"var{i + 1}" for i in range(m)]
    elif len(names) != m:
        return {"error": "Length of names must match the number of columns."}

    corr: list[list[float | None]] = [[None] * m for _ in range(m)]
    pvals: list[list[float | None]] = [[None] * m for _ in range(m)]
    counts: list[list[int]] = [[0] * m for _ in range(m)]

    for i in range(m):
        for j in range(i, m):
            xi, xj = _pairwise_complete(columns[i], columns[j])
            n = len(xi)
            counts[i][j] = counts[j][i] = n

            if i == j:
                corr[i][j] = 1.0 if n >= 1 else None
                continue

            if method == "spearman":
                xi, xj = _rank_data(xi), _rank_data(xj)

            r = _pearson_r(xi, xj)
            corr[i][j] = corr[j][i] = r
            if r is not None:
                p = _r_to_p(r, n)
                pvals[i][j] = pvals[j][i] = p

    return {
        "test": f"{method.capitalize()} correlation matrix",
        "method": method,
        "names": list(names),
        "correlations": corr,
        "p_values": pvals,
        "n": counts,
    }
