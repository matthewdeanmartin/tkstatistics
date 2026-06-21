# tkstatistics/viz/histogram.py

"""
Histogram chart builder.

``compute_bins`` is the numeric core (equivalence-testable against numpy's
``histogram``); ``build_histogram`` turns the binned counts plus chart chrome
(axes, labels) into a backend-agnostic :class:`~tkstatistics.viz.scene.Scene`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .axes import draw_axes, draw_x_ticks, draw_y_ticks, make_plot_area, nice_ticks
from .scene import Rect, Scene, Text


@dataclass
class HistogramSpec:
    """Inputs that define a histogram (independent of pixel size)."""

    values: list[float]
    bins: int = 10
    title: str = ""
    x_label: str = ""


def _clean(values: list[float | int | None]) -> list[float]:
    return [float(v) for v in values if v is not None and math.isfinite(float(v))]


def compute_bins(values: list[float | int | None], bins: int = 10) -> tuple[list[float], list[int]]:
    """Bin ``values`` into ``bins`` equal-width buckets.

    Returns ``(edges, counts)`` where ``edges`` has ``bins + 1`` entries and
    ``counts`` has ``bins``. Matches numpy.histogram's default convention:
    half-open bins ``[edge_i, edge_{i+1})`` except the last, which is closed.
    """
    if bins < 1:
        raise ValueError("bins must be >= 1")

    clean = _clean(values)
    if not clean:
        return ([0.0, 1.0], [0])

    lo = min(clean)
    hi = max(clean)
    if lo == hi:
        # Degenerate range: numpy widens to (lo-0.5, hi+0.5).
        lo -= 0.5
        hi += 0.5

    width = (hi - lo) / bins
    edges = [lo + i * width for i in range(bins + 1)]
    edges[-1] = hi  # guard against floating-point drift at the top edge

    counts = [0] * bins
    for v in clean:
        if v >= hi:
            counts[-1] += 1
            continue
        idx = int((v - lo) / width)
        if idx < 0:
            idx = 0
        elif idx >= bins:
            idx = bins - 1
        counts[idx] += 1

    return (edges, counts)


def build_histogram(spec: HistogramSpec, width: float = 640.0, height: float = 400.0) -> Scene:
    """Build a drawable histogram scene at the given pixel size."""
    edges, counts = compute_bins(spec.values, spec.bins)
    scene = Scene(width=width, height=height)

    max_count = max(counts) if counts else 0
    x_min, x_max = edges[0], edges[-1]
    area = make_plot_area(scene, x_min, x_max, 0.0, max(max_count, 1), has_title=bool(spec.title))

    # Title.
    if spec.title:
        scene.add(Text(x=width / 2, y=20, text=spec.title, font_size=14))

    # Bars.
    for i, count in enumerate(counts):
        left = area.x_px(edges[i])
        right = area.x_px(edges[i + 1])
        scene.add(
            Rect(
                x=left,
                y=area.y_px(count),
                width=max(right - left - 1.0, 1.0),
                height=area.bottom - area.y_px(count),
            )
        )

    draw_axes(scene, area)
    draw_y_ticks(scene, area, nice_ticks(0, max_count, 4))

    # X ticks at bin edges (label first, middle, last to avoid crowding).
    edge_idxs = sorted({0, len(edges) // 2, len(edges) - 1})
    draw_x_ticks(scene, area, [edges[i] for i in edge_idxs])

    if spec.x_label:
        scene.add(Text(x=area.left + area.width / 2, y=height - 8, text=spec.x_label, font_size=11))

    return scene
