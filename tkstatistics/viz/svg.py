# tkstatistics/viz/svg.py

"""
Render a :class:`~tkstatistics.viz.scene.Scene` to an SVG document string.

SVG is the export format and the testable, display-free rendering target: the
same scene that draws on a Tk Canvas serializes here for snapshot tests and for
saving charts from headless runs.
"""

from __future__ import annotations

from xml.sax.saxutils import escape

from .scene import Scene


def _num(value: float) -> str:
    """Format a coordinate compactly and deterministically."""
    return f"{value:.2f}".rstrip("0").rstrip(".")


def render_svg(scene: Scene) -> str:
    """Serialize a scene to a standalone SVG string."""
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_num(scene.width)}" '
        f'height="{_num(scene.height)}" viewBox="0 0 {_num(scene.width)} {_num(scene.height)}">',
        f'<rect x="0" y="0" width="{_num(scene.width)}" height="{_num(scene.height)}" fill="{scene.background}"/>',
    ]

    for r in scene.rects:
        parts.append(
            f'<rect x="{_num(r.x)}" y="{_num(r.y)}" width="{_num(r.width)}" height="{_num(r.height)}" '
            f'fill="{r.fill}" stroke="{r.stroke}" stroke-width="{_num(r.stroke_width)}"/>'
        )

    for ln in scene.lines:
        parts.append(
            f'<line x1="{_num(ln.x1)}" y1="{_num(ln.y1)}" x2="{_num(ln.x2)}" y2="{_num(ln.y2)}" '
            f'stroke="{ln.stroke}" stroke-width="{_num(ln.stroke_width)}"/>'
        )

    for pl in scene.polylines:
        pts = " ".join(f"{_num(x)},{_num(y)}" for x, y in pl.points)
        parts.append(
            f'<polyline points="{pts}" fill="none" stroke="{pl.stroke}" stroke-width="{_num(pl.stroke_width)}"/>'
        )

    for t in scene.texts:
        parts.append(
            f'<text x="{_num(t.x)}" y="{_num(t.y)}" text-anchor="{t.anchor}" '
            f'font-size="{_num(t.font_size)}" font-family="sans-serif" fill="{t.fill}">{escape(t.text)}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)
