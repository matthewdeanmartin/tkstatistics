# tkstatistics/viz/axes.py

"""
Shared plot-area geometry and tick helpers used by the chart builders.

Charts differ in what they draw inside the plot area, but they all need the same
chrome: margins, a data→pixel mapping, axis lines, and "nice" tick values. This
module centralizes that so each chart builder only describes its data marks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .scene import Line, Scene, Text


@dataclass
class PlotArea:
    """Maps data coordinates to pixels within a chart's plot rectangle."""

    left: float
    top: float
    width: float
    height: float
    x_min: float
    x_max: float
    y_min: float
    y_max: float

    @property
    def right(self) -> float:
        return self.left + self.width

    @property
    def bottom(self) -> float:
        return self.top + self.height

    def x_px(self, value: float) -> float:
        span = (self.x_max - self.x_min) or 1.0
        return self.left + (value - self.x_min) / span * self.width

    def y_px(self, value: float) -> float:
        # Pixel y grows downward, so larger data values sit higher (smaller y).
        span = (self.y_max - self.y_min) or 1.0
        return self.bottom - (value - self.y_min) / span * self.height


def make_plot_area(
    scene: Scene,
    x_min: float,
    x_max: float,
    y_min: float,
    y_max: float,
    *,
    has_title: bool = False,
    margin_left: float = 55.0,
    margin_right: float = 20.0,
    margin_bottom: float = 50.0,
) -> PlotArea:
    """Compute the plot area for ``scene`` given data bounds."""
    margin_top = 40.0 if has_title else 20.0
    return PlotArea(
        left=margin_left,
        top=margin_top,
        width=scene.width - margin_left - margin_right,
        height=scene.height - margin_top - margin_bottom,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
    )


def draw_axes(scene: Scene, area: PlotArea) -> None:
    """Draw the left (y) and bottom (x) axis lines."""
    scene.add(Line(x1=area.left, y1=area.top, x2=area.left, y2=area.bottom))
    scene.add(Line(x1=area.left, y1=area.bottom, x2=area.right, y2=area.bottom))


def draw_y_ticks(scene: Scene, area: PlotArea, ticks: list[float]) -> None:
    """Draw y-axis tick marks and labels at the given data values."""
    for tick in ticks:
        ty = area.y_px(tick)
        scene.add(Line(x1=area.left - 4, y1=ty, x2=area.left, y2=ty))
        scene.add(Text(x=area.left - 8, y=ty + 4, text=fmt(tick), anchor="end", font_size=10))


def draw_x_ticks(scene: Scene, area: PlotArea, ticks: list[float]) -> None:
    """Draw x-axis tick marks and labels at the given data values."""
    for tick in ticks:
        tx = area.x_px(tick)
        scene.add(Line(x1=tx, y1=area.bottom, x2=tx, y2=area.bottom + 4))
        scene.add(Text(x=tx, y=area.bottom + 18, text=fmt(tick), anchor="middle", font_size=10))


def fmt(value: float) -> str:
    """Compact human-readable number formatting for tick labels."""
    if not math.isfinite(value):
        return str(value)
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.3g}"


def nice_ticks(lo: float, hi: float, count: int = 5) -> list[float]:
    """Pick ``count``-ish round tick values spanning ``[lo, hi]``."""
    if hi <= lo:
        return [lo]
    raw_step = (hi - lo) / count
    magnitude = 10 ** math.floor(math.log10(raw_step))
    step = magnitude
    for mult in (1, 2, 2.5, 5, 10):
        step = mult * magnitude
        if raw_step <= step:
            break
    ticks: list[float] = []
    start = math.floor(lo / step) * step
    tick = start
    while tick <= hi + step * 0.5:
        if tick >= lo - step * 0.5:
            # Snap near-zero values to exactly 0 to avoid "-0" / float noise.
            ticks.append(0.0 if abs(tick) < step * 1e-9 else tick)
        tick += step
    return ticks
