# tkstatistics/core/specs.py

"""
Manages the creation and execution of JSON analysis specifications.
"""

from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timezone
from collections.abc import Callable
from pathlib import Path
from typing import Any

from tkstatistics.__about__ import __version__

# Import all stats functions to register them
from tkstatistics.stats import descriptives, nonparametric, parametric, regression
from tkstatistics.stats.multiplicity import holm_bonferroni_correction

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
    # Parametric
    "ttest_1samp": parametric.ttest_1samp,
    "ttest_ind": parametric.ttest_ind,
    # Regression
    "ols": regression.ols,
    "stdlib_simple_regression": regression.stdlib_simple_regression,  # <-- New entry
}

SUPPORTED_SPEC_VERSION = 1

_ANALYSIS_INPUT_RULES: dict[str, dict[str, str]] = {
    "describe": {"data": "column"},
    "frequency_table": {"data": "column_or_literal"},
    "mann_whitney_u": {"x": "column_or_list", "y": "column_or_list"},
    "wilcoxon_signed_rank": {"x": "column_or_list", "y": "column_or_list"},
    "fisher_exact_2x2": {"table": "literal"},
    "ttest_1samp": {"data": "column"},
    "ttest_ind": {"x": "column_or_list", "y": "column_or_list"},
    "stdlib_simple_regression": {"x": "column", "y": "column"},
    "ols": {"X": "column_list_or_matrix", "y": "column"},
}

_ANALYSIS_OPTION_RULES: dict[str, set[str]] = {
    "describe": set(),
    "frequency_table": set(),
    "mann_whitney_u": set(),
    "wilcoxon_signed_rank": set(),
    "fisher_exact_2x2": set(),
    "ttest_1samp": {"null_mean", "alternative", "conf_level"},
    "ttest_ind": {"null_diff", "alternative", "variance_assumption", "conf_level"},
    "stdlib_simple_regression": set(),
    "ols": {"add_intercept"},
}


