# tkstatistics/viz/scene.py

"""
A backend-agnostic description of a chart as a list of drawing primitives.

Coordinates are in pixels with the origin at the top-left (SVG/Canvas
convention). Renderers (SVG, Tk Canvas) consume a :class:`Scene` without
knowing anything about statistics — the chart builders produce scenes, the
renderers draw them.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Rect:
    """An axis-aligned rectangle."""

    x: float
    y: float
    width: float
    height: float
    fill: str = "#4477aa"
    stroke: str = "#22344a"
    stroke_width: float = 1.0


@dataclass
class Line:
    """A single straight line segment."""

    x1: float
    y1: float
    x2: float
    y2: float
    stroke: str = "#333333"
    stroke_width: float = 1.0


@dataclass
class Polyline:
    """A connected sequence of points (not filled)."""

    points: list[tuple[float, float]]
    stroke: str = "#cc3311"
    stroke_width: float = 1.5


@dataclass
class Text:
    """A text label anchored at (x, y)."""

    x: float
    y: float
    text: str
    anchor: str = "middle"  # start | middle | end
    font_size: float = 11.0
    fill: str = "#222222"


@dataclass
class Scene:
    """A complete drawable chart at a fixed pixel size."""

    width: float
    height: float
    background: str = "#ffffff"
    rects: list[Rect] = field(default_factory=list)
    lines: list[Line] = field(default_factory=list)
    polylines: list[Polyline] = field(default_factory=list)
    texts: list[Text] = field(default_factory=list)

    def add(self, primitive: Rect | Line | Polyline | Text) -> None:
        """Append a primitive to the appropriate layer."""
        if isinstance(primitive, Rect):
            self.rects.append(primitive)
        elif isinstance(primitive, Line):
            self.lines.append(primitive)
        elif isinstance(primitive, Polyline):
            self.polylines.append(primitive)
        elif isinstance(primitive, Text):
            self.texts.append(primitive)
        else:  # pragma: no cover - defensive
            raise TypeError(f"Unsupported primitive: {type(primitive)!r}")
