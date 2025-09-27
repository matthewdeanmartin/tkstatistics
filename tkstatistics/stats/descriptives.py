# tkstatistics/stats/descriptives.py

"""
Calculates descriptive statistics for a list of numerical data.
"""
from __future__ import annotations

import math
import statistics
from collections import Counter
from typing import Any, Union

Numeric = Union[int, float]


def describe(data: list[Numeric | None]) -> dict[str, Any]:
    """
    Computes a comprehensive set of descriptive statistics for a sample.
    Handles missing values (None) gracefully.
    """
    # Filter out missing values for calculations
    clean_data = [x for x in data if x is not None and math.isfinite(x)]

    if not clean_data:
        return {
            "n": len(data),
            "missing": len(data),
            "mean": None,
            "median": None,
            "mode": [],
            "stdev": None,
            "variance": None,
            "min": None,
            "max": None,
            "range": None,
            "iqr": None,
            "quantiles": {},
        }

    n = len(clean_data)

    # Use statistics module where possible
    mean = statistics.mean(clean_data)
    median = statistics.median(clean_data)

    try:
        modes = statistics.multimode(clean_data)
    except statistics.StatisticsError:
        modes = []  # No unique mode

    stdev = statistics.stdev(clean_data) if n > 1 else 0.0
    variance = statistics.variance(clean_data) if n > 1 else 0.0

    min_val = min(clean_data)
    max_val = max(clean_data)

    # Quantiles
    q = statistics.quantiles(clean_data, n=4)  # q[0]=Q1, q[1]=Q2, q[2]=Q3
    iqr = q[2] - q[0]

    return {
        "n": len(data),
        "missing": len(data) - n,
        "mean": mean,
        "median": median,
        "mode": modes,
        "stdev": stdev,
        "variance": variance,
        "min": min_val,
        "max": max_val,
        "range": max_val - min_val,
        "iqr": iqr,
        "quantiles": {
            "25% (Q1)": q[0],
            "50% (Median)": q[1],
            "75% (Q3)": q[2],
        },
    }


def frequency_table(data: list[Any]) -> dict[str, int]:
    """Generates a frequency count for categorical data."""
    return dict(Counter(str(x) if x is not None else "Missing" for x in data))
