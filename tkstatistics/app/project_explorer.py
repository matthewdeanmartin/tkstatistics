# tkstatistics/app/project_explorer.py
"""
A widget to display the contents of a project (datasets, analyses).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable
from tkinter import ttk
from typing import Any

from tkstatistics.core.project import Project


class ProjectExplorer(ttk.Frame):
    """A tree view for navigating datasets and analyses within a project."""

    def __init__(self, master: tk.Misc, **kwargs):
        super().__init__(master, **kwargs)

        # Callbacks for the main app to hook into
        self.on_select_dataset: Callable[[str], None] | None = None
        self.on_select_analysis: Callable[[dict[str, Any]], None] | None = None

        ttk.Label(self, text="Project Explorer", anchor="w").pack(fill="x", padx=2, pady=2)

        self.tree = ttk.Treeview(self, show="tree")
        self.tree.pack(fill="both", expand=True)

        # Top-level nodes
        self.datasets_node = self.tree.insert("", "end", text="Datasets", open=True)
        self.analyses_node = self.tree.insert("", "end", text="Analyses", open=True)

        # Maps treeview item IDs to the full analysis spec dictionary
        self.analysis_map: dict[str, dict[str, Any]] = {}

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_select(self, event=None):
        """Handle item selection to load datasets or trigger analysis re-run."""
        selection = self.tree.selection()
        if not selection:
            return

        selected_item_id = selection[0]
        parent = self.tree.parent(selected_item_id)

        # If a dataset was clicked, invoke the dataset callback
        if parent == self.datasets_node and self.on_select_dataset:
            dataset_name = self.tree.item(selected_item_id, "text")
            self.on_select_dataset(dataset_name)

        # If an analysis was clicked, invoke the analysis callback with its spec
        elif parent == self.analyses_node and self.on_select_analysis:
            spec = self.analysis_map.get(selected_item_id)
            if spec:
                self.on_select_analysis(spec)

    def populate(self, project: Project | None):
        """Clears and repopulates the tree from a Project object."""
        # Clear existing items
        for item in self.tree.get_children(self.datasets_node):
            self.tree.delete(item)
        for item in self.tree.get_children(self.analyses_node):
            self.tree.delete(item)
        self.analysis_map.clear()

        if not project:
            return

        # Populate datasets
        for name in project.list_datasets():
            self.tree.insert(self.datasets_node, "end", text=name)

        # Populate analyses, storing the spec for each one
        for analysis_spec in project.list_analyses():
            title = f"{analysis_spec.get('analysis', 'Unknown')}: {analysis_spec.get('dataset', 'N/A')}"
            # The item_id is the key we use to retrieve the full spec later
            item_id = self.tree.insert(self.analyses_node, "end", text=title)
            self.analysis_map[item_id] = analysis_spec