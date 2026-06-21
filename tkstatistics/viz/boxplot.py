# tkstatistics/viz/boxplot.py

"""
Box-and-whisker plot builder.

``compute_box_stats`` is the numeric core (Tukey quartiles + 1.5·IQR whiskers +
outliers); ``build_boxplot`` lays it out as a vertical box on a shared plot area.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field

from .axes import draw_axes, draw_y_ticks, make_plot_area, nice_ticks
from .scene import Line, Rect, Scene, Text


@dataclass
class BoxStats:
    """Summary five-number-ish stats for a box plot."""

    q1: float
    median: float
    q3: float
    whisker_low: float
    whisker_high: float
    outliers: list[float] = field(default_factory=list)

    @property
    def iqr(self) -> float:
        return self.q3 - self.q1


@dataclass
class BoxplotSpec:
    """Inputs that define a single box plot (independent of pixel size)."""

    values: list[float]
    title: str = ""
    y_label: str = ""


def _clean(values: list[float | int | None]) -> list[float]:
    return [float(v) for v in values if v is not None and math.isfinite(float(v))]


def compute_box_stats(values: list[float | int | None]) -> BoxStats:
    """Compute quartiles, Tukey whiskers, and outliers for ``values``."""
    clean = sorted(_clean(values))
    if not clean:
        raise ValueError("Box plot requires at least one finite value.")
    if len(clean) == 1:
        v = clean[0]
        return BoxStats(q1=v, median=v, q3=v, whisker_low=v, whisker_high=v, outliers=[])

    # statistics.quantiles with n=4 → [Q1, Q2, Q3] (exclusive method, matches the
    # package's descriptives module).
    q1, median, q3 = statistics.quantiles(clean, n=4)
    iqr = q3 - q1
    low_fence = q1 - 1.5 * iqr
    high_fence = q3 + 1.5 * iqr

    inside = [v for v in clean if low_fence <= v <= high_fence]
    whisker_low = min(inside) if inside else q1
    whisker_high = max(inside) if inside else q3
    outliers = [v for v in clean if v < low_fence or v > high_fence]

    return BoxStats(
        q1=q1,
        median=median,
        q3=q3,
        whisker_low=whisker_low,
        whisker_high=whisker_high,
        outliers=outliers,
    )


def build_boxplot(spec: BoxplotSpec, width: float = 480.0, height: float = 420.0) -> Scene:
    """Build a drawable vertical box plot scene."""
    stats = compute_box_stats(spec.values)
    scene = Scene(width=width, height=height)

    if spec.title:
        scene.add(Text(x=width / 2, y=20, text=spec.title, font_size=14))

    # Vertical extent covers whiskers and any outliers, with a little padding.
    all_y = [stats.whisker_low, stats.whisker_high, *stats.outliers]
    y_lo, y_hi = min(all_y), max(all_y)
    pad = (y_hi - y_lo) * 0.05 or 1.0
    area = make_plot_area(scene, 0.0, 1.0, y_lo - pad, y_hi + pad, has_title=bool(spec.title))

    draw_axes(scene, area)
    draw_y_ticks(scene, area, nice_ticks(y_lo, y_hi, 5))
    if spec.y_label:
        scene.add(Text(x=14, y=area.top + area.height / 2, text=spec.y_label, anchor="middle", font_size=11))

    # The box spans the central portion of the plot width.
    box_left = area.x_px(0.32)
    box_right = area.x_px(0.68)
    center_x = area.x_px(0.5)

    y_q1 = area.y_px(stats.q1)
    y_q3 = area.y_px(stats.q3)
    y_med = area.y_px(stats.median)

    # Box (Q1..Q3).
    scene.add(Rect(x=box_left, y=y_q3, width=box_right - box_left, height=y_q1 - y_q3))
    # Median line.
    scene.add(Line(x1=box_left, y1=y_med, x2=box_right, y2=y_med, stroke="#cc3311", stroke_width=2.0))

    # Whiskers + caps.
    scene.add(Line(x1=center_x, y1=y_q3, x2=center_x, y2=area.y_px(stats.whisker_high)))
    scene.add(Line(x1=center_x, y1=y_q1, x2=center_x, y2=area.y_px(stats.whisker_low)))
    cap = (box_right - box_left) * 0.4
    for value in (stats.whisker_high, stats.whisker_low):
        cy = area.y_px(value)
        scene.add(Line(x1=center_x - cap, y1=cy, x2=center_x + cap, y2=cy))

    # Outliers as small open circles (drawn as tiny rects to keep primitives simple).
    for value in stats.outliers:
        oy = area.y_px(value)
        scene.add(Rect(x=center_x - 2, y=oy - 2, width=4, height=4, fill="#ffffff", stroke="#cc3311"))

    return scene
