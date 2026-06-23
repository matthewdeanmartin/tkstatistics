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


class HistogramDialog(AnalysisDialog):
    """Dialog for choosing a variable and bin count for a histogram."""

    def __init__(self, master, variables: list[str]):
        self.variable = tk.StringVar()
        self.bins = tk.IntVar(value=10)
        super().__init__(master, title="Histogram", variables=variables)

    def create_body(self, master: ttk.Frame):
        var_frame = ttk.Labelframe(master, text="Variable")
        var_combo = ttk.Combobox(var_frame, textvariable=self.variable, values=self.variables, state="readonly")
        var_combo.pack(padx=5, pady=5)
        var_frame.pack(fill="x", expand=True, pady=5)

        bins_frame = ttk.Labelframe(master, text="Number of bins")
        bins_spin = ttk.Spinbox(bins_frame, from_=1, to=100, textvariable=self.bins, width=6)
        bins_spin.pack(padx=5, pady=5)
        bins_frame.pack(fill="x", expand=True, pady=5)

    def validate(self) -> bool:
        if not self.variable.get():
            messagebox.showwarning("No Selection", "Please select a variable.", parent=self)
            return False
        try:
            if self.bins.get() < 1:
                raise ValueError
        except (tk.TclError, ValueError):
            messagebox.showwarning("Invalid Bins", "Number of bins must be a positive integer.", parent=self)
            return False
        return True

    def apply(self):
        self.result = {"variable": self.variable.get(), "bins": self.bins.get()}


class OneSampleTTestDialog(AnalysisDialog):
    """Dialog for a one-sample t-test."""

    def __init__(self, master, variables: list[str]):
        self.variable = tk.StringVar()
        self.null_mean = tk.StringVar(value="0")
        self.alternative = tk.StringVar(value="two-sided")
        super().__init__(master, title="One-Sample t-test", variables=variables)

    def create_body(self, master: ttk.Frame):
        var_frame = ttk.Labelframe(master, text="Test Variable")
        ttk.Combobox(var_frame, textvariable=self.variable, values=self.variables, state="readonly").pack(padx=5, pady=5)
        var_frame.pack(fill="x", expand=True, pady=5)

        mean_frame = ttk.Labelframe(master, text="Null hypothesis mean (μ₀)")
        ttk.Entry(mean_frame, textvariable=self.null_mean, width=12).pack(padx=5, pady=5)
        mean_frame.pack(fill="x", expand=True, pady=5)

        alt_frame = ttk.Labelframe(master, text="Alternative")
        ttk.Combobox(
            alt_frame, textvariable=self.alternative,
            values=["two-sided", "less", "greater"], state="readonly",
        ).pack(padx=5, pady=5)
        alt_frame.pack(fill="x", expand=True, pady=5)

    def validate(self) -> bool:
        if not self.variable.get():
            messagebox.showwarning("No Selection", "Please select a test variable.", parent=self)
            return False
        try:
            float(self.null_mean.get())
        except ValueError:
            messagebox.showwarning("Invalid Value", "Null mean must be a number.", parent=self)
            return False
        return True

    def apply(self):
        self.result = {
            "variable": self.variable.get(),
            "null_mean": float(self.null_mean.get()),
            "alternative": self.alternative.get(),
        }


