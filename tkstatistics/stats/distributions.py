# tkstatistics/stats/distributions.py

"""
Special functions and continuous-distribution CDFs/PPFs implemented with stdlib
``math`` only.

This is the single home for the numerical kernels shared across the package: the
parametric tests, the regression inference, ANOVA, and the Q-Q / normal plotting
code all draw their distribution functions from here rather than reimplementing
them. Each public function is equivalence-tested against scipy in the test suite.
"""

from __future__ import annotations

import math

__all__ = [
    "regularized_incomplete_beta",
    "student_t_cdf",
    "student_t_ppf",
    "normal_cdf",
    "normal_ppf",
    "chi2_cdf",
    "f_cdf",
]


# ---------------------------------------------------------------------------
# Incomplete beta (Lentz continued fraction) — basis for Student-t, F.
# ---------------------------------------------------------------------------


def _betacf(a: float, b: float, x: float) -> float:
    """Continued-fraction expansion for the regularized incomplete beta."""
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


def regularized_incomplete_beta(a: float, b: float, x: float) -> float:
    """Regularized incomplete beta function I_x(a, b)."""
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0

    ln_beta = math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
    front = math.exp(math.log(x) * a + math.log(1.0 - x) * b + ln_beta)

    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - (front * _betacf(b, a, 1.0 - x) / b)


# ---------------------------------------------------------------------------
# Lower regularized incomplete gamma (series + continued fraction) — chi-square.
# ---------------------------------------------------------------------------


def _lower_regularized_gamma(s: float, x: float) -> float:
    """Lower regularized incomplete gamma P(s, x)."""
    if x <= 0.0:
        return 0.0
    if s <= 0.0:
        raise ValueError("Shape parameter must be positive.")

    if x < s + 1.0:
        # Series representation.
        term = 1.0 / s
        total = term
        n = s
        for _ in range(500):
            n += 1.0
            term *= x / n
            total += term
            if abs(term) < abs(total) * 1.0e-15:
                break
        return total * math.exp(-x + s * math.log(x) - math.lgamma(s))

    # Continued fraction for the upper gamma Q(s, x); P = 1 - Q.
    fpmin = 1.0e-30
    b = x + 1.0 - s
    c = 1.0 / fpmin
    d = 1.0 / b
    h = d
    for i in range(1, 500):
        an = -i * (i - s)
        b += 2.0
        d = an * d + b
        if abs(d) < fpmin:
            d = fpmin
        c = b + an / c
        if abs(c) < fpmin:
            c = fpmin
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1.0e-15:
            break
    q = math.exp(-x + s * math.log(x) - math.lgamma(s)) * h
    return 1.0 - q


# ---------------------------------------------------------------------------
# Student's t.
# ---------------------------------------------------------------------------


def student_t_cdf(t: float, df: float) -> float:
    """Cumulative distribution function of Student's t with ``df`` dof."""
    if df <= 0:
        raise ValueError("Degrees of freedom must be positive.")
    if t == 0.0:
        return 0.5

    x = df / (df + t * t)
    ibeta = regularized_incomplete_beta(0.5 * df, 0.5, x)
    if t > 0:
        return 1.0 - 0.5 * ibeta
    return 0.5 * ibeta


def student_t_ppf(prob: float, df: float) -> float:
    """Inverse CDF (quantile) of Student's t with ``df`` dof."""
    if not (0.0 < prob < 1.0):
        raise ValueError("Probability must be in (0, 1).")
    if df <= 0:
        raise ValueError("Degrees of freedom must be positive.")
    if prob == 0.5:
        return 0.0

    if prob < 0.5:
        return -student_t_ppf(1.0 - prob, df)

    lo, hi = 0.0, 1.0
    while student_t_cdf(hi, df) < prob:
        hi *= 2.0
        if hi > 1e6:
            break

    for _ in range(80):
        mid = 0.5 * (lo + hi)
        if student_t_cdf(mid, df) < prob:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------------------
# Standard normal.
# ---------------------------------------------------------------------------


def normal_cdf(z: float, mean: float = 0.0, sd: float = 1.0) -> float:
    """CDF of the normal distribution, using the error function."""
    if sd <= 0:
        raise ValueError("Standard deviation must be positive.")
    return 0.5 * (1.0 + math.erf((z - mean) / (sd * math.sqrt(2.0))))


def normal_ppf(prob: float, mean: float = 0.0, sd: float = 1.0) -> float:
    """Inverse CDF of the normal distribution (Acklam's rational approximation)."""
    if not (0.0 < prob < 1.0):
        raise ValueError("Probability must be in (0, 1).")
    if sd <= 0:
        raise ValueError("Standard deviation must be positive.")

    # Coefficients for Peter Acklam's algorithm.
    a = [-3.969683028665376e01, 2.209460984245205e02, -2.759285104469687e02,
         1.383577518672690e02, -3.066479806614716e01, 2.506628277459239e00]
    b = [-5.447609879822406e01, 1.615858368580409e02, -1.556989798598866e02,
         6.680131188771972e01, -1.328068155288572e01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e00,
         -2.549732539343734e00, 4.374664141464968e00, 2.938163982698783e00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e00,
         3.754408661907416e00]

    p_low = 0.02425
    p_high = 1.0 - p_low

    if prob < p_low:
        q = math.sqrt(-2.0 * math.log(prob))
        z = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        )
    elif prob <= p_high:
        q = prob - 0.5
        r = q * q
        z = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (
            ((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1.0
        )
    else:
        q = math.sqrt(-2.0 * math.log(1.0 - prob))
        z = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / (
            (((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1.0
        )

    # One Halley refinement step for full double precision.
    e = normal_cdf(z) - prob
    u = e * math.sqrt(2.0 * math.pi) * math.exp(z * z / 2.0)
    z = z - u / (1.0 + z * u / 2.0)

    return mean + sd * z


# ---------------------------------------------------------------------------
# Chi-square and F.
# ---------------------------------------------------------------------------


def chi2_cdf(x: float, df: float) -> float:
    """CDF of the chi-square distribution with ``df`` degrees of freedom."""
    if df <= 0:
        raise ValueError("Degrees of freedom must be positive.")
    if x <= 0.0:
        return 0.0
    return _lower_regularized_gamma(df / 2.0, x / 2.0)


def f_cdf(x: float, df1: float, df2: float) -> float:
    """CDF of the F distribution with (df1, df2) degrees of freedom."""
    if df1 <= 0 or df2 <= 0:
        raise ValueError("Degrees of freedom must be positive.")
    if x <= 0.0:
        return 0.0
    # F CDF via the incomplete beta: I_{df1*x/(df1*x+df2)}(df1/2, df2/2).
    z = (df1 * x) / (df1 * x + df2)
    return regularized_incomplete_beta(df1 / 2.0, df2 / 2.0, z)
