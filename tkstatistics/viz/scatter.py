# tkstatistics/viz/scatter.py

"""
Scatter plot builder, with an optional OLS-fitted regression line.

The fitted line reuses the package's own ``stdlib_simple_regression`` so the
chart and the regression analysis agree by construction.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ..stats.regression import stdlib_simple_regression
from .axes import draw_axes, draw_x_ticks, draw_y_ticks, make_plot_area, nice_ticks
from .scene import Line, Rect, Scene, Text


@dataclass
class ScatterSpec:
    """Inputs that define a scatter plot (independent of pixel size)."""

    x: list[float]
    y: list[float]
    title: str = ""
    x_label: str = ""
    y_label: str = ""
    fit_line: bool = False


def _clean_pairs(x: list[float | int | None], y: list[float | int | None]) -> tuple[list[float], list[float]]:
    cx: list[float] = []
    cy: list[float] = []
    for xi, yi in zip(x, y, strict=False):
        if xi is None or yi is None:
            continue
        fx, fy = float(xi), float(yi)
        if math.isfinite(fx) and math.isfinite(fy):
            cx.append(fx)
            cy.append(fy)
    return cx, cy


def build_scatter(spec: ScatterSpec, width: float = 560.0, height: float = 420.0) -> Scene:
    """Build a drawable scatter plot scene, optionally with a fitted line."""
    x, y = _clean_pairs(spec.x, spec.y)
    scene = Scene(width=width, height=height)

    if spec.title:
        scene.add(Text(x=width / 2, y=20, text=spec.title, font_size=14))

    if not x:
        # Nothing to plot; return an empty framed scene rather than crashing.
        area = make_plot_area(scene, 0.0, 1.0, 0.0, 1.0, has_title=bool(spec.title))
        draw_axes(scene, area)
        return scene

    x_lo, x_hi = min(x), max(x)
    y_lo, y_hi = min(y), max(y)
    x_pad = (x_hi - x_lo) * 0.05 or 1.0
    y_pad = (y_hi - y_lo) * 0.05 or 1.0
    area = make_plot_area(
        scene, x_lo - x_pad, x_hi + x_pad, y_lo - y_pad, y_hi + y_pad, has_title=bool(spec.title)
    )

    draw_axes(scene, area)
    draw_x_ticks(scene, area, nice_ticks(x_lo, x_hi, 5))
    draw_y_ticks(scene, area, nice_ticks(y_lo, y_hi, 5))
    if spec.x_label:
        scene.add(Text(x=area.left + area.width / 2, y=height - 8, text=spec.x_label, font_size=11))
    if spec.y_label:
        scene.add(Text(x=14, y=area.top + area.height / 2, text=spec.y_label, anchor="middle", font_size=11))

    # Points as small filled squares.
    for px, py in zip(x, y, strict=True):
        cx, cy = area.x_px(px), area.y_px(py)
        scene.add(Rect(x=cx - 2.5, y=cy - 2.5, width=5, height=5, fill="#4477aa", stroke="#22344a"))

    # Optional fitted line across the visible x range.
    if spec.fit_line and len(x) >= 2:
        result = stdlib_simple_regression(x, y)
        if "error" not in result:
            intercept, slope = result["coefficients"]
            x0, x1 = area.x_min, area.x_max
            scene.add(
                Line(
                    x1=area.x_px(x0),
                    y1=area.y_px(intercept + slope * x0),
                    x2=area.x_px(x1),
                    y2=area.y_px(intercept + slope * x1),
                    stroke="#cc3311",
                    stroke_width=2.0,
                )
            )

    return scene
