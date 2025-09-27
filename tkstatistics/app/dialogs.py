# tkstatistics/app/dialogs.py

"""
Tkinter dialog windows for statistical analyses.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk


class AnalysisDialog(tk.Toplevel):
    """A base class for analysis dialog windows."""

    def __init__(self, master: tk.Misc, title: str, variables: list[str]):
        super().__init__(master)
        self.title(title)
        self.transient(master)  # Keep dialog on top of the main window
        self.grab_set()  # Modal behavior

        self.variables = variables
        self.result: list[str] | None = None

        body = ttk.Frame(self)
        self.create_body(body)  # Implemented by subclasses
        body.pack(padx=10, pady=10)

        self.create_buttons()

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.wait_window(self)

    def create_body(self, master: ttk.Frame):
        """Placeholder for subclass UI creation."""
        raise NotImplementedError

    def create_buttons(self):
        """Creates the OK and Cancel buttons."""
        button_frame = ttk.Frame(self)

        ok_button = ttk.Button(button_frame, text="OK", command=self.ok)
        ok_button.pack(side="left", padx=5, pady=5)

        cancel_button = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_button.pack(side="left", padx=5, pady=5)

        button_frame.pack()

    def ok(self, event=None):
        """Handles the OK button click."""
        if not self.validate():
            return
        self.withdraw()
        self.update_idletasks()
        self.apply()
        self.cancel()

    def cancel(self, event=None):
        """Handles window closing or Cancel button click."""
        self.master.focus_set()
        self.destroy()

    def validate(self) -> bool:
        """Override to validate input before closing."""
        return True

    def apply(self):
        """Override to process data on OK click."""
        pass


class DescriptivesDialog(AnalysisDialog):
    """Dialog for selecting variables for descriptive statistics."""

    def __init__(self, master, variables: list[str]):
        # The title is passed to the parent constructor
        super().__init__(master, title="Descriptive Statistics", variables=variables)

    def create_body(self, master: ttk.Frame):
        """Creates the variable selection listbox."""
        ttk.Label(master, text="Select one or more variables:").pack(anchor="w")

        listbox_frame = ttk.Frame(master, borderwidth=1, relief="sunken")
        self.listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE, height=10)

        for var in self.variables:
            self.listbox.insert(tk.END, var)

        # Scrollbar for the listbox
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        listbox_frame.pack(fill="both", expand=True, pady=5)

    def validate(self) -> bool:
        """Ensure at least one variable is selected."""
        if not self.listbox.curselection():
            messagebox.showwarning("No Selection", "Please select at least one variable.", parent=self)
            return False
        return True

    def apply(self):
        """Store the selected variable names in the result attribute."""
        selected_indices = self.listbox.curselection()
        self.result = [self.variables[i] for i in selected_indices]


# --- New Dialogs for Regression ---


class SimpleRegressionDialog(AnalysisDialog):
    """Dialog for Simple Linear Regression."""

    def __init__(self, master, variables: list[str]):
        self.dependent_var = tk.StringVar()
        self.independent_var = tk.StringVar()
        super().__init__(master, title="Simple Linear Regression", variables=variables)

    def create_body(self, master: ttk.Frame):
        # Dependent Variable
        dep_frame = ttk.Labelframe(master, text="Dependent Variable (Y)")
        dep_combo = ttk.Combobox(dep_frame, textvariable=self.dependent_var, values=self.variables, state="readonly")
        dep_combo.pack(padx=5, pady=5)
        dep_frame.pack(fill="x", expand=True, pady=5)

        # Independent Variable
        ind_frame = ttk.Labelframe(master, text="Independent Variable (X)")
        ind_combo = ttk.Combobox(ind_frame, textvariable=self.independent_var, values=self.variables, state="readonly")
        ind_combo.pack(padx=5, pady=5)
        ind_frame.pack(fill="x", expand=True, pady=5)

    def validate(self) -> bool:
        dep = self.dependent_var.get()
        ind = self.independent_var.get()
        if not dep or not ind:
            messagebox.showwarning(
                "Incomplete Selection", "Please select both a dependent and an independent variable.", parent=self
            )
            return False
        if dep == ind:
            messagebox.showwarning(
                "Invalid Selection", "The dependent and independent variables cannot be the same.", parent=self
            )
            return False
        return True

    def apply(self):
        self.result = {"dependent": self.dependent_var.get(), "independent": self.independent_var.get()}


class MultipleRegressionDialog(AnalysisDialog):
    """Dialog for Multiple Linear Regression."""

    def __init__(self, master, variables: list[str]):
        self.dependent_var = tk.StringVar()
        super().__init__(master, title="Multiple Linear Regression", variables=variables)

    def create_body(self, master: ttk.Frame):
        # Dependent Variable
        dep_frame = ttk.Labelframe(master, text="Dependent Variable (Y)")
        dep_combo = ttk.Combobox(dep_frame, textvariable=self.dependent_var, values=self.variables, state="readonly")
        dep_combo.pack(padx=5, pady=5)
        dep_frame.pack(fill="x", expand=True, pady=5)

        # Predictor Variables
        pred_frame = ttk.Labelframe(master, text="Predictor Variables (X)")
        listbox_frame = ttk.Frame(pred_frame, borderwidth=1, relief="sunken")
        self.listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE, height=8)

        for var in self.variables:
            self.listbox.insert(tk.END, var)

        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        listbox_frame.pack(fill="both", expand=True, padx=5, pady=5)
        pred_frame.pack(fill="x", expand=True, pady=5)

    def validate(self) -> bool:
        dep = self.dependent_var.get()
        selected_indices = self.listbox.curselection()
        if not dep:
            messagebox.showwarning("Incomplete Selection", "Please select a dependent variable.", parent=self)
            return False
        if not selected_indices:
            messagebox.showwarning(
                "Incomplete Selection", "Please select at least one predictor variable.", parent=self
            )
            return False

        predictors = [self.variables[i] for i in selected_indices]
        if dep in predictors:
            messagebox.showwarning(
                "Invalid Selection", "The dependent variable cannot also be a predictor.", parent=self
            )
            return False
        return True

    def apply(self):
        selected_indices = self.listbox.curselection()
        self.result = {
            "dependent": self.dependent_var.get(),
            "predictors": [self.variables[i] for i in selected_indices],
        }