class TwoSampleDialog(AnalysisDialog):
    """Dialog for tests comparing two variables (independent t, Mann-Whitney, Wilcoxon)."""

    def __init__(self, master, variables: list[str], title: str, *, show_variance: bool = False):
        self.x_var = tk.StringVar()
        self.y_var = tk.StringVar()
        self.alternative = tk.StringVar(value="two-sided")
        self.variance = tk.StringVar(value="welch")
        self._show_variance = show_variance
        super().__init__(master, title=title, variables=variables)

    def create_body(self, master: ttk.Frame):
        x_frame = ttk.Labelframe(master, text="Variable 1 (X)")
        ttk.Combobox(x_frame, textvariable=self.x_var, values=self.variables, state="readonly").pack(padx=5, pady=5)
        x_frame.pack(fill="x", expand=True, pady=5)

        y_frame = ttk.Labelframe(master, text="Variable 2 (Y)")
        ttk.Combobox(y_frame, textvariable=self.y_var, values=self.variables, state="readonly").pack(padx=5, pady=5)
        y_frame.pack(fill="x", expand=True, pady=5)

        alt_frame = ttk.Labelframe(master, text="Alternative")
        ttk.Combobox(
            alt_frame, textvariable=self.alternative,
            values=["two-sided", "less", "greater"], state="readonly",
        ).pack(padx=5, pady=5)
        alt_frame.pack(fill="x", expand=True, pady=5)

        if self._show_variance:
            var_frame = ttk.Labelframe(master, text="Variance assumption")
            ttk.Combobox(
                var_frame, textvariable=self.variance,
                values=["welch", "pooled"], state="readonly",
            ).pack(padx=5, pady=5)
            var_frame.pack(fill="x", expand=True, pady=5)

    def validate(self) -> bool:
        if not self.x_var.get() or not self.y_var.get():
            messagebox.showwarning("Incomplete Selection", "Please select both variables.", parent=self)
            return False
        if self.x_var.get() == self.y_var.get():
            messagebox.showwarning("Invalid Selection", "The two variables must be different.", parent=self)
            return False
        return True

    def apply(self):
        self.result = {
            "x": self.x_var.get(),
            "y": self.y_var.get(),
            "alternative": self.alternative.get(),
            "variance_assumption": self.variance.get(),
        }


class FisherExactDialog(AnalysisDialog):
    """Dialog for entering a 2x2 contingency table for Fisher's exact test."""

    def __init__(self, master, variables: list[str]):
        self.cells = [[tk.StringVar(value="0") for _ in range(2)] for _ in range(2)]
        super().__init__(master, title="Fisher's Exact Test (2x2)", variables=variables)

    def create_body(self, master: ttk.Frame):
        ttk.Label(master, text="Enter the 2x2 contingency table counts:").grid(row=0, column=0, columnspan=3, pady=4)
        for r in range(2):
            for c in range(2):
                ttk.Entry(master, textvariable=self.cells[r][c], width=8).grid(row=r + 1, column=c + 1, padx=4, pady=4)
        ttk.Label(master, text="Row 1").grid(row=1, column=0)
        ttk.Label(master, text="Row 2").grid(row=2, column=0)

    def validate(self) -> bool:
        for row in self.cells:
            for var in row:
                try:
                    if int(var.get()) < 0:
                        raise ValueError
                except ValueError:
                    messagebox.showwarning("Invalid Value", "All cells must be non-negative integers.", parent=self)
                    return False
        return True

    def apply(self):
        self.result = {"table": [[int(self.cells[r][c].get()) for c in range(2)] for r in range(2)]}


class SingleVariableDialog(AnalysisDialog):
    """Generic dialog for picking exactly one variable (box plot, Q-Q plot)."""

    def __init__(self, master, variables: list[str], title: str = "Select Variable"):
        self.variable = tk.StringVar()
        super().__init__(master, title=title, variables=variables)

    def create_body(self, master: ttk.Frame):
        frame = ttk.Labelframe(master, text="Variable")
        combo = ttk.Combobox(frame, textvariable=self.variable, values=self.variables, state="readonly")
        combo.pack(padx=5, pady=5)
        frame.pack(fill="x", expand=True, pady=5)

    def validate(self) -> bool:
        if not self.variable.get():
            messagebox.showwarning("No Selection", "Please select a variable.", parent=self)
            return False
        return True

    def apply(self):
        self.result = {"variable": self.variable.get()}


