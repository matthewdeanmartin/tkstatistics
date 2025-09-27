# tkstatistics/app/grid.py

"""
A read-only data grid widget for displaying tabular data using ttk.Treeview.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from tkstatistics.core.dataset import TabularData


class DataGrid(ttk.Frame):
    """A widget for displaying a dataset in a scrollable grid."""

    def __init__(self, master: tk.Misc, **kwargs):
        super().__init__(master, **kwargs)
        self.tree = ttk.Treeview(self, show="headings")

        # --- Scrollbars ---
        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # --- Layout ---
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def clear(self):
        """Removes all data and columns from the grid."""
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = ()

    def display_data(self, dataset: TabularData):
        """
        Populates the grid with data from a TabularData object.

        Args:
            dataset: The TabularData instance to display.
        """
        self.clear()

        columns = dataset.column_names
        if not columns:
            return

        self.tree["columns"] = columns

        for col_name in columns:
            self.tree.heading(col_name, text=col_name, anchor="w")
            # A simple heuristic for column width
            # In a real app, this could be more sophisticated (e.g., based on content)
            self.tree.column(col_name, width=100, stretch=False, anchor="w")

        # Insert data rows
        for i, row in enumerate(dataset.to_list_of_dicts()):
            # Use alternating row colors for readability
            tag = "evenrow" if i % 2 == 0 else "oddrow"
            self.tree.insert("", "end", values=list(row.values()), tags=(tag,))

        self.tree.tag_configure("evenrow", background="#f0f0f0")
        self.tree.tag_configure("oddrow", background="white")
