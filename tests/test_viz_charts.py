from __future__ import annotations

import statistics
import xml.dom.minidom as minidom

import pytest

from tkstatistics.viz import (
    BoxplotSpec,
    QQSpec,
    ScatterSpec,
    build_boxplot,
    build_qqplot,
    build_scatter,
    compute_box_stats,
    compute_qq_points,
    render_svg,
)


# ---------------------------------------------------------------------------
# Box plot
# ---------------------------------------------------------------------------


def test_box_stats_quartiles_match_statistics_module():
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    stats = compute_box_stats(data)
    q1, med, q3 = statistics.quantiles(data, n=4)
    assert stats.q1 == pytest.approx(q1)
    assert stats.median == pytest.approx(med)
    assert stats.q3 == pytest.approx(q3)


def test_box_stats_detects_outliers():
    # 100 is far beyond Q3 + 1.5*IQR.
    data = [10, 11, 12, 13, 14, 15, 16, 17, 18, 100]
    stats = compute_box_stats(data)
    assert 100 in stats.outliers
    assert stats.whisker_high < 100


def test_box_stats_single_value():
    stats = compute_box_stats([5.0])
    assert stats.q1 == stats.median == stats.q3 == 5.0
    assert stats.outliers == []


def test_box_stats_rejects_empty():
    with pytest.raises(ValueError):
        compute_box_stats([None, float("nan")])


def test_build_boxplot_svg_wellformed():
    spec = BoxplotSpec(values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 50], title="Box", y_label="v")
    svg = render_svg(build_boxplot(spec))
    minidom.parseString(svg)
    assert "Box" in svg


# ---------------------------------------------------------------------------
# Scatter
# ---------------------------------------------------------------------------


def test_build_scatter_has_point_per_pair():
    spec = ScatterSpec(x=[1, 2, 3, 4], y=[2, 4, 6, 8], title="S")
    scene = build_scatter(spec)
    # No fit line requested → rects are exactly the 4 points.
    assert len(scene.rects) == 4


def test_build_scatter_fit_line_adds_a_line():
    spec = ScatterSpec(x=[1, 2, 3, 4, 5], y=[2.1, 3.9, 6.2, 7.8, 10.1], fit_line=True)
    without = build_scatter(ScatterSpec(x=spec.x, y=spec.y, fit_line=False))
    withline = build_scatter(spec)
    # The fitted line is an extra red Line primitive.
    red_lines = [ln for ln in withline.lines if ln.stroke == "#cc3311"]
    assert len(red_lines) == 1
    assert len(withline.lines) == len(without.lines) + 1


def test_build_scatter_drops_incomplete_pairs():
    spec = ScatterSpec(x=[1, None, 3, float("nan")], y=[2, 4, None, 6])
    scene = build_scatter(spec)
    assert len(scene.rects) == 1  # only the (1,2) pair survives


def test_build_scatter_empty_does_not_crash():
    scene = build_scatter(ScatterSpec(x=[], y=[]))
    assert scene.rects == []


# ---------------------------------------------------------------------------
# Q-Q plot
# ---------------------------------------------------------------------------


def test_qq_points_sorted_and_paired():
    data = [3.0, 1.0, 2.0, 5.0, 4.0]
    points = compute_qq_points(data)
    assert len(points) == 5
    # Sample quantiles (second element) come out sorted ascending.
    sample = [s for _, s in points]
    assert sample == sorted(sample)
    # Theoretical quantiles are symmetric around 0 for symmetric ranks.
    theo = [t for t, _ in points]
    assert theo[0] == pytest.approx(-theo[-1], abs=1e-9)


def test_qq_theoretical_quantiles_match_scipy():
    scipy_stats = pytest.importorskip("scipy.stats")
    data = list(range(1, 21))
    points = compute_qq_points(data)
    n = len(data)
    for i, (theo, _) in enumerate(points, start=1):
        p = (i - 0.375) / (n + 0.25)
        assert theo == pytest.approx(float(scipy_stats.norm.ppf(p)), abs=1e-6)


def test_build_qqplot_svg_wellformed():
    spec = QQSpec(values=[2.1, 3.4, 1.9, 5.5, 4.2, 3.1, 2.8], title="Q-Q")
    svg = render_svg(build_qqplot(spec))
    minidom.parseString(svg)
    assert "Q-Q" in svg


def test_histogram_still_works_after_refactor():
    # Guard the axes-helper refactor of the histogram builder.
    from tkstatistics.viz import HistogramSpec, build_histogram

    scene = build_histogram(HistogramSpec(values=list(range(20)), bins=4))
    assert len(scene.rects) == 4