def create_spec(
    analysis_name: str,
    dataset_name: str,
    inputs: dict[str, Any],
    options: dict[str, Any],
    app_version: str = __version__,
    mode: str = "exploratory",
    plan_id: str | None = None,
    seed: int | None = None,
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

    if mode not in {"exploratory", "confirmatory"}:
        raise ValueError("mode must be either 'exploratory' or 'confirmatory'")

    return {
        "spec_version": SUPPORTED_SPEC_VERSION,
        "analysis": analysis_name,
        "dataset": dataset_name,
        "inputs": inputs,
        "options": options,
        "seed": seed if seed is not None else random.randint(0, 2**32 - 1),
        "mode": mode,
        "plan_id": plan_id,
        "app_version": app_version,
    }


def canonicalize_spec(spec: dict[str, Any]) -> str:
    """Returns a stable JSON representation of a spec."""
    return json.dumps(spec, sort_keys=True, separators=(",", ":"))


def compute_spec_hash(spec: dict[str, Any]) -> str:
    """Computes a deterministic hash for a validated spec."""
    canonical = canonicalize_spec(spec)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _dataset_fingerprint(dataset: Any) -> str:
    """Computes a stable hash over dataset rows for reproducibility records."""
    payload = {
        "name": dataset.name,
        "columns": dataset.column_names,
        "rows": dataset.to_list_of_dicts(),
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _validate_input_value(input_rule: str, value: Any, dataset_columns: set[str], role: str):
    if input_rule == "column":
        if not isinstance(value, str) or value not in dataset_columns:
            raise ValueError(f"Input '{role}' must name an existing dataset column.")
        return

    if input_rule == "column_or_literal":
        if isinstance(value, str) and value in dataset_columns:
            return
        return

    if input_rule == "column_or_list":
        if isinstance(value, str):
            if value not in dataset_columns:
                raise ValueError(f"Input '{role}' references unknown column '{value}'.")
            return
        if not isinstance(value, list):
            raise ValueError(f"Input '{role}' must be a dataset column or a literal list.")
        return

    if input_rule == "column_list_or_matrix":
        if not isinstance(value, list) or not value:
            raise ValueError(f"Input '{role}' must be a non-empty list.")
        if all(isinstance(v, str) for v in value):
            unknown = [v for v in value if v not in dataset_columns]
            if unknown:
                raise ValueError(f"Input '{role}' references unknown columns: {', '.join(unknown)}")
            return
        if not all(isinstance(row, list) for row in value):
            raise ValueError(f"Input '{role}' must be a list of column names or a matrix.")
        return

    if input_rule == "literal":
        return

    raise ValueError(f"Unknown validation rule for input '{role}'.")


def validate_spec(spec: dict[str, Any], project: Project) -> dict[str, Any]:
    """
    Validates and normalizes an analysis spec.

    Returns a normalized copy with defaults and compatibility migration applied.
    """
    if not isinstance(spec, dict):
        raise ValueError("Spec payload must be a JSON object.")

    normalized = dict(spec)

    if "spec_version" not in normalized:
        normalized["spec_version"] = SUPPORTED_SPEC_VERSION
    if "app_version" not in normalized:
        legacy_version = normalized.pop("version", None)
        normalized["app_version"] = str(legacy_version) if legacy_version is not None else __version__
    if "mode" not in normalized:
        normalized["mode"] = "exploratory"
    if "plan_id" not in normalized:
        normalized["plan_id"] = None
    if "seed" not in normalized:
        normalized["seed"] = random.randint(0, 2**32 - 1)

    required_fields = {"analysis", "dataset", "inputs", "options", "seed", "mode", "spec_version", "app_version"}
    missing = [field for field in required_fields if field not in normalized]
    if missing:
        raise ValueError(f"Spec missing required fields: {', '.join(sorted(missing))}")

    if normalized["spec_version"] != SUPPORTED_SPEC_VERSION:
        raise ValueError(f"Unsupported spec_version '{normalized['spec_version']}'. Only version {SUPPORTED_SPEC_VERSION} is currently supported.")

    analysis_name = normalized.get("analysis")
    if not isinstance(analysis_name, str) or analysis_name not in ANALYSIS_DISPATCHER:
        raise ValueError(f"Spec contains an invalid analysis name: '{analysis_name}'")

    dataset_name = normalized.get("dataset")
    if not isinstance(dataset_name, str) or not dataset_name:
        raise ValueError("Spec 'dataset' must be a non-empty string.")
    if project.get_dataset_id(dataset_name) is None:
        raise ValueError(f"Dataset '{dataset_name}' not found in project.")

    mode = normalized.get("mode")
    if mode not in {"exploratory", "confirmatory"}:
        raise ValueError("Spec 'mode' must be either 'exploratory' or 'confirmatory'.")

    if not isinstance(normalized.get("seed"), int):
        raise ValueError("Spec 'seed' must be an integer.")

    inputs = normalized.get("inputs")
    options = normalized.get("options")
    if not isinstance(inputs, dict):
        raise ValueError("Spec 'inputs' must be a JSON object.")
    if not isinstance(options, dict):
        raise ValueError("Spec 'options' must be a JSON object.")

    input_rules = _ANALYSIS_INPUT_RULES[analysis_name]
    missing_input_roles = [role for role in input_rules if role not in inputs]
    if missing_input_roles:
        raise ValueError(f"Missing required input roles for {analysis_name}: {', '.join(missing_input_roles)}")
    unknown_roles = [role for role in inputs if role not in input_rules]
    if unknown_roles:
        raise ValueError(f"Unknown input roles for {analysis_name}: {', '.join(unknown_roles)}")

    dataset = project.load_dataset(dataset_name)
    dataset_columns = set(dataset.column_names)
    for role, rule in input_rules.items():
        _validate_input_value(rule, inputs[role], dataset_columns, role)

    allowed_options = _ANALYSIS_OPTION_RULES.get(analysis_name, set())
    unknown_options = [option for option in options if option not in allowed_options]
    if unknown_options:
        raise ValueError(f"Unknown options for {analysis_name}: {', '.join(sorted(unknown_options))}")

    if analysis_name == "ols" and "add_intercept" in options and not isinstance(options["add_intercept"], bool):
        raise ValueError("Option 'add_intercept' must be a boolean.")

    if analysis_name == "ttest_1samp":
        if "null_mean" in options and not isinstance(options["null_mean"], (int, float)):
            raise ValueError("Option 'null_mean' must be numeric.")
        if "alternative" in options and options["alternative"] not in {"two-sided", "less", "greater"}:
            raise ValueError("Option 'alternative' must be one of: two-sided, less, greater.")
        if "conf_level" in options:
            conf_level = options["conf_level"]
            if not isinstance(conf_level, (int, float)) or not (0 < float(conf_level) < 1):
                raise ValueError("Option 'conf_level' must be numeric and between 0 and 1.")

    if analysis_name == "ttest_ind":
        if "null_diff" in options and not isinstance(options["null_diff"], (int, float)):
            raise ValueError("Option 'null_diff' must be numeric.")
        if "alternative" in options and options["alternative"] not in {"two-sided", "less", "greater"}:
            raise ValueError("Option 'alternative' must be one of: two-sided, less, greater.")
        if "variance_assumption" in options and options["variance_assumption"] not in {"welch", "pooled"}:
            raise ValueError("Option 'variance_assumption' must be one of: welch, pooled.")
        if "conf_level" in options:
            conf_level = options["conf_level"]
            if not isinstance(conf_level, (int, float)) or not (0 < float(conf_level) < 1):
                raise ValueError("Option 'conf_level' must be numeric and between 0 and 1.")

    return normalized


def _prepare_analysis_kwargs(spec: dict[str, Any], dataset: Any) -> dict[str, Any]:
    """Maps spec inputs/options into callable kwargs."""
    kwargs: dict[str, Any] = {}
    for role, var_name_or_value in spec.get("inputs", {}).items():
        if isinstance(var_name_or_value, str) and var_name_or_value in dataset.column_names:
            kwargs[role] = dataset.get_column(var_name_or_value)
        elif isinstance(var_name_or_value, list) and var_name_or_value and all(isinstance(v, str) and v in dataset.column_names for v in var_name_or_value):
            kwargs[role] = [dataset.get_column(v) for v in var_name_or_value]
        else:
            kwargs[role] = var_name_or_value

    kwargs.update(spec.get("options", {}))

    if spec["analysis"] == "ols" and "X" in kwargs and kwargs["X"] and isinstance(kwargs["X"][0], list):
        kwargs["X"] = list(zip(*kwargs["X"], strict=False))

    return kwargs


def run_spec_payload(spec: dict[str, Any], project: Project) -> dict[str, Any]:
    """Executes a validated spec and returns a reproducible run artifact."""
    normalized_spec = validate_spec(spec, project)
    analysis_name = normalized_spec["analysis"]
    analysis_func = ANALYSIS_DISPATCHER[analysis_name]
    dataset = project.load_dataset(normalized_spec["dataset"])
    kwargs = _prepare_analysis_kwargs(normalized_spec, dataset)

    random_state = random.getstate()
    try:
        random.seed(normalized_spec["seed"])
        results = analysis_func(**kwargs)
    finally:
        random.setstate(random_state)

    artifact = {
        "spec": normalized_spec,
        "spec_hash": compute_spec_hash(normalized_spec),
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "app_version": __version__,
        "dataset_fingerprint": _dataset_fingerprint(dataset),
        "result": results,
        "warnings": [],
        "status": "ok",
    }

    # Multiplicity correction — only when the analysis produced a p_value
    if isinstance(results, dict) and "p_value" in results:
        current_p = results["p_value"]
        dataset_name = normalized_spec["dataset"]
        current_hash = artifact["spec_hash"]

        # Get prior completed runs; exclude current spec (handles re-runs via UPSERT)
        prior_pairs = project.get_p_values_for_dataset(dataset_name)
        pool_pairs = [(h, p) for h, p in prior_pairs if h != current_hash]
        pool_pairs.append((current_hash, current_p))

        pool_p_values = [p for _, p in pool_pairs]
        current_idx = len(pool_pairs) - 1  # always last (appended above)

        adjusted = holm_bonferroni_correction(pool_p_values)

        artifact["multiplicity"] = {
            "method": "holm-bonferroni",
            "num_tests_on_dataset": len(pool_pairs),
            "adjusted_p_value": adjusted[current_idx],
            "note": "Based on all completed analyses on this dataset.",
        }

    return artifact


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

    # 2. Load the project and required data
    project = Project(project_path)
    try:
        artifact = run_spec_payload(spec, project)
        project.save_run_artifact(artifact)
        return artifact
    finally:
        project.close()  # Ensure connection is closed
