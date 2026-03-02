from __future__ import annotations


def bonferroni_correction(p_values: list[float], alpha: float = 0.05) -> list[float]:
    """Returns adjusted p-values: min(p * m, 1.0) per test."""
    m = len(p_values)
    if m == 0:
        return []
    return [min(p * m, 1.0) for p in p_values]


def holm_bonferroni_correction(p_values: list[float], alpha: float = 0.05) -> list[float]:
    """Step-down FWER correction. Returns adjusted p-values in input order.

    Algorithm: sort ascending, compute cumulative max of (m-rank)*p, clamp to [0,1],
    then re-map back to original positions.
    """
    m = len(p_values)
    if m == 0:
        return []
    indexed = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted_sorted = [0.0] * m
    running_max = 0.0
    for rank_zero, (orig_idx, p) in enumerate(indexed):
        factor = m - rank_zero  # = m - rank + 1 (1-indexed)
        running_max = max(running_max, factor * p)
        adjusted_sorted[rank_zero] = min(running_max, 1.0)
    result = [0.0] * m
    for rank_zero, (orig_idx, _) in enumerate(indexed):
        result[orig_idx] = adjusted_sorted[rank_zero]
    return result
