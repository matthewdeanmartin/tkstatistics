# tkstatistics/stats/nonparametric.py

"""
Implementations of nonparametric statistical tests using only stdlib.
"""
from __future__ import annotations

import math
from typing import Any, Union

Numeric = Union[int, float]


def _rank_data(data: list[Numeric], tie_method: str = "average") -> list[float]:
    """Helper to rank data, handling ties."""
    sorted_pairs = sorted(enumerate(data), key=lambda x: x[1])
    ranks = [0.0] * len(data)
    i = 0
    while i < len(sorted_pairs):
        j = i
        # Find all ties from current position
        while j < len(sorted_pairs) - 1 and sorted_pairs[j][1] == sorted_pairs[j + 1][1]:
            j += 1

        # Assign rank for the tied group
        if i == j:  # No ties
            ranks[sorted_pairs[i][0]] = i + 1
        else:  # Ties found
            rank_sum = sum(range(i + 1, j + 2))
            avg_rank = rank_sum / (j - i + 1)
            for k in range(i, j + 1):
                ranks[sorted_pairs[k][0]] = avg_rank
        i = j + 1
    return ranks


def mann_whitney_u(x: list[Numeric], y: list[Numeric]) -> dict[str, Any]:
    """
    Performs the Mann-Whitney U test for two independent samples.

    Returns U statistic, effect size (rank-biserial correlation),
    and an approximate p-value using normal approximation.
    """
    n1, n2 = len(x), len(y)
    if n1 == 0 or n2 == 0:
        return {"error": "Input samples cannot be empty."}

    combined = x + y
    ranks = _rank_data(combined)

    rank_sum_x = sum(ranks[:n1])

    u1 = rank_sum_x - (n1 * (n1 + 1)) / 2
    u2 = (n1 * n2) - u1
    u_stat = min(u1, u2)

    # Effect size: Rank-Biserial Correlation
    rb_corr = 1 - (2 * u_stat) / (n1 * n2)

    # Normal approximation for p-value (for larger samples)
    mean_u = (n1 * n2) / 2
    std_u = math.sqrt((n1 * n2 * (n1 + n2 + 1)) / 12)

    if std_u == 0:
        p_value = 1.0 if u_stat > mean_u else 0.0
    else:
        z = (u_stat - mean_u) / std_u
        # Use math.erf to get two-tailed p-value from z-score
        p_value = math.erf(abs(z) / math.sqrt(2.0))
        p_value = 1.0 - p_value

    return {
        "test": "Mann-Whitney U Test",
        "u_statistic": u_stat,
        "n1": n1,
        "n2": n2,
        "effect_size_rank_biserial": rb_corr,
        "p_value_approx": p_value,
        "notes": "P-value is based on a normal distribution approximation.",
    }


def wilcoxon_signed_rank(x: list[Numeric], y: list[Numeric]) -> dict[str, Any]:
    """
    Performs the Wilcoxon signed-rank test for two related, paired samples.
    """
    if len(x) != len(y):
        return {"error": "Paired samples must have the same length."}

    diffs = [xi - yi for xi, yi in zip(x, y, strict=False) if xi != yi]
    if not diffs:
        return {
            "test": "Wilcoxon Signed-Rank Test",
            "w_statistic": 0,
            "n": 0,
            "p_value_approx": 1.0,
            "notes": "All pairs were identical.",
        }

    abs_diffs = [abs(d) for d in diffs]
    ranks = _rank_data(abs_diffs)

    w_plus = sum(r for d, r in zip(diffs, ranks, strict=False) if d > 0)
    w_minus = sum(r for d, r in zip(diffs, ranks, strict=False) if d < 0)
    w_stat = min(w_plus, w_minus)
    n = len(diffs)

    # Normal approximation for p-value
    mean_w = n * (n + 1) / 4
    std_w = math.sqrt(n * (n + 1) * (2 * n + 1) / 24)

    if std_w == 0:
        p_value = 1.0 if w_stat > mean_w else 0.0
    else:
        z = (w_stat - mean_w) / std_w
        p_value = 1.0 - math.erf(abs(z) / math.sqrt(2.0))

    return {
        "test": "Wilcoxon Signed-Rank Test",
        "w_statistic": w_stat,
        "n_pairs": n,
        "sum_ranks_positive": w_plus,
        "sum_ranks_negative": w_minus,
        "p_value_approx": p_value,
        "notes": "P-value is based on a normal distribution approximation.",
    }


def fisher_exact_2x2(table: list[list[int]]) -> dict[str, Any]:
    """
    Performs Fisher's exact test on a 2x2 contingency table.
    Calculates an exact p-value.

    Args:
        table: A list of lists, e.g., [[a, b], [c, d]]
    """
    if len(table) != 2 or len(table[0]) != 2 or len(table[1]) != 2:
        return {"error": "Table must be 2x2."}

    a, b = table[0]
    c, d = table[1]
    n = a + b + c + d

    def hypergeom_prob(a, b, c, d):
        n = a + b + c + d
        num = math.factorial(a + b) * math.factorial(c + d) * math.factorial(a + c) * math.factorial(b + d)
        den = math.factorial(n) * math.factorial(a) * math.factorial(b) * math.factorial(c) * math.factorial(d)
        return num / den

    p_observed = hypergeom_prob(a, b, c, d)
    p_sum = 0.0

    # Iterate through all possible tables with the same marginals
    row1_sum = a + b
    col1_sum = a + c

    for i in range(max(0, row1_sum + col1_sum - n), min(row1_sum, col1_sum) + 1):
        new_a = i
        new_b = row1_sum - new_a
        new_c = col1_sum - new_a
        new_d = n - row1_sum - col1_sum + new_a

        if new_b >= 0 and new_c >= 0 and new_d >= 0:
            p = hypergeom_prob(new_a, new_b, new_c, new_d)
            if p <= p_observed:
                p_sum += p

    return {
        "test": "Fisher's Exact Test (2x2)",
        "p_value_exact": p_sum,
        "notes": "P-value is exact for a two-sided test.",
    }
