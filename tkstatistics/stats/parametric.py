from __future__ import annotations

import math
import statistics
from typing import Any


def _clean_numeric(data: list[float | int | None]) -> list[float]:
    return [float(x) for x in data if x is not None and math.isfinite(float(x))]


def _betacf(a: float, b: float, x: float) -> float:
    max_iter = 200
    eps = 3.0e-12
    fpmin = 1.0e-30

    qab = a + b
    qap = a + 1.0
    qam = a - 1.0

    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < fpmin:
        d = fpmin
    d = 1.0 / d
    h = d

    for m in range(1, max_iter + 1):
        m2 = 2 * m

        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        h *= d * c

        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < fpmin:
            d = fpmin
        c = 1.0 + aa / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta

        if abs(delta - 1.0) < eps:
            break

    return h


def _regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0

    ln_beta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(math.log(x) * a + math.log(1.0 - x) * b + ln_beta)

    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - (front * _betacf(b, a, 1.0 - x) / b)


def _student_t_cdf(t: float, df: int) -> float:
    if df <= 0:
        raise ValueError("Degrees of freedom must be positive.")
    if t == 0.0:
        return 0.5

    x = df / (df + t * t)
    ibeta = _regularized_incomplete_beta(0.5 * df, 0.5, x)
    if t > 0:
        return 1.0 - 0.5 * ibeta
    return 0.5 * ibeta


def _student_t_ppf(prob: float, df: int) -> float:
    if not (0.0 < prob < 1.0):
        raise ValueError("Probability must be in (0, 1).")
    if df <= 0:
        raise ValueError("Degrees of freedom must be positive.")
    if prob == 0.5:
        return 0.0

    if prob < 0.5:
        return -_student_t_ppf(1.0 - prob, df)

    lo, hi = 0.0, 1.0
    while _student_t_cdf(hi, df) < prob:
        hi *= 2.0
        if hi > 1e6:
            break

    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if _student_t_cdf(mid, df) < prob:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def ttest_1samp(
    data: list[float | int | None],
    null_mean: float = 0.0,
    alternative: str = "two-sided",
    conf_level: float = 0.95,
) -> dict[str, Any]:
    clean = _clean_numeric(data)
    n = len(clean)
    if n < 2:
        return {"error": "At least two non-missing finite observations are required."}

    if alternative not in {"two-sided", "less", "greater"}:
        return {"error": "alternative must be one of: two-sided, less, greater."}

    if not (0.0 < conf_level < 1.0):
        return {"error": "conf_level must be between 0 and 1."}

    sample_mean = statistics.mean(clean)
    sample_stdev = statistics.stdev(clean)
    se = sample_stdev / math.sqrt(n)
    df = n - 1

    if se <= 0.0:
        if sample_mean == null_mean:
            t_stat = 0.0
            p_value = 1.0
        else:
            t_stat = math.inf if sample_mean > null_mean else -math.inf
            if alternative == "two-sided":
                p_value = 0.0
            elif alternative == "greater":
                p_value = 0.0 if t_stat > 0 else 1.0
            else:
                p_value = 0.0 if t_stat < 0 else 1.0
        ci_low = sample_mean
        ci_high = sample_mean
    else:
        t_stat = (sample_mean - null_mean) / se
        cdf = _student_t_cdf(t_stat, df)
        if alternative == "two-sided":
            p_value = 2.0 * min(cdf, 1.0 - cdf)
        elif alternative == "greater":
            p_value = 1.0 - cdf
        else:
            p_value = cdf

        alpha = 1.0 - conf_level
        t_crit = _student_t_ppf(1.0 - alpha / 2.0, df)
        margin = t_crit * se
        ci_low = sample_mean - margin
        ci_high = sample_mean + margin

    effect_size = None
    if sample_stdev > 0:
        effect_size = (sample_mean - null_mean) / sample_stdev

    return {
        "test": "One-Sample Student t-test",
        "n": n,
        "df": df,
        "mean": sample_mean,
        "null_mean": null_mean,
        "alternative": alternative,
        "t_statistic": t_stat,
        "p_value": max(0.0, min(1.0, p_value)),
        "std_error": se,
        "stdev": sample_stdev,
        "cohen_d": effect_size,
        "conf_level": conf_level,
        "confidence_interval": [ci_low, ci_high],
    }
