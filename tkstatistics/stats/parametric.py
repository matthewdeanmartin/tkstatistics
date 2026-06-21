from __future__ import annotations

import math
import statistics
from typing import Any

from .distributions import regularized_incomplete_beta, student_t_cdf, student_t_ppf

# Backwards-compatible private aliases. The special functions now live in
# ``distributions``; these names are kept so existing tests/imports keep working.
_regularized_incomplete_beta = regularized_incomplete_beta
_student_t_cdf = student_t_cdf
_student_t_ppf = student_t_ppf


def _clean_numeric(data: list[float | int | None]) -> list[float]:
    return [float(x) for x in data if x is not None and math.isfinite(float(x))]


def ttest_1samp(
    data: list[float | int | None],
    null_mean: float = 0.0,
    alternative: str = "two-sided",
    conf_level: float = 0.95,
) -> dict[str, Any]:
    """Run a one-sample Student t-test using only stdlib math.

    The test compares a sample mean against a null/reference mean.
    """
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


def ttest_ind(
    x: list[float | int | None],
    y: list[float | int | None],
    null_diff: float = 0.0,
    alternative: str = "two-sided",
    variance_assumption: str = "welch",
    conf_level: float = 0.95,
) -> dict[str, Any]:
    """Run a two-sample t-test with Welch or pooled variance.

    `variance_assumption="welch"` does not assume equal population variances.
    It uses a separate variance estimate for each sample plus the
    Welch-Satterthwaite degrees-of-freedom adjustment. This is usually the
    safer default.

    `variance_assumption="pooled"` assumes both groups come from populations
    with the same variance, then pools them into one shared estimate.
    This can be a bit more powerful when the equal-variance assumption is
    true, but can be misleading when variances differ.
    """
    clean_x = _clean_numeric(x)
    clean_y = _clean_numeric(y)
    n1 = len(clean_x)
    n2 = len(clean_y)

    if n1 < 2 or n2 < 2:
        return {"error": "Each sample must contain at least two non-missing finite observations."}

    if alternative not in {"two-sided", "less", "greater"}:
        return {"error": "alternative must be one of: two-sided, less, greater."}

    if variance_assumption not in {"welch", "pooled"}:
        return {"error": "variance_assumption must be one of: welch, pooled."}

    if not (0.0 < conf_level < 1.0):
        return {"error": "conf_level must be between 0 and 1."}

    mean_x = statistics.mean(clean_x)
    mean_y = statistics.mean(clean_y)
    var_x = statistics.variance(clean_x)
    var_y = statistics.variance(clean_y)
    mean_diff = mean_x - mean_y

    if variance_assumption == "welch":
        a = var_x / n1
        b = var_y / n2
        se = math.sqrt(a + b)
        denom = (a * a) / (n1 - 1) + (b * b) / (n2 - 1)
        df = (a + b) * (a + b) / denom if denom > 0 else float(n1 + n2 - 2)
    else:
        pooled_var = ((n1 - 1) * var_x + (n2 - 1) * var_y) / (n1 + n2 - 2)
        se = math.sqrt(pooled_var * (1.0 / n1 + 1.0 / n2))
        df = float(n1 + n2 - 2)

    if se <= 0.0:
        if mean_diff == null_diff:
            t_stat = 0.0
            p_value = 1.0
        else:
            t_stat = math.inf if mean_diff > null_diff else -math.inf
            if alternative == "two-sided":
                p_value = 0.0
            elif alternative == "greater":
                p_value = 0.0 if t_stat > 0 else 1.0
            else:
                p_value = 0.0 if t_stat < 0 else 1.0
        ci_low = mean_diff
        ci_high = mean_diff
    else:
        t_stat = (mean_diff - null_diff) / se
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
        ci_low = mean_diff - margin
        ci_high = mean_diff + margin

    cohen_d = None
    if variance_assumption == "pooled":
        pooled_sd = math.sqrt(((n1 - 1) * var_x + (n2 - 1) * var_y) / (n1 + n2 - 2))
        if pooled_sd > 0:
            cohen_d = (mean_diff - null_diff) / pooled_sd

    return {
        "test": "Independent Two-Sample t-test",
        "variant": variance_assumption,
        "n1": n1,
        "n2": n2,
        "df": df,
        "mean_x": mean_x,
        "mean_y": mean_y,
        "mean_difference": mean_diff,
        "null_difference": null_diff,
        "alternative": alternative,
        "t_statistic": t_stat,
        "p_value": max(0.0, min(1.0, p_value)),
        "std_error": se,
        "var_x": var_x,
        "var_y": var_y,
        "cohen_d": cohen_d,
        "conf_level": conf_level,
        "confidence_interval": [ci_low, ci_high],
    }
