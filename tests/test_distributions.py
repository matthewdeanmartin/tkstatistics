from __future__ import annotations

import math

import pytest

from tkstatistics.stats import distributions as dist

scipy_stats = pytest.importorskip("scipy.stats")


def test_student_t_cdf_matches_scipy():
    for t_value, df in [(0.0, 1.0), (0.25, 2.0), (-1.75, 5.0), (2.5, 10.0), (4.0, 30.0)]:
        expected = float(scipy_stats.t.cdf(t_value, df))
        assert math.isclose(dist.student_t_cdf(t_value, df), expected, rel_tol=1e-8, abs_tol=1e-8)


def test_student_t_ppf_matches_scipy():
    for prob, df in [(0.75, 3.0), (0.9, 5.0), (0.975, 10.0), (0.99, 40.0)]:
        expected = float(scipy_stats.t.ppf(prob, df))
        assert math.isclose(dist.student_t_ppf(prob, df), expected, rel_tol=1e-8, abs_tol=1e-8)


def test_normal_cdf_matches_scipy():
    for z in [-3.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.5]:
        expected = float(scipy_stats.norm.cdf(z))
        assert math.isclose(dist.normal_cdf(z), expected, rel_tol=1e-10, abs_tol=1e-10)


def test_normal_ppf_matches_scipy():
    for prob in [0.001, 0.01, 0.25, 0.5, 0.75, 0.975, 0.999]:
        expected = float(scipy_stats.norm.ppf(prob))
        assert math.isclose(dist.normal_ppf(prob), expected, rel_tol=1e-7, abs_tol=1e-7)


def test_chi2_cdf_matches_scipy():
    for x, df in [(0.5, 1.0), (2.0, 2.0), (5.0, 3.0), (10.0, 5.0), (20.0, 10.0)]:
        expected = float(scipy_stats.chi2.cdf(x, df))
        assert math.isclose(dist.chi2_cdf(x, df), expected, rel_tol=1e-8, abs_tol=1e-9)


def test_f_cdf_matches_scipy():
    for x, df1, df2 in [(1.0, 1.0, 1.0), (2.0, 3.0, 10.0), (0.5, 5.0, 5.0), (4.0, 2.0, 20.0)]:
        expected = float(scipy_stats.f.cdf(x, df1, df2))
        assert math.isclose(dist.f_cdf(x, df1, df2), expected, rel_tol=1e-8, abs_tol=1e-9)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        dist.student_t_cdf(1.0, 0.0)
    with pytest.raises(ValueError):
        dist.normal_ppf(0.0)
    with pytest.raises(ValueError):
        dist.chi2_cdf(1.0, -1.0)