class ScatterDialog(AnalysisDialog):
    """Dialog for a scatter plot: X, Y, and an optional fitted line."""

    def __init__(self, master, variables: list[str]):
        self.x_var = tk.StringVar()
        self.y_var = tk.StringVar()
        self.fit_line = tk.BooleanVar(value=False)
        super().__init__(master, title="Scatter Plot", variables=variables)

    def create_body(self, master: ttk.Frame):
        x_frame = ttk.Labelframe(master, text="X (horizontal)")
        ttk.Combobox(x_frame, textvariable=self.x_var, values=self.variables, state="readonly").pack(padx=5, pady=5)
        x_frame.pack(fill="x", expand=True, pady=5)

        y_frame = ttk.Labelframe(master, text="Y (vertical)")
        ttk.Combobox(y_frame, textvariable=self.y_var, values=self.variables, state="readonly").pack(padx=5, pady=5)
        y_frame.pack(fill="x", expand=True, pady=5)

        ttk.Checkbutton(master, text="Overlay fitted regression line", variable=self.fit_line).pack(anchor="w", pady=5)

    def validate(self) -> bool:
        if not self.x_var.get() or not self.y_var.get():
            messagebox.showwarning("Incomplete Selection", "Please select both X and Y variables.", parent=self)
            return False
        if self.x_var.get() == self.y_var.get():
            messagebox.showwarning("Invalid Selection", "X and Y cannot be the same variable.", parent=self)
            return False
        return True

    def apply(self):
        self.result = {"x": self.x_var.get(), "y": self.y_var.get(), "fit_line": self.fit_line.get()}


class MultiVariableDialog(AnalysisDialog):
    """Pick two or more variables (one-way ANOVA groups, correlation columns).

    When ``methods`` is provided, also offers a method chooser (e.g. Pearson vs
    Spearman for a correlation matrix).
    """

    def __init__(
        self,
        master,
        variables: list[str],
        title: str,
        *,
        prompt: str = "Select two or more variables:",
        methods: list[str] | None = None,
    ):
        self._prompt = prompt
        self._methods = methods
        self.method = tk.StringVar(value=methods[0] if methods else "")
        super().__init__(master, title=title, variables=variables)

    def create_body(self, master: ttk.Frame):
        ttk.Label(master, text=self._prompt).pack(anchor="w")

        listbox_frame = ttk.Frame(master, borderwidth=1, relief="sunken")
        self.listbox = tk.Listbox(listbox_frame, selectmode=tk.MULTIPLE, height=10)
        for var in self.variables:
            self.listbox.insert(tk.END, var)
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        listbox_frame.pack(fill="both", expand=True, pady=5)

        if self._methods:
            method_frame = ttk.Labelframe(master, text="Method")
            ttk.Combobox(
                method_frame, textvariable=self.method,
                values=self._methods, state="readonly",
            ).pack(padx=5, pady=5)
            method_frame.pack(fill="x", expand=True, pady=5)

    def validate(self) -> bool:
        if len(self.listbox.curselection()) < 2:
            messagebox.showwarning("Need More", "Please select at least two variables.", parent=self)
            return False
        return True

    def apply(self):
        selected = [self.variables[i] for i in self.listbox.curselection()]
        self.result = {"variables": selected}
        if self._methods:
            self.result["method"] = self.method.get()


_INFERENTIAL_TESTS = {
    "One-Sample t-test": "ttest_1samp",
    "Independent t-test": "ttest_ind",
    "Mann-Whitney U": "mann_whitney_u",
    "Wilcoxon Signed-Rank": "wilcoxon_signed_rank",
    "One-Way ANOVA": "one_way_anova",
}

# Tests whose inputs are an arbitrary number of group columns rather than the
# X/(Y) pair the rest of the dialog assumes.
_MULTI_GROUP_TESTS = {"one_way_anova"}


