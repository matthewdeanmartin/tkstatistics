# tkstatistics/viz/qqplot.py

"""
Normal quantile-quantile (Q-Q) plot builder.

Sample quantiles (sorted data) are plotted against theoretical standard-normal
quantiles obtained from :func:`tkstatistics.stats.distributions.normal_ppf`,
using Blom's plotting positions. A reference line through the data's mean/sd
shows the expected normal relationship.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

from ..stats.distributions import normal_ppf
from .axes import draw_axes, draw_x_ticks, draw_y_ticks, make_plot_area, nice_ticks
from .scene import Line, Rect, Scene, Text


@dataclass
class QQSpec:
    """Inputs that define a normal Q-Q plot (independent of pixel size)."""

    values: list[float]
    title: str = ""


def _clean(values: list[float | int | None]) -> list[float]:
    return [float(v) for v in values if v is not None and math.isfinite(float(v))]


def compute_qq_points(values: list[float | int | None]) -> list[tuple[float, float]]:
    """Return (theoretical_quantile, sample_quantile) pairs, sorted by theory.

    Uses Blom's plotting position (i - 3/8) / (n + 1/4), the common default for
    normal probability plots.
    """
    sample = sorted(_clean(values))
    n = len(sample)
    points: list[tuple[float, float]] = []
    for i, value in enumerate(sample, start=1):
        p = (i - 0.375) / (n + 0.25)
        points.append((normal_ppf(p), value))
    return points


def build_qqplot(spec: QQSpec, width: float = 520.0, height: float = 480.0) -> Scene:
    """Build a drawable normal Q-Q plot scene."""
    points = compute_qq_points(spec.values)
    scene = Scene(width=width, height=height)

    if spec.title:
        scene.add(Text(x=width / 2, y=20, text=spec.title, font_size=14))

    if len(points) < 2:
        area = make_plot_area(scene, -1.0, 1.0, -1.0, 1.0, has_title=bool(spec.title))
        draw_axes(scene, area)
        return scene

    tx = [p[0] for p in points]
    sy = [p[1] for p in points]
    x_lo, x_hi = min(tx), max(tx)
    y_lo, y_hi = min(sy), max(sy)
    x_pad = (x_hi - x_lo) * 0.05 or 1.0
    y_pad = (y_hi - y_lo) * 0.05 or 1.0
    area = make_plot_area(
        scene, x_lo - x_pad, x_hi + x_pad, y_lo - y_pad, y_hi + y_pad, has_title=bool(spec.title)
    )

    draw_axes(scene, area)
    draw_x_ticks(scene, area, nice_ticks(x_lo, x_hi, 5))
    draw_y_ticks(scene, area, nice_ticks(y_lo, y_hi, 5))
    scene.add(Text(x=area.left + area.width / 2, y=height - 8, text="Theoretical quantiles", font_size=11))
    scene.add(Text(x=14, y=area.top + area.height / 2, text="Sample quantiles", anchor="middle", font_size=11))

    # Reference line: sample follows Normal(mean, sd) → y = mean + sd * z.
    clean = _clean(spec.values)
    mean = statistics.mean(clean)
    sd = statistics.stdev(clean) if len(clean) > 1 else 0.0
    if sd > 0:
        x0, x1 = area.x_min, area.x_max
        scene.add(
            Line(
                x1=area.x_px(x0),
                y1=area.y_px(mean + sd * x0),
                x2=area.x_px(x1),
                y2=area.y_px(mean + sd * x1),
                stroke="#cc3311",
                stroke_width=1.5,
            )
        )

    # Points.
    for theo, samp in points:
        cx, cy = area.x_px(theo), area.y_px(samp)
        scene.add(Rect(x=cx - 2.5, y=cy - 2.5, width=5, height=5, fill="#4477aa", stroke="#22344a"))

    return scene
