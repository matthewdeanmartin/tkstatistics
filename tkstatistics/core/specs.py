# tkstatistics/core/specs.py

"""
Manages the creation and execution of JSON analysis specifications.
"""
from __future__ import annotations

import json
import random
from collections.abc import Callable
from pathlib import Path
from typing import Any

# Import all stats functions to register them
from tkstatistics.stats import descriptives, nonparametric, regression

from .project import Project

# This dispatcher map is crucial for the headless runner.
# It connects the string name in the JSON spec to the actual Python function.
ANALYSIS_DISPATCHER: dict[str, Callable[..., dict[str, Any]]] = {
    # Descriptives
    "describe": descriptives.describe,
    "frequency_table": descriptives.frequency_table,
    # Nonparametric
    "mann_whitney_u": nonparametric.mann_whitney_u,
    "wilcoxon_signed_rank": nonparametric.wilcoxon_signed_rank,
    "fisher_exact_2x2": nonparametric.fisher_exact_2x2,
    # "ttest_ind": parametric.ttest_ind, # To be added
    # Regression
    "ols": regression.ols,
    "stdlib_simple_regression": regression.stdlib_simple_regression,  # <-- New entry
}


def create_spec(
    analysis_name: str, dataset_name: str, inputs: dict[str, Any], options: dict[str, Any], app_version: str = "0.1.0"
) -> dict[str, Any]:
    """
    Creates a JSON-serializable dictionary representing an analysis specification.

    Args:
        analysis_name: The name of the analysis function (e.g., 'describe').
        dataset_name: The name of the dataset used.
        inputs: A dictionary mapping input roles to variable names (e.g., {'x': 'height'}).
        options: A dictionary of options passed to the analysis function.
        app_version: The version of tkstatistics that created the spec.

    Returns:
        A dictionary representing the analysis spec.
    """
    if analysis_name not in ANALYSIS_DISPATCHER:
        raise ValueError(f"Unknown analysis name: '{analysis_name}'")

    return {
        "analysis": analysis_name,
        "dataset": dataset_name,
        "inputs": inputs,
        "options": options,
        "seed": random.randint(0, 2**32 - 1),
        "version": f"tkstatistics {app_version}",
    }


def run_spec(spec_path: Path, project_path: Path) -> dict[str, Any]:
    """
    Runs an analysis headlessly from a JSON specification file.

    Args:
        spec_path: Path to the .json spec file.
        project_path: Path to the .statproj project file.

    Returns:
        A dictionary containing the analysis results.
    """
    # 1. Load and validate the spec
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ValueError(f"Failed to load or parse spec file: {e}") from e

    analysis_name = spec.get("analysis")
    if not analysis_name or analysis_name not in ANALYSIS_DISPATCHER:
        raise ValueError(f"Spec contains an invalid analysis name: '{analysis_name}'")

    # 2. Load the project and required data
    project = Project(project_path)
    try:
        dataset = project.load_dataset(spec["dataset"])
    finally:
        project.close()  # Ensure connection is closed

    # 3. Prepare arguments for the statistical function
    analysis_func = ANALYSIS_DISPATCHER[analysis_name]

    # Map input variable names from the spec to actual data columns or values
    kwargs = {}
    for role, var_name_or_value in spec.get("inputs", {}).items():
        # Heuristic: if the value is a string and a column name, fetch it.
        # Otherwise, pass it as a literal. This supports inputs like `table` in fisher_exact.
        if isinstance(var_name_or_value, str) and var_name_or_value in dataset.column_names:
            kwargs[role] = dataset.get_column(var_name_or_value)
        else:
            kwargs[role] = var_name_or_value

    # Add options from the spec
    kwargs.update(spec.get("options", {}))

    # 4. Execute the analysis
    results = analysis_func(**kwargs)
    return results
