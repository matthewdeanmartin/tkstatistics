# tkstatistics/viz/canvas.py

"""
Render a :class:`~tkstatistics.viz.scene.Scene` onto a Tk ``Canvas``.

Kept separate from the scene/SVG modules so that building and exporting charts
never requires importing tkinter (or having a display).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .scene import Scene

if TYPE_CHECKING:  # pragma: no cover
    import tkinter as tk

_ANCHOR_MAP = {"start": "w", "middle": "center", "end": "e"}


def render_canvas(canvas: tk.Canvas, scene: Scene) -> None:
    """Draw ``scene`` onto an existing Tk ``Canvas``, clearing it first."""
    canvas.delete("all")
    canvas.configure(background=scene.background)

    for r in scene.rects:
        canvas.create_rectangle(
            r.x, r.y, r.x + r.width, r.y + r.height,
            fill=r.fill, outline=r.stroke, width=r.stroke_width,
        )

    for ln in scene.lines:
        canvas.create_line(ln.x1, ln.y1, ln.x2, ln.y2, fill=ln.stroke, width=ln.stroke_width)

    for pl in scene.polylines:
        if len(pl.points) >= 2:
            flat = [coord for point in pl.points for coord in point]
            canvas.create_line(*flat, fill=pl.stroke, width=pl.stroke_width)

    for t in scene.texts:
        canvas.create_text(
            t.x, t.y, text=t.text,
            anchor=_ANCHOR_MAP.get(t.anchor, "center"),
            font=("sans-serif", int(t.font_size)),
            fill=t.fill,
        )
