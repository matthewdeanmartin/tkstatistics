# tkstatistics/app/main.py

from __future__ import annotations

import os
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from tkstatistics.core import specs
from tkstatistics.core.dataset import TabularData
from tkstatistics.core.io_csv import import_csv
from tkstatistics.core.project import Project
from tkstatistics.stats import descriptives, regression

from .demo import create_demo_dataset
from .dialogs import DescriptivesDialog, MultipleRegressionDialog, SimpleRegressionDialog
from .grid import DataGrid
from .output_viewer import OutputViewer
from .project_explorer import ProjectExplorer


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("tkstatistics")
        self.geometry("1100x750")

        self.project: Project | None = None
        self.active_dataset: TabularData | None = None
        self._temp_project_path: str | None = None

        self._create_widgets()
        self._create_menus()
        self._load_insta_demo()
        self._update_ui_state()
        self.protocol("WM_DELETE_WINDOW", self._on_close)


    def _on_dataset_selected(self, name: str):
        """Callback from ProjectExplorer when a dataset is clicked."""
        self._load_dataset_into_grid(name)

    def _create_widgets(self):
        """Creates the main 3-pane window layout."""
        # Main container is a horizontal paned window
        main_pane = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_pane.pack(fill="both", expand=True, padx=5, pady=5)

        # Left pane: Project Explorer
        self.project_explorer = ProjectExplorer(main_pane)
        # Wire up the callbacks from the explorer to methods in this class
        self.project_explorer.on_select_dataset = self._on_dataset_selected
        self.project_explorer.on_select_analysis = self._on_analysis_selected
        main_pane.add(self.project_explorer, weight=1)

        right_pane = ttk.PanedWindow(main_pane, orient=tk.VERTICAL)
        main_pane.add(right_pane, weight=4)

        self.data_grid = DataGrid(right_pane)
        right_pane.add(self.data_grid, weight=3)

        self.output_viewer = OutputViewer(right_pane)
        right_pane.add(self.output_viewer, weight=2)

        # Status Bar
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self, textvariable=self.status_var, anchor="w", relief=tk.SUNKEN)
        status_bar.pack(side="bottom", fill="x")

    def _set_project(self, project: Project):
        """Central method to set a new project and update the UI."""
        self._clean_up_temp_project()
        self.project = project
        self.title(f"tkstatistics - {project.filepath.name}")
        self.project_explorer.populate(project)

        datasets = project.list_datasets()
        if datasets:
            self._load_dataset_into_grid(datasets[0])
        else:
            self.active_dataset = None
            self.data_grid.clear()
            self.status_var.set(f"Project '{project.filepath.name}' loaded. No datasets found.")
        self._update_ui_state()

    def _load_dataset_into_grid(self, name: str):
        """Loads a dataset from the project and displays it."""
        if not self.project:
            return
        try:
            self.active_dataset = self.project.load_dataset(name)
            self.data_grid.display_data(self.active_dataset)
            rows, cols = self.active_dataset.shape
            self.status_var.set(f"Active dataset: '{name}' ({rows} rows x {cols} columns).")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dataset '{name}':\n{e}")
        self._update_ui_state()

    def _on_dataset_selected(self, name: str):
        """Callback from ProjectExplorer when a dataset is clicked."""
        self._load_dataset_into_grid(name)

    def _on_analysis_selected(self, spec: dict[str, Any]):
        """Callback from ProjectExplorer when a past analysis is clicked."""
        self._execute_and_display_spec(spec)

    def _execute_and_display_spec(self, spec: dict[str, Any]):
        """Central function to run an analysis from a spec and display its results."""
        if not self.project:
            return

        # 1. Ensure the correct dataset is active
        dataset_name = spec.get("dataset")
        if not dataset_name or not self.active_dataset or self.active_dataset.name != dataset_name:
            self._load_dataset_into_grid(dataset_name)
        if not self.active_dataset:
            messagebox.showerror("Error", f"Dataset '{dataset_name}' for this analysis could not be loaded.")
            return

        # 2. Get the analysis function and prepare arguments
        try:
            analysis_name = spec["analysis"]
            analysis_func = specs.ANALYSIS_DISPATCHER[analysis_name]

            # Prepare keyword arguments from the spec's 'inputs'
            kwargs = {}
            for role, var_name_or_list in spec.get("inputs", {}).items():
                if isinstance(var_name_or_list, list):  # For multiple predictors
                    kwargs[role] = [self.active_dataset.get_column(v) for v in var_name_or_list]
                else:
                    kwargs[role] = self.active_dataset.get_column(var_name_or_list)

            # For multiple regression, the `ols` function expects rows, not columns
            if analysis_name == "ols":
                kwargs["X"] = list(zip(*kwargs["X"], strict=False))

            # 3. Run the analysis
            results = analysis_func(**kwargs)

            # 4. Format and display results
            if analysis_name == "describe":
                var_name = spec["inputs"]["data"]
                output_text = self._format_descriptives_results(var_name, results)
                title = f"Descriptives: {var_name}"
            elif analysis_name == "stdlib_simple_regression":
                dep_var, ind_var = spec["inputs"]["y"], spec["inputs"]["x"]
                output_text = self._format_regression_results("Simple Linear Regression (stdlib)", dep_var, [ind_var],
                                                              results)
                title = f"Simple Regression: {dep_var} on {ind_var}"
            elif analysis_name == "ols":
                dep_var, pred_vars = spec["inputs"]["y"], spec["inputs"]["X"]
                output_text = self._format_regression_results("Multiple Linear Regression (OLS)", dep_var, pred_vars,
                                                              results)
                title = f"Multiple Regression: {dep_var}"
            else:
                title = "Analysis Result"
                output_text = str(results)  # Fallback formatting

            self.output_viewer.add_result(title, output_text)

        except Exception as e:
            messagebox.showerror("Analysis Error", f"Failed to re-run analysis:\n{e}", parent=self)

    def _run_descriptives(self):
        if not self.active_dataset:
            return
        dialog = DescriptivesDialog(self, self.active_dataset.column_names)
        selected_vars = dialog.result
        if not selected_vars:
            return

        for var_name in selected_vars:
            # Create the spec BEFORE running the analysis
            spec = specs.create_spec("describe", self.active_dataset.name, inputs={"data": var_name}, options={})
            self.project.save_analysis(spec)
            self.project_explorer.populate(self.project)
            self._execute_and_display_spec(spec)  # Use the central executor

    def _run_simple_regression(self):
        if not self.active_dataset:
            return
        dialog = SimpleRegressionDialog(self, self.active_dataset.column_names)
        selections = dialog.result
        if not selections:
            return

        dep_var, ind_var = selections["dependent"], selections["independent"]
        spec = specs.create_spec("stdlib_simple_regression", self.active_dataset.name,
                                 inputs={"y": dep_var, "x": ind_var}, options={})
        self.project.save_analysis(spec)
        self.project_explorer.populate(self.project)
        self._execute_and_display_spec(spec)  # Use the central executor

    def _run_multiple_regression(self):
        if not self.active_dataset:
            return
        dialog = MultipleRegressionDialog(self, self.active_dataset.column_names)
        selections = dialog.result
        if not selections:
            return

        dep_var, pred_vars = selections["dependent"], selections["predictors"]
        # Note: The input role for multiple predictors is 'X', matching the OLS function signature
        spec = specs.create_spec("ols", self.active_dataset.name, inputs={"y": dep_var, "X": pred_vars}, options={})
        self.project.save_analysis(spec)
        self.project_explorer.populate(self.project)
        self._execute_and_display_spec(spec)  # Use the central executor

    # --- Boilerplate methods for file IO, menus, and state management (mostly unchanged) ---
    def _create_menus(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Project...", command=self._new_project)
        file_menu.add_command(label="Open Project...", command=self._open_project)
        file_menu.add_separator()
        self.import_csv_menu_index = file_menu.index("end") + 1
        file_menu.add_command(label="Import CSV...", command=self._import_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_close)
        self.file_menu = file_menu
        analyze_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Analyze", menu=analyze_menu)
        analyze_menu.add_command(label="Descriptives...", command=self._run_descriptives)
        analyze_menu.add_separator()
        reg_menu = tk.Menu(analyze_menu, tearoff=0)
        analyze_menu.add_cascade(label="Regression", menu=reg_menu)
        reg_menu.add_command(label="Simple Linear (stdlib)...", command=self._run_simple_regression)
        reg_menu.add_command(label="Multiple Linear (OLS)...", command=self._run_multiple_regression)
        self.analyze_menu = analyze_menu
        graphs_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Graphs", menu=graphs_menu)
        graphs_menu.add_command(label="Histogram...")
        self.graphs_menu = graphs_menu

    def _new_project(self):
        path = filedialog.asksaveasfilename(
            title="Create New Project", defaultextension=".statproj", filetypes=[("tkstatistics Project", "*.statproj")]
        )
        if path:
            self._set_project(Project(path))

    def _open_project(self):
        path = filedialog.askopenfilename(title="Open Project", filetypes=[("tkstatistics Project", "*.statproj")])
        if path:
            self._set_project(Project(path))

    def _import_csv(self):
        if not self.project:
            messagebox.showerror("Error", "No project is open.")
            return
        path = filedialog.askopenfilename(title="Import CSV File", filetypes=[("CSV Files", "*.csv")])
        if not path:
            return
        try:
            new_dataset = import_csv(Path(path))
            self.project.save_dataset(new_dataset)
            self.project_explorer.populate(self.project)
            self._load_dataset_into_grid(new_dataset.name)
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import file:\n{e}")

    def _load_insta_demo(self):
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix=".statproj", delete=False)
            self._temp_project_path = temp_file.name
            temp_file.close()
            demo_project = Project(self._temp_project_path)
            demo_data = create_demo_dataset()
            demo_project.save_dataset(demo_data)
            self._set_project(demo_project)
        except Exception as e:
            messagebox.showerror("Demo Load Error", f"Failed to create demo project:\n{e}")

    def _on_close(self):
        self._clean_up_temp_project()
        self.destroy()

    def _clean_up_temp_project(self):
        if self.project and self._temp_project_path:
            self.project.close()
            self.project = None
            try:
                os.remove(self._temp_project_path)
                self._temp_project_path = None
            except OSError:
                pass

    def _update_ui_state(self):
        project_loaded = self.project is not None
        data_loaded = self.active_dataset is not None
        self.file_menu.entryconfig(self.import_csv_menu_index, state=tk.NORMAL if project_loaded else tk.DISABLED)
        self.menu_bar.entryconfig("Analyze", state=tk.NORMAL if data_loaded else tk.DISABLED)
        self.menu_bar.entryconfig("Graphs", state=tk.NORMAL if data_loaded else tk.DISABLED)

    def _format_descriptives_results(self, var_name: str, results: dict[str, Any]) -> str:
        lines = [f"Descriptive Statistics: {var_name}\n"]
        if results.get("mean") is None:
            return "\n".join(lines + [f"  N: {results['n']}", f"  Missing: {results['missing']}",
                                      "\n(No valid data to compute statistics)"])
        lines.extend([
            f"  N: {results['n']} (Missing: {results['missing']})",
            f"  Mean: {results['mean']:.4f}", f"  Median: {results['median']:.4f}",
            f"  Std. Deviation: {results['stdev']:.4f}", f"  Variance: {results['variance']:.4f}",
            f"  Min: {results['min']:.4f}", f"  Max: {results['max']:.4f}", f"  IQR: {results['iqr']:.4f}"
        ])
        return "\n".join(lines)

    def _format_regression_results(self, title: str, dep_var: str, pred_vars: list[str],
                                   results: dict[str, Any]) -> str:
        if "error" in results:
            return f"{title}\n\nError: {results['error']}\nDetails: {results.get('details', 'N/A')}"
        lines = [
            f"{title}", f"Dependent Variable: {dep_var}\n",
            f"R-squared: {results['r_squared']:.4f}", f"Adjusted R-squared: {results['adj_r_squared']:.4f}",
            f"Observations: {results['n']}\n",
            f"{'Variable':<15} {'Coefficient':>12} {'Std. Error':>12} {'t-statistic':>12}",
            "-" * 53
        ]
        lines.append(
            f"{'(Intercept)':<15} {results['coefficients'][0]:>12.4f} {results['std_errors'][0]:>12.4f} {results['t_statistics'][0]:>12.3f}")
        for i, var_name in enumerate(pred_vars):
            lines.append(
                f"{var_name:<15} {results['coefficients'][i + 1]:>12.4f} {results['std_errors'][i + 1]:>12.4f} {results['t_statistics'][i + 1]:>12.3f}")
        lines.append(f"\n{results['notes']}")
        return "\n".join(lines)


def launch_app():
    app = App()
    app.mainloop()
