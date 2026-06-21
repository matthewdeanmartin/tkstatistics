"""
Pure-stdlib visualization layer.

A chart is built as a :class:`~tkstatistics.viz.scene.Scene` of drawing
primitives (rectangles, lines, polylines, text). The same scene renders to an
SVG string (exportable and testable without a display) and to a Tk ``Canvas``
(interactive). No third-party plotting libraries are used.
"""

from .boxplot import BoxplotSpec, build_boxplot, compute_box_stats
from .histogram import HistogramSpec, build_histogram, compute_bins
from .qqplot import QQSpec, build_qqplot, compute_qq_points
from .scatter import ScatterSpec, build_scatter
from .scene import Scene
from .svg import render_svg

__all__ = [
    "Scene",
    "render_svg",
    "HistogramSpec",
    "build_histogram",
    "compute_bins",
    "BoxplotSpec",
    "build_boxplot",
    "compute_box_stats",
    "ScatterSpec",
    "build_scatter",
    "QQSpec",
    "build_qqplot",
    "compute_qq_points",
]
