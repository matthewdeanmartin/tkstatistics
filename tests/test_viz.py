from __future__ import annotations

import pytest

from tkstatistics.viz import build_histogram, compute_bins, render_svg
from tkstatistics.viz.histogram import HistogramSpec


def test_compute_bins_basic_counts():
    edges, counts = compute_bins([1, 2, 2, 3, 3, 3, 4], bins=3)
    assert len(edges) == 4
    assert len(counts) == 3
    assert sum(counts) == 7


def test_compute_bins_matches_numpy():
    np = pytest.importorskip("numpy")
    data = [0.1, 0.5, 0.5, 1.2, 2.3, 2.4, 2.9, 3.1, 3.8, 4.0, 4.0, 4.4]

    for bins in (3, 5, 10):
        edges, counts = compute_bins(data, bins=bins)
        np_counts, np_edges = np.histogram(data, bins=bins)
        assert counts == list(np_counts)
        for e, ne in zip(edges, np_edges, strict=True):
            assert e == pytest.approx(float(ne))


def test_compute_bins_drops_missing_and_nonfinite():
    edges, counts = compute_bins([1.0, None, 2.0, float("nan"), float("inf"), 3.0], bins=2)
    assert sum(counts) == 3


def test_compute_bins_degenerate_range():
    edges, counts = compute_bins([5.0, 5.0, 5.0], bins=4)
    assert sum(counts) == 3
    assert edges[0] < 5.0 < edges[-1]


def test_compute_bins_empty():
    edges, counts = compute_bins([], bins=5)
    assert counts == [0]


def test_compute_bins_rejects_zero_bins():
    with pytest.raises(ValueError):
        compute_bins([1.0, 2.0], bins=0)


def test_build_histogram_produces_one_bar_per_bin():
    spec = HistogramSpec(values=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10], bins=5, title="T", x_label="x")
    scene = build_histogram(spec, width=400, height=300)
    assert len([r for r in scene.rects]) == 5
    assert scene.width == 400
    assert scene.height == 300
    # Title + x_label text present.
    texts = [t.text for t in scene.texts]
    assert "T" in texts
    assert "x" in texts


def test_render_svg_is_wellformed_xml():
    import xml.dom.minidom as minidom

    spec = HistogramSpec(values=[1, 2, 2, 3, 3, 3], bins=3, title="My <Hist>")
    scene = build_histogram(spec)
    svg = render_svg(scene)

    assert svg.startswith("<svg")
    assert svg.rstrip().endswith("</svg>")
    # Title with special chars must be escaped, and the doc must parse.
    assert "My <Hist>" not in svg
    assert "My &lt;Hist&gt;" in svg
    minidom.parseString(svg)  # raises if malformed


def test_render_svg_has_a_rect_per_bar():
    spec = HistogramSpec(values=list(range(20)), bins=4)
    svg = render_svg(build_histogram(spec))
    # 1 background rect + 4 bar rects.
    assert svg.count("<rect") == 5
