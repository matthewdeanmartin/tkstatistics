# tkstatistics/app/output_viewer.py

"""
A widget to display a history of analysis results and their formatted text output.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Dict


class OutputViewer(ttk.Frame):
    """A two-pane widget for browsing and viewing analysis results."""

    def __init__(self, master: tk.Misc, **kwargs):
        super().__init__(master, **kwargs)

        self.results_map: Dict[str, str] = {}

        # Main container
        paned_window = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned_window.pack(fill="both", expand=True)

        # --- Left Pane: History Tree ---
        tree_frame = ttk.Frame(paned_window, padding=2)
        ttk.Label(tree_frame, text="Analysis History", anchor="w").pack(fill="x")

        self.tree = ttk.Treeview(tree_frame, show="tree")
        self.tree.pack(fill="both", expand=True)
        paned_window.add(tree_frame, weight=1)

        # --- Right Pane: Results Text ---
        text_frame = ttk.Frame(paned_window, padding=2)
        ttk.Label(text_frame, text="Results", anchor="w").pack(fill="x")

        self.text = tk.Text(
            text_frame,
            wrap="word",
            state=tk.DISABLED,  # Read-only
            borderwidth=0,
            font=("Courier New", 10),  # Monospaced font for tables
        )
        # Scrollbar for the text widget
        text_scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text.yview)
        self.text.configure(yscrollcommand=text_scrollbar.set)

        self.text.pack(side="left", fill="both", expand=True)
        text_scrollbar.pack(side="right", fill="y")
        paned_window.add(text_frame, weight=4)

        # --- Bindings ---
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

    def _on_tree_select(self, event=None):
        """Displays the result for the selected history item."""
        selection = self.tree.selection()
        if not selection:
            return

        selected_item_id = selection[0]
        content = self.results_map.get(selected_item_id, "No result found.")

        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.insert("1.0", content)
        self.text.config(state=tk.DISABLED)

    def add_result(self, title: str, content: str):
        """
        Adds a new analysis result to the viewer and immediately displays it.

        Args:
            title: The title to display in the history tree.
            content: The formatted string content of the result.
        """
        # The item ID is the return value of the insert method
        item_id = self.tree.insert("", "end", text=title)
        self.results_map[item_id] = content

        # Automatically select the new item
        self.tree.selection_set(item_id)
        self.tree.focus(item_id)
        self.tree.see(item_id)

        # --- THE FIX ---
        # Explicitly call the update method instead of relying on the event.
        self._on_tree_select()
