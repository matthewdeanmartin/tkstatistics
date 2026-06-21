# tkstatistics/app/chart_window.py

"""
A Toplevel window that displays a chart Scene on a Canvas, with SVG export.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from tkstatistics.viz import render_svg
from tkstatistics.viz.canvas import render_canvas
from tkstatistics.viz.scene import Scene


class ChartWindow(tk.Toplevel):
    """Displays a :class:`Scene` and offers SVG export."""

    def __init__(self, master: tk.Misc, scene: Scene, title: str = "Chart"):
        super().__init__(master)
        self.title(title)
        self.scene = scene

        toolbar = ttk.Frame(self)
        toolbar.pack(side="top", fill="x")
        ttk.Button(toolbar, text="Export SVG...", command=self._export_svg).pack(side="left", padx=4, pady=4)

        self.canvas = tk.Canvas(self, width=scene.width, height=scene.height, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        render_canvas(self.canvas, scene)

    def _export_svg(self):
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Export chart as SVG",
            defaultextension=".svg",
            filetypes=[("SVG image", "*.svg")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(render_svg(self.scene))
        except OSError as exc:
            messagebox.showerror("Export Failed", f"Could not write SVG:\n{exc}", parent=self)
