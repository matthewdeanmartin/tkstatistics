# tkstatistics/app/project_explorer.py
"""
A widget to display the contents of a project (datasets, analyses).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from tkstatistics.core.project import Project


class ProjectExplorer(ttk.Frame):
    """A tree view for navigating datasets and analyses within a project."""

    def __init__(self, master: tk.Misc, **kwargs):
        super().__init__(master, **kwargs)

        self.on_select_dataset: Callable[[str], None] | None = None

        ttk.Label(self, text="Project Explorer", anchor="w").pack(fill="x", padx=2, pady=2)

        self.tree = ttk.Treeview(self, show="tree")
        self.tree.pack(fill="both", expand=True)

        # Top-level nodes
        self.datasets_node = self.tree.insert("", "end", text="Datasets", open=True)
        self.analyses_node = self.tree.insert("", "end", text="Analyses", open=True)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _on_select(self, event=None):
        """Handle item selection to load datasets."""
        selection = self.tree.selection()
        if not selection:
            return

        selected_item = selection[0]
        parent = self.tree.parent(selected_item)

        # If a dataset was clicked, invoke the callback
        if parent == self.datasets_node and self.on_select_dataset:
            dataset_name = self.tree.item(selected_item, "text")
            self.on_select_dataset(dataset_name)

    def populate(self, project: Project | None):
        """Clears and repopulates the tree from a Project object."""
        # Clear existing items
        for item in self.tree.get_children(self.datasets_node):
            self.tree.delete(item)
        for item in self.tree.get_children(self.analyses_node):
            self.tree.delete(item)

        if not project:
            return

        # Populate datasets
        for name in project.list_datasets():
            self.tree.insert(self.datasets_node, "end", text=name)

        # Populate analyses
        for analysis in project.list_analyses():
            # Display spec details in a readable way
            title = f"{analysis['analysis']}: {analysis['dataset']}"
            self.tree.insert(self.analyses_node, "end", text=title)
