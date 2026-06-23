# tkstatistics/app/main.py

from __future__ import annotations

import os
import tempfile
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any

from tkstatistics.core import plans, render, specs
from tkstatistics.core.dataset import TabularData
from tkstatistics.core.io_csv import import_csv
from tkstatistics.core.project import Project

from .chart_window import ChartWindow
from .demo import create_demo_dataset
from .dialogs import (
    DeclareHypothesisDialog,
    DescriptivesDialog,
    FisherExactDialog,
    HistogramDialog,
    MultipleRegressionDialog,
    MultiVariableDialog,
    OneSampleTTestDialog,
    ScatterDialog,
    SelectPlanDialog,
    SimpleRegressionDialog,
    SingleVariableDialog,
    TwoSampleDialog,
)
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
        self.project_explorer.on_select_plan = self._on_plan_selected
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

    def _on_plan_selected(self, plan: dict[str, Any]):
        """Callback from ProjectExplorer when a pre-registered plan is clicked."""
        lines = [
            "Pre-registered Plan",
            "",
            f"  Plan id     : {plans.plan_id(plan)}",
            f"  Hypothesis  : {plan.get('hypothesis', '')}",
        ]
        if plan.get("prediction"):
            lines.append(f"  Prediction  : {plan['prediction']}")
        lines.extend([
            f"  Test        : {plan.get('analysis', '')}",
            f"  Dataset     : {plan.get('dataset', '')}",
            f"  Inputs      : {plan.get('inputs', {})}",
            f"  Decision opts: {plan.get('decision_options', {})}",
            f"  Alpha       : {plan.get('alpha')}",
            "",
            "  Use Analyze ▸ Run Confirmatory Test... to reveal the result.",
        ])
        self.output_viewer.add_result(
            f"Plan: {plan.get('analysis', '')}",
            "\n".join(lines),
            result_key=f"plan::{plans.plan_id(plan)}",
        )

    def _execute_and_display_spec(self, spec: dict[str, Any]):
        """Central function to run an analysis from a spec and display its results.

        Runs through the same ``run_spec_payload`` pipeline the CLI uses, so the
        GUI gets reproducible artifacts, multiplicity correction, and the
        confirmatory pre-registration gate for free. The persisted artifact also
        feeds the audit report.
        """
        if not self.project:
            return

        dataset_name = spec.get("dataset")
        if not dataset_name or not self.active_dataset or self.active_dataset.name != dataset_name:
            self._load_dataset_into_grid(dataset_name)
        if not self.active_dataset:
            messagebox.showerror("Error", f"Dataset '{dataset_name}' for this analysis could not be loaded.")
            return

        try:
            artifact = specs.run_spec_payload(spec, self.project)
        except specs.ConfirmatoryGateError as exc:
            messagebox.showwarning("Confirmatory Run Refused", str(exc), parent=self)
            return
        except Exception as e:
            messagebox.showerror("Analysis Error", f"Failed to run analysis:\n{e}", parent=self)
            return

        # Persist the run so multiplicity pooling and the audit report see it.
        self.project.save_run_artifact(artifact)

        result = artifact.get("result", {})
        output_text = self._format_artifact(spec, artifact)
        title = self._analysis_title(spec, result)

        result_key = artifact.get("spec_hash") or specs.compute_spec_hash(spec)
        self.output_viewer.add_result(title, output_text, result_key=result_key)

    def _analysis_title(self, spec: dict[str, Any], result: dict[str, Any]) -> str:
        """Build a short history-tree title for an analysis."""
        analysis_name = spec.get("analysis", "Analysis")
        inputs = spec.get("inputs", {})
        if analysis_name == "describe":
            return f"Descriptives: {inputs.get('data', '')}"
        if analysis_name == "stdlib_simple_regression":
            return f"Simple Regression: {inputs.get('y', '')} on {inputs.get('x', '')}"
        if analysis_name == "ols":
            return f"Multiple Regression: {inputs.get('y', '')}"
        if analysis_name == "correlation_matrix":
            return f"Correlation Matrix ({result.get('method', '')})" if isinstance(result, dict) else "Correlation Matrix"
        if isinstance(result, dict) and result.get("test"):
            return str(result["test"])
        return analysis_name

    def _format_artifact(self, spec: dict[str, Any], artifact: dict[str, Any]) -> str:
        """Render an artifact for the output viewer.

        Regression keeps its rich coefficient table; everything else uses the
        shared ``render_artifact`` text so tests, descriptives, pre-registration,
        and multiplicity all display consistently with the CLI.
        """
        analysis_name = spec.get("analysis")
        result = artifact.get("result", {})

        if analysis_name in ("stdlib_simple_regression", "ols") and isinstance(result, dict) and "error" not in result:
            inputs = spec.get("inputs", {})
            if analysis_name == "stdlib_simple_regression":
                body = self._format_regression_results(
                    "Simple Linear Regression (stdlib)", inputs.get("y", ""), [inputs.get("x", "")], result
                )
            else:
                body = self._format_regression_results(
                    "Multiple Linear Regression (OLS)", inputs.get("y", ""), inputs.get("X", []), result
                )
            trailer = render.render_artifact_trailer(artifact)
            return body + ("\n\n" + trailer if trailer else "")

        return render.render_artifact(artifact)

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
        spec = specs.create_spec("stdlib_simple_regression", self.active_dataset.name, inputs={"y": dep_var, "x": ind_var}, options={})
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

    # --- Hypothesis tests (exploratory) ---

    def _save_and_run(self, spec: dict[str, Any]):
        """Persist the spec to the project explorer and run it."""
        self.project.save_analysis(spec)
        self.project_explorer.populate(self.project)
        self._execute_and_display_spec(spec)

    def _run_ttest_1samp(self):
        if not self.active_dataset:
            return
        dialog = OneSampleTTestDialog(self, self.active_dataset.column_names)
        if not dialog.result:
            return
        spec = specs.create_spec(
            "ttest_1samp", self.active_dataset.name,
            inputs={"data": dialog.result["variable"]},
            options={"null_mean": dialog.result["null_mean"], "alternative": dialog.result["alternative"]},
        )
        self._save_and_run(spec)

    def _run_ttest_ind(self):
        if not self.active_dataset:
            return
        dialog = TwoSampleDialog(self, self.active_dataset.column_names, "Independent t-test", show_variance=True)
        if not dialog.result:
            return
        spec = specs.create_spec(
            "ttest_ind", self.active_dataset.name,
            inputs={"x": dialog.result["x"], "y": dialog.result["y"]},
            options={
                "alternative": dialog.result["alternative"],
                "variance_assumption": dialog.result["variance_assumption"],
            },
        )
        self._save_and_run(spec)

    def _run_mann_whitney(self):
        if not self.active_dataset:
            return
        dialog = TwoSampleDialog(self, self.active_dataset.column_names, "Mann-Whitney U")
        if not dialog.result:
            return
        spec = specs.create_spec(
            "mann_whitney_u", self.active_dataset.name,
            inputs={"x": dialog.result["x"], "y": dialog.result["y"]}, options={},
        )
        self._save_and_run(spec)

    def _run_wilcoxon(self):
        if not self.active_dataset:
            return
        dialog = TwoSampleDialog(self, self.active_dataset.column_names, "Wilcoxon Signed-Rank")
        if not dialog.result:
            return
        spec = specs.create_spec(
            "wilcoxon_signed_rank", self.active_dataset.name,
            inputs={"x": dialog.result["x"], "y": dialog.result["y"]}, options={},
        )
        self._save_and_run(spec)

    def _run_fisher_exact(self):
        if not self.active_dataset:
            return
        dialog = FisherExactDialog(self, self.active_dataset.column_names)
        if not dialog.result:
            return
        spec = specs.create_spec(
            "fisher_exact_2x2", self.active_dataset.name,
            inputs={"table": dialog.result["table"]}, options={},
        )
        self._save_and_run(spec)

    def _run_anova(self):
        if not self.active_dataset:
            return
        dialog = MultiVariableDialog(
            self, self.active_dataset.column_names, "One-Way ANOVA",
            prompt="Select two or more group columns to compare:",
        )
        if not dialog.result:
            return
        spec = specs.create_spec(
            "one_way_anova", self.active_dataset.name,
            inputs={"groups": dialog.result["variables"]}, options={},
        )
        self._save_and_run(spec)

    def _run_correlation_matrix(self):
        if not self.active_dataset:
            return
        dialog = MultiVariableDialog(
            self, self.active_dataset.column_names, "Correlation Matrix",
            prompt="Select two or more variables to correlate:",
            methods=["pearson", "spearman"],
        )
        if not dialog.result:
            return
        spec = specs.create_spec(
            "correlation_matrix", self.active_dataset.name,
            inputs={"columns": dialog.result["variables"]},
            options={"method": dialog.result["method"]},
        )
        self._save_and_run(spec)

    # --- Pre-registration / confirmatory workflow ---

    def _declare_hypothesis(self):
        if not self.active_dataset:
            return
        dialog = DeclareHypothesisDialog(self, self.active_dataset.column_names)
        if not dialog.result:
            return
        r = dialog.result
        plan = plans.build_plan(
            analysis=r["analysis"],
            dataset=self.active_dataset.name,
            inputs=r["inputs"],
            options=r["options"],
            hypothesis=r["hypothesis"],
            prediction=r["prediction"],
            alpha=r["alpha"],
        )
        try:
            plan_id = self.project.commit_plan(plan)
        except ValueError as exc:
            messagebox.showerror("Could Not Register", str(exc), parent=self)
            return
        self.project_explorer.populate(self.project)
        messagebox.showinfo(
            "Hypothesis Pre-registered",
            f"Plan committed (id {plan_id}).\n\nThe result is sealed. Use "
            "'Run Confirmatory Test...' to reveal it.",
            parent=self,
        )

    def _run_confirmatory(self):
        if not self.project:
            return
        dataset_name = self.active_dataset.name if self.active_dataset else None
        committed = self.project.list_plans(dataset_name)
        if not committed:
            messagebox.showinfo(
                "No Plans",
                "No pre-registered plans for this dataset yet.\nUse 'Pre-register Hypothesis...' first.",
                parent=self,
            )
            return
        dialog = SelectPlanDialog(self, committed)
        if not dialog.result:
            return

        plan = dialog.result["plan"]
        spec = specs.create_spec(
            plan["analysis"],
            plan["dataset"],
            inputs=plan["inputs"],
            options=plan["decision_options"],
            mode="confirmatory",
            plan_id=plans.plan_id(plan),
        )
        self._save_and_run(spec)

    def _show_audit(self):
        if not self.active_dataset:
            return
        report = specs.audit_dataset(self.project, self.active_dataset.name)
        self.output_viewer.add_result(
            f"Audit: {self.active_dataset.name}",
            self._format_audit(report),
            result_key=f"audit::{self.active_dataset.name}",
        )

    def _format_audit(self, report: dict[str, Any]) -> str:
        lines = [
            f"Transparency Audit — dataset '{report['dataset']}'",
            "",
            f"  Hypotheses pre-registered     : {report['num_plans_declared']}",
            f"  Analyses executed             : {report['num_runs_executed']}",
            f"  Inferential tests run         : {report['num_inferential_runs']}",
            f"  Confirmatory runs             : {report['num_confirmatory_runs']}",
            f"  Exploratory inferential runs  : {report['num_exploratory_inferential_runs']}",
        ]
        if report["unused_plan_ids"]:
            lines.append(f"  Unused plans                  : {', '.join(report['unused_plan_ids'])}")
        if report["warnings"]:
            lines.append("")
            lines.append("  ⚠ Warnings:")
            for warning in report["warnings"]:
                lines.append(f"    - {warning}")
        else:
            lines.append("")
            lines.append("  No transparency concerns detected.")
        return "\n".join(lines)

    def _run_histogram(self):
        if not self.active_dataset:
            return
        dialog = HistogramDialog(self, self.active_dataset.column_names)
        selection = dialog.result
        if not selection:
            return

        from tkstatistics.viz import build_histogram
        from tkstatistics.viz.histogram import HistogramSpec

        var_name = selection["variable"]
        column = self.active_dataset.get_column(var_name)
        spec = HistogramSpec(
            values=column,
            bins=selection["bins"],
            title=f"Histogram of {var_name}",
            x_label=var_name,
        )
        scene = build_histogram(spec)
        ChartWindow(self, scene, title=f"Histogram: {var_name}")

    def _run_boxplot(self):
        if not self.active_dataset:
            return
        dialog = SingleVariableDialog(self, self.active_dataset.column_names, title="Box Plot")
        if not dialog.result:
            return

        from tkstatistics.viz import BoxplotSpec, build_boxplot

        var_name = dialog.result["variable"]
        column = self.active_dataset.get_column(var_name)
        try:
            scene = build_boxplot(BoxplotSpec(values=column, title=f"Box Plot of {var_name}", y_label=var_name))
        except ValueError as exc:
            messagebox.showwarning("Cannot Plot", str(exc), parent=self)
            return
        ChartWindow(self, scene, title=f"Box Plot: {var_name}")

    def _run_scatter(self):
        if not self.active_dataset:
            return
        dialog = ScatterDialog(self, self.active_dataset.column_names)
        if not dialog.result:
            return

        from tkstatistics.viz import ScatterSpec, build_scatter

        x_name, y_name = dialog.result["x"], dialog.result["y"]
        spec = ScatterSpec(
            x=self.active_dataset.get_column(x_name),
            y=self.active_dataset.get_column(y_name),
            title=f"{y_name} vs {x_name}",
            x_label=x_name,
            y_label=y_name,
            fit_line=dialog.result["fit_line"],
        )
        ChartWindow(self, build_scatter(spec), title=f"Scatter: {y_name} vs {x_name}")

    def _run_qqplot(self):
        if not self.active_dataset:
            return
        dialog = SingleVariableDialog(self, self.active_dataset.column_names, title="Normal Q-Q Plot")
        if not dialog.result:
            return

        from tkstatistics.viz import QQSpec, build_qqplot

        var_name = dialog.result["variable"]
        column = self.active_dataset.get_column(var_name)
        scene = build_qqplot(QQSpec(values=column, title=f"Normal Q-Q Plot of {var_name}"))
        ChartWindow(self, scene, title=f"Q-Q Plot: {var_name}")

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
        analyze_menu.add_command(label="Correlation Matrix...", command=self._run_correlation_matrix)
        analyze_menu.add_separator()
        tests_menu = tk.Menu(analyze_menu, tearoff=0)
        analyze_menu.add_cascade(label="Hypothesis Tests", menu=tests_menu)
        tests_menu.add_command(label="One-Sample t-test...", command=self._run_ttest_1samp)
        tests_menu.add_command(label="Independent t-test...", command=self._run_ttest_ind)
        tests_menu.add_command(label="One-Way ANOVA...", command=self._run_anova)
        tests_menu.add_command(label="Mann-Whitney U...", command=self._run_mann_whitney)
        tests_menu.add_command(label="Wilcoxon Signed-Rank...", command=self._run_wilcoxon)
        tests_menu.add_command(label="Fisher's Exact (2x2)...", command=self._run_fisher_exact)
        analyze_menu.add_separator()
        analyze_menu.add_command(label="Pre-register Hypothesis...", command=self._declare_hypothesis)
        analyze_menu.add_command(label="Run Confirmatory Test...", command=self._run_confirmatory)
        analyze_menu.add_command(label="Audit Report...", command=self._show_audit)
        self.analyze_menu = analyze_menu
        graphs_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Graphs", menu=graphs_menu)
        graphs_menu.add_command(label="Histogram...", command=self._run_histogram)
        graphs_menu.add_command(label="Box Plot...", command=self._run_boxplot)
        graphs_menu.add_command(label="Scatter Plot...", command=self._run_scatter)
        graphs_menu.add_command(label="Normal Q-Q Plot...", command=self._run_qqplot)
        self.graphs_menu = graphs_menu

    def _new_project(self):
        path = filedialog.asksaveasfilename(title="Create New Project", defaultextension=".statproj", filetypes=[("tkstatistics Project", "*.statproj")])
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
            return "\n".join(
                lines
                + [
                    f"  N: {results['n']}",
                    f"  Missing: {results['missing']}",
                    "\n(No valid data to compute statistics)",
                ]
            )
        lines.extend(
            [
                f"  N: {results['n']} (Missing: {results['missing']})",
                f"  Mean: {results['mean']:.4f}",
                f"  Median: {results['median']:.4f}",
                f"  Std. Deviation: {results['stdev']:.4f}",
                f"  Variance: {results['variance']:.4f}",
                f"  Min: {results['min']:.4f}",
                f"  Max: {results['max']:.4f}",
                f"  IQR: {results['iqr']:.4f}",
            ]
        )
        return "\n".join(lines)

    def _format_regression_results(self, title: str, dep_var: str, pred_vars: list[str], results: dict[str, Any]) -> str:
        if "error" in results:
            return f"{title}\n\nError: {results['error']}\nDetails: {results.get('details', 'N/A')}"

        def cell(value: Any, spec: str = ">12.4f") -> str:
            if value is None:
                return f"{'—':>12}"
            return f"{value:{spec}}"

        lines = [
            f"{title}",
            f"Dependent Variable: {dep_var}\n",
            f"R-squared: {results['r_squared']:.4f}",
            f"Adjusted R-squared: {results['adj_r_squared']:.4f}",
            f"Observations: {results['n']}\n",
            f"{'Variable':<15} {'Coefficient':>12} {'Std. Error':>12} {'t-stat':>12} {'p-value':>12}",
            "-" * 66,
        ]
        p_values = results.get("p_values") or [None] * len(results["coefficients"])
        labels = ["(Intercept)", *pred_vars]
        for i, var_name in enumerate(labels):
            lines.append(
                f"{var_name:<15} {cell(results['coefficients'][i])} {cell(results['std_errors'][i])} "
                f"{cell(results['t_statistics'][i], '>12.3f')} {cell(p_values[i])}"
            )
        lines.append(f"\n{results['notes']}")
        return "\n".join(lines)


def launch_app():
    app = App()
    app.mainloop()
