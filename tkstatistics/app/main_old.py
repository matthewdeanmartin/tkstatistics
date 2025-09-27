# tkstatistics/app/main.py

"""
The main application window for tkstatistics.
"""
from __future__ import annotations

import os
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Optional

from tkstatistics.core.dataset import TabularData
from tkstatistics.core.io_csv import import_csv
from tkstatistics.core.project import Project

# Import both stats modules
from tkstatistics.stats import descriptives, regression

from .demo import create_demo_dataset, get_demo_spec
from .dialogs import DescriptivesDialog, MultipleRegressionDialog, SimpleRegressionDialog
from .grid import DataGrid
from .output_viewer import OutputViewer  # <-- Import the new viewer


class App(tk.Tk):
    """The main application class."""

    def __init__(self):
        super().__init__()
        self.title("tkstatistics - No Project")
        self.geometry("900x700")  # Made the window a bit bigger

        self.project: Optional[Project] = None
        self.active_dataset: Optional[TabularData] = None
        self.demo_spec: Optional[Dict[str, Any]] = None
        self._temp_project_path: Optional[str] = None

        self._create_widgets()
        self._create_menus()

        # --- Insta-Demo on startup ---
        self._load_insta_demo()

        self._update_ui_state()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _load_insta_demo(self):
        """Creates and loads a temporary project with sample data on startup."""
        try:
            # Create a temporary file that will be deleted on close
            temp_file = tempfile.NamedTemporaryFile(suffix=".statproj", delete=False)
            self._temp_project_path = temp_file.name
            temp_file.close()

            self.project = Project(self._temp_project_path)
            self.title("tkstatistics - Insta-Demo Project")

            # Generate and save data
            demo_data = create_demo_dataset()
            self.project.save_dataset(demo_data)
            self.active_dataset = demo_data

            # Load demo spec into memory
            self.demo_spec = get_demo_spec()

            # Display data and update UI
            self.data_grid.display_data(self.active_dataset)
            rows, cols = self.active_dataset.shape
            self.status_var.set(
                f"Demo data '{self.active_dataset.name}' loaded. Dimensions: {rows} rows x {cols} columns."
            )

        except Exception as e:
            messagebox.showerror("Demo Load Error", f"Failed to create demo project:\n{e}")
            self.status_var.set("Failed to load insta-demo.")

    def _create_widgets(self):
        """Creates the main window layout with a paned view."""
        # Main container will be a paned window
        main_pane = ttk.PanedWindow(self, orient=tk.VERTICAL)
        main_pane.pack(fill="both", expand=True, padx=5, pady=5)

        # Top pane: Data Grid
        self.data_grid = DataGrid(main_pane)
        main_pane.add(self.data_grid, weight=3)  # Give more initial space to grid

        # Bottom pane: Output Viewer
        self.output_viewer = OutputViewer(main_pane)
        main_pane.add(self.output_viewer, weight=2)

        # Status Bar
        self.status_var = tk.StringVar(value="Welcome to tkstatistics!")
        status_bar = ttk.Label(self, textvariable=self.status_var, anchor="w", relief=tk.SUNKEN)
        status_bar.pack(side="bottom", fill="x")

    # ... (_create_menus, _load_insta_demo, and other methods are mostly the same) ...

    def _run_descriptives(self):
        """Launch dialog, run analysis, and send results to the OutputViewer."""
        if not self.active_dataset:
            return

        dialog = DescriptivesDialog(self, self.active_dataset.column_names)
        selected_vars = dialog.result
        if not selected_vars:
            return

        for var_name in selected_vars:
            data_column = self.active_dataset.get_column(var_name)
            results = descriptives.describe(data_column)

            output_text = self._format_descriptives_results(var_name, results)
            title = f"Descriptives: {var_name}"

            # Send result to the new viewer instead of a messagebox
            self.output_viewer.add_result(title, output_text)

    def _run_simple_regression(self):
        """Handle the simple linear regression workflow."""
        if not self.active_dataset:
            return

        dialog = SimpleRegressionDialog(self, self.active_dataset.column_names)
        selections = dialog.result
        if not selections:
            return

        dep_var = selections["dependent"]
        ind_var = selections["independent"]

        y_data = self.active_dataset.get_column(dep_var)
        x_data = self.active_dataset.get_column(ind_var)

        results = regression.stdlib_simple_regression(x_data, y_data)

        title = f"Simple Regression: {dep_var}"
        output_text = self._format_regression_results("Simple Linear Regression (stdlib)", dep_var, [ind_var], results)

        # Send result to the new viewer
        self.output_viewer.add_result(title, output_text)

    def _run_multiple_regression(self):
        """Handle the multiple linear regression workflow."""
        if not self.active_dataset:
            return

        dialog = MultipleRegressionDialog(self, self.active_dataset.column_names)
        selections = dialog.result
        if not selections:
            return

        dep_var = selections["dependent"]
        pred_vars = selections["predictors"]

        y_data = self.active_dataset.get_column(dep_var)
        X_data = [self.active_dataset.get_column(p) for p in pred_vars]
        X_data_rows = list(zip(*X_data))

        results = regression.ols(X_data_rows, y_data)

        title = f"Multiple Regression: {dep_var}"
        output_text = self._format_regression_results("Multiple Linear Regression (OLS)", dep_var, pred_vars, results)

        # Send result to the new viewer
        self.output_viewer.add_result(title, output_text)

    # --- (The rest of main.py remains the same as the previous version) ---
    def _create_menus(self):
        """Creates the main application menu bar."""
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        # --- File Menu ---
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project...", command=self._new_project)
        file_menu.add_command(label="Open Project...", command=self._open_project)
        file_menu.add_separator()
        self.import_csv_menu_index = file_menu.index("end") + 1  # Get index for state changes
        file_menu.add_command(label="Import CSV...", command=self._import_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        # which one?
        # file_menu.add_command(label="Exit", command=self._on_close)
        self.file_menu = file_menu

        # --- Analyze Menu ---
        analyze_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Analyze", menu=analyze_menu)
        analyze_menu.add_command(label="Descriptives...", command=self._run_descriptives)
        analyze_menu.add_separator()
        reg_menu = tk.Menu(analyze_menu, tearoff=0)
        analyze_menu.add_cascade(label="Regression", menu=reg_menu)
        reg_menu.add_command(label="Simple Linear (stdlib)...", command=self._run_simple_regression)
        reg_menu.add_command(label="Multiple Linear (OLS)...", command=self._run_multiple_regression)
        self.analyze_menu = analyze_menu

        # --- Graphs Menu (initially disabled) ---
        graphs_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Graphs", menu=graphs_menu)
        graphs_menu.add_command(label="Histogram...")  # command to be added later
        self.graphs_menu = graphs_menu

    def _update_ui_state(self):
        """Enable/disable menus based on application state (e.g., project open)."""
        project_loaded = self.project is not None
        data_loaded = self.active_dataset is not None

        # File menu items
        self.file_menu.entryconfig(self.import_csv_menu_index, state=tk.NORMAL if project_loaded else tk.DISABLED)

        # Top-level menus
        self.menu_bar.entryconfig("Analyze", state=tk.NORMAL if data_loaded else tk.DISABLED)
        self.menu_bar.entryconfig("Graphs", state=tk.NORMAL if data_loaded else tk.DISABLED)

    def _clean_up_temp_project(self):
        """Closes project connection and deletes the temporary project file."""
        if self.project:
            self.project.close()
            self.project = None

        if self._temp_project_path:
            try:
                os.remove(self._temp_project_path)
                self._temp_project_path = None
            except OSError:
                # File might not exist or be locked, fail silently
                pass

    def _on_close(self):
        """Handles application shutdown."""
        self._clean_up_temp_project()
        self.destroy()

    def _new_project(self):
        path = filedialog.asksaveasfilename(
            title="Create New Project",
            defaultextension=".statproj",
            filetypes=[("tkstatistics Project", "*.statproj"), ("All Files", "*.*")],
        )
        if path:
            self._clean_up_temp_project()  # Get rid of demo project
            self.project = Project(path)
            self.title(f"tkstatistics - {Path(path).name}")
            self.status_var.set(f"Project created at {path}")
            self.active_dataset = None
            self.data_grid.clear()
            self.output_viewer.tree.delete(*self.output_viewer.tree.get_children())
            self.output_viewer.results_map.clear()
            self._update_ui_state()

    def _open_project(self):
        path = filedialog.askopenfilename(
            title="Open Project", filetypes=[("tkstatistics Project", "*.statproj"), ("All Files", "*.* ")]
        )
        if path:
            self._clean_up_temp_project()  # Get rid of demo project
            self.project = Project(path)
            self.title(f"tkstatistics - {Path(path).name}")
            self.status_var.set(f"Project opened from {path}")
            self.active_dataset = None
            self.data_grid.clear()
            self.output_viewer.tree.delete(*self.output_viewer.tree.get_children())
            self.output_viewer.results_map.clear()
            self._update_ui_state()

    def _import_csv(self):
        if not self.project:
            messagebox.showerror("Error", "No project is open. Please create or open a project first.")
            return

        path = filedialog.askopenfilename(
            title="Import CSV File", filetypes=[("CSV Files", "*.csv"), ("TSV Files", "*.tsv"), ("All Files", "*.*")]
        )
        if not path:
            return

        try:
            new_dataset = import_csv(Path(path))
            self.project.save_dataset(new_dataset)
            self.active_dataset = new_dataset
            self.data_grid.display_data(self.active_dataset)
            rows, cols = self.active_dataset.shape
            self.status_var.set(f"Loaded '{self.active_dataset.name}'. Dimensions: {rows} rows x {cols} columns.")
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import file:\n{e}")
            self.status_var.set("CSV import failed.")

        self._update_ui_state()

    def _format_descriptives_results(self, var_name: str, results: Dict[str, Any]) -> str:
        """Formats the results of the describe function into a nice string."""
        lines = [f"Descriptive Statistics: {var_name}\n"]

        if results.get("mean") is None:
            lines.append(f"  N: {results['n']}")
            lines.append(f"  Missing: {results['missing']}")
            lines.append("\n(No valid data to compute statistics)")
            return "\n".join(lines)

        lines.append(f"  N: {results['n']} (Missing: {results['missing']})")
        lines.append(f"  Mean: {results['mean']:.4f}")
        lines.append(f"  Median: {results['median']:.4f}")
        lines.append(f"  Std. Deviation: {results['stdev']:.4f}")
        lines.append(f"  Variance: {results['variance']:.4f}")
        lines.append(f"  Min: {results['min']:.4f}")
        lines.append(f"  Max: {results['max']:.4f}")
        lines.append(f"  IQR: {results['iqr']:.4f}")

        return "\n".join(lines)

    def _run_descriptives_popup(self):
        """Launch dialog, run analysis, and show results."""
        if not self.active_dataset:
            return

        dialog = DescriptivesDialog(self, self.active_dataset.column_names)

        # The main app waits here until the dialog is closed.
        # The dialog's `apply` method sets `dialog.result`.
        selected_vars = dialog.result

        if not selected_vars:
            # User cancelled or selected nothing
            return

        # --- Process results ---
        full_results_text = []
        for var_name in selected_vars:
            data_column = self.active_dataset.get_column(var_name)
            results = descriptives.describe(data_column)
            full_results_text.append(self._format_descriptives_results(var_name, results))

        # For now, display results in a simple message box.
        # This will be replaced by the Output Viewer later.
        messagebox.showinfo("Descriptive Statistics", "\n\n---\n\n".join(full_results_text), parent=self)

    # --- New Methods for Regression ---

    def _format_regression_results(
        self, title: str, dep_var: str, pred_vars: List[str], results: Dict[str, Any]
    ) -> str:
        """Formats the results of a regression analysis into a string."""
        if "error" in results:
            return f"{title}\n\nError: {results['error']}\nDetails: {results.get('details', 'N/A')}"

        lines = [f"{title}", f"Dependent Variable: {dep_var}\n"]
        lines.append(f"R-squared: {results['r_squared']:.4f}")
        lines.append(f"Adjusted R-squared: {results['adj_r_squared']:.4f}")
        lines.append(f"Observations: {results['n']}\n")
        lines.append(f"{'Variable':<15} {'Coefficient':>12} {'Std. Error':>12} {'t-statistic':>12}")
        lines.append("-" * 53)

        # Intercept
        lines.append(
            f"{'(Intercept)':<15} {results['coefficients'][0]:>12.4f} {results['std_errors'][0]:>12.4f} {results['t_statistics'][0]:>12.3f}"
        )

        # Predictors
        for i, var_name in enumerate(pred_vars):
            lines.append(
                f"{var_name:<15} {results['coefficients'][i + 1]:>12.4f} {results['std_errors'][i + 1]:>12.4f} {results['t_statistics'][i + 1]:>12.3f}"
            )

        lines.append(f"\n{results['notes']}")
        return "\n".join(lines)

    def _run_simple_regression_popup(self):
        """Handle the simple linear regression workflow."""
        if not self.active_dataset:
            return

        dialog = SimpleRegressionDialog(self, self.active_dataset.column_names)
        selections = dialog.result

        if not selections:
            return

        dep_var = selections["dependent"]
        ind_var = selections["independent"]

        y_data = self.active_dataset.get_column(dep_var)
        x_data = self.active_dataset.get_column(ind_var)

        results = regression.stdlib_simple_regression(x_data, y_data)

        output_text = self._format_regression_results("Simple Linear Regression (stdlib)", dep_var, [ind_var], results)
        messagebox.showinfo("Regression Results", output_text, parent=self)

    def _run_multiple_regression_popup(self):
        """Handle the multiple linear regression workflow."""
        if not self.active_dataset:
            return

        dialog = MultipleRegressionDialog(self, self.active_dataset.column_names)
        selections = dialog.result

        if not selections:
            return

        dep_var = selections["dependent"]
        pred_vars = selections["predictors"]

        y_data = self.active_dataset.get_column(dep_var)
        X_data = [self.active_dataset.get_column(p) for p in pred_vars]
        # Transpose X_data from list-of-cols to list-of-rows for the ols function
        X_data_rows = list(zip(*X_data))

        results = regression.ols(X_data_rows, y_data)

        output_text = self._format_regression_results("Multiple Linear Regression (OLS)", dep_var, pred_vars, results)
        messagebox.showinfo("Regression Results", output_text, parent=self)


def launch_app():
    """Initializes and runs the main application loop."""
    app = App()
    app.mainloop()