class DeclareHypothesisDialog(AnalysisDialog):
    """Dialog to pre-register a hypothesis and the confirmatory test for it.

    Captures the hypothesis statement, the test + variables + decision options,
    and alpha. The result is consumed by the app to build and commit a plan
    BEFORE the test is ever run — the anti-p-hacking ceremony.
    """

    def __init__(self, master, variables: list[str]):
        self.hypothesis = tk.StringVar()
        self.prediction = tk.StringVar()
        self.test_label = tk.StringVar(value="One-Sample t-test")
        self.x_var = tk.StringVar()
        self.y_var = tk.StringVar()
        self.null_mean = tk.StringVar(value="0")
        self.alternative = tk.StringVar(value="two-sided")
        self.variance = tk.StringVar(value="welch")
        self.alpha = tk.StringVar(value="0.05")
        super().__init__(master, title="Pre-register Hypothesis", variables=variables)

    def create_body(self, master: ttk.Frame):
        hyp_frame = ttk.Labelframe(master, text="Hypothesis (stated before seeing the result)")
        ttk.Entry(hyp_frame, textvariable=self.hypothesis, width=50).pack(padx=5, pady=5, fill="x")
        hyp_frame.pack(fill="x", expand=True, pady=4)

        pred_frame = ttk.Labelframe(master, text="Directional prediction (optional)")
        ttk.Entry(pred_frame, textvariable=self.prediction, width=50).pack(padx=5, pady=5, fill="x")
        pred_frame.pack(fill="x", expand=True, pady=4)

        test_frame = ttk.Labelframe(master, text="Confirmatory test")
        test_combo = ttk.Combobox(
            test_frame, textvariable=self.test_label,
            values=list(_INFERENTIAL_TESTS), state="readonly",
        )
        test_combo.pack(padx=5, pady=5)
        test_combo.bind("<<ComboboxSelected>>", lambda _e: self._sync_input_visibility())
        test_frame.pack(fill="x", expand=True, pady=4)

        self.var_frame = ttk.Labelframe(master, text="Variables")
        ttk.Label(self.var_frame, text="X / data:").grid(row=0, column=0, sticky="e", padx=3, pady=3)
        ttk.Combobox(self.var_frame, textvariable=self.x_var, values=self.variables, state="readonly", width=18).grid(row=0, column=1, padx=3, pady=3)
        ttk.Label(self.var_frame, text="Y (two-sample):").grid(row=1, column=0, sticky="e", padx=3, pady=3)
        ttk.Combobox(self.var_frame, textvariable=self.y_var, values=self.variables, state="readonly", width=18).grid(row=1, column=1, padx=3, pady=3)
        self.var_frame.pack(fill="x", expand=True, pady=4)

        self.groups_frame = ttk.Labelframe(master, text="Groups (two or more columns to compare)")
        groups_inner = ttk.Frame(self.groups_frame, borderwidth=1, relief="sunken")
        self.groups_listbox = tk.Listbox(groups_inner, selectmode=tk.MULTIPLE, height=6)
        for var in self.variables:
            self.groups_listbox.insert(tk.END, var)
        groups_scroll = ttk.Scrollbar(groups_inner, orient=tk.VERTICAL, command=self.groups_listbox.yview)
        self.groups_listbox.config(yscrollcommand=groups_scroll.set)
        groups_scroll.pack(side="right", fill="y")
        self.groups_listbox.pack(side="left", fill="both", expand=True)
        groups_inner.pack(fill="both", expand=True, padx=5, pady=5)
        # var_frame / groups_frame are packed/unpacked dynamically by
        # _sync_input_visibility() once opt_frame (their pack anchor) exists.

        self.opt_frame = ttk.Labelframe(master, text="Decision options")
        opt_frame = self.opt_frame
        ttk.Label(opt_frame, text="Null mean (μ₀):").grid(row=0, column=0, sticky="e", padx=3, pady=3)
        ttk.Entry(opt_frame, textvariable=self.null_mean, width=10).grid(row=0, column=1, padx=3, pady=3)
        ttk.Label(opt_frame, text="Alternative:").grid(row=1, column=0, sticky="e", padx=3, pady=3)
        ttk.Combobox(opt_frame, textvariable=self.alternative, values=["two-sided", "less", "greater"], state="readonly", width=10).grid(row=1, column=1, padx=3, pady=3)
        ttk.Label(opt_frame, text="Variance:").grid(row=2, column=0, sticky="e", padx=3, pady=3)
        ttk.Combobox(opt_frame, textvariable=self.variance, values=["welch", "pooled"], state="readonly", width=10).grid(row=2, column=1, padx=3, pady=3)
        ttk.Label(opt_frame, text="Alpha (α):").grid(row=3, column=0, sticky="e", padx=3, pady=3)
        ttk.Entry(opt_frame, textvariable=self.alpha, width=10).grid(row=3, column=1, padx=3, pady=3)
        opt_frame.pack(fill="x", expand=True, pady=4)

        # Now that the anchor frame exists, show the inputs for the default test.
        self._sync_input_visibility()

    def _sync_input_visibility(self):
        """Show the group listbox for ANOVA, the X/Y pickers for everything else.

        ANOVA has no decision options, so its option frame is hidden too (alpha
        is still captured — it is collected separately below the frame layout).
        """
        analysis = _INFERENTIAL_TESTS[self.test_label.get()]
        if analysis in _MULTI_GROUP_TESTS:
            self.var_frame.pack_forget()
            self.groups_frame.pack(before=self.opt_frame, fill="both", expand=True, pady=4)
        else:
            self.groups_frame.pack_forget()
            self.var_frame.pack(before=self.opt_frame, fill="x", expand=True, pady=4)

    def _selected_groups(self) -> list[str]:
        return [self.variables[i] for i in self.groups_listbox.curselection()]

    def validate(self) -> bool:
        if not self.hypothesis.get().strip():
            messagebox.showwarning("Missing Hypothesis", "Please state your hypothesis first.", parent=self)
            return False
        analysis = _INFERENTIAL_TESTS[self.test_label.get()]
        if analysis in _MULTI_GROUP_TESTS:
            if len(self._selected_groups()) < 2:
                messagebox.showwarning("Need More", "ANOVA needs at least two group columns.", parent=self)
                return False
            return self._validate_alpha()
        if not self.x_var.get():
            messagebox.showwarning("Missing Variable", "Please select the X / data variable.", parent=self)
            return False
        if analysis in ("ttest_ind", "mann_whitney_u", "wilcoxon_signed_rank"):
            if not self.y_var.get():
                messagebox.showwarning("Missing Variable", "This test needs a second (Y) variable.", parent=self)
                return False
            if self.x_var.get() == self.y_var.get():
                messagebox.showwarning("Invalid Selection", "X and Y must differ.", parent=self)
                return False
        if not self._validate_alpha():
            return False
        if analysis == "ttest_1samp":
            try:
                float(self.null_mean.get())
            except ValueError:
                messagebox.showwarning("Invalid Value", "Null mean must be a number.", parent=self)
                return False
        return True

    def _validate_alpha(self) -> bool:
        try:
            if not (0.0 < float(self.alpha.get()) < 1.0):
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid Alpha", "Alpha must be a number between 0 and 1.", parent=self)
            return False
        return True

    def apply(self):
        analysis = _INFERENTIAL_TESTS[self.test_label.get()]
        if analysis == "ttest_1samp":
            inputs = {"data": self.x_var.get()}
            options = {"null_mean": float(self.null_mean.get()), "alternative": self.alternative.get()}
        elif analysis == "ttest_ind":
            inputs = {"x": self.x_var.get(), "y": self.y_var.get()}
            options = {"alternative": self.alternative.get(), "variance_assumption": self.variance.get()}
        elif analysis in _MULTI_GROUP_TESTS:  # one_way_anova
            inputs = {"groups": self._selected_groups()}
            options = {}
        else:  # mann_whitney_u, wilcoxon_signed_rank
            inputs = {"x": self.x_var.get(), "y": self.y_var.get()}
            options = {}

        self.result = {
            "analysis": analysis,
            "inputs": inputs,
            "options": options,
            "hypothesis": self.hypothesis.get().strip(),
            "prediction": self.prediction.get().strip(),
            "alpha": float(self.alpha.get()),
        }


class SelectPlanDialog(AnalysisDialog):
    """Dialog to pick a committed pre-registration plan to run confirmatorily."""

    def __init__(self, master, plans: list[dict]):
        self._plans = plans
        super().__init__(master, title="Run Confirmatory Test", variables=[])

    def create_body(self, master: ttk.Frame):
        ttk.Label(master, text="Select a pre-registered plan to reveal its result:").pack(anchor="w")
        listbox_frame = ttk.Frame(master, borderwidth=1, relief="sunken")
        self.listbox = tk.Listbox(listbox_frame, height=8, width=60)
        for plan in self._plans:
            label = f"[{plan['analysis']}] {plan.get('hypothesis', '')[:50]}"
            self.listbox.insert(tk.END, label)
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        listbox_frame.pack(fill="both", expand=True, pady=5)

    def validate(self) -> bool:
        if not self.listbox.curselection():
            messagebox.showwarning("No Selection", "Please select a plan.", parent=self)
            return False
        return True

    def apply(self):
        self.result = {"plan": self._plans[self.listbox.curselection()[0]]}


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
