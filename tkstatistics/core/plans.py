# tkstatistics/core/plans.py

"""
Pre-registration of analysis plans — the anti-p-hacking core of tkstatistics.

A *plan* declares a hypothesis and the exact confirmatory test that will be run
*before* the result is revealed. Once committed, a plan is immutable and is
identified by a deterministic hash. A confirmatory run is only permitted (and a
p-value only revealed) when it references a committed plan whose declared
analysis, inputs, and decision options match the spec being executed.

This module is intentionally storage-agnostic: it builds and hashes plan
dictionaries. Persistence lives in :mod:`tkstatistics.core.project`.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

PLAN_VERSION = 1

# Option keys that change the *decision rule* of a test. These are part of the
# plan's identity: changing alpha or sidedness after seeing data is p-hacking,
# so they are locked by the plan hash. Cosmetic options (e.g. conf_level for a
# reported interval) are not part of the locked decision contract.
DECISION_OPTION_KEYS: dict[str, set[str]] = {
    "ttest_1samp": {"null_mean", "alternative"},
    "ttest_ind": {"null_diff", "alternative", "variance_assumption"},
    "mann_whitney_u": set(),
    "wilcoxon_signed_rank": set(),
    "fisher_exact_2x2": set(),
}


def _canonical_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    """Sort lists/keys so equivalent declarations hash identically."""
    canonical: dict[str, Any] = {}
    for key in sorted(inputs):
        value = inputs[key]
        canonical[key] = value
    return canonical


def decision_options(analysis: str, options: dict[str, Any]) -> dict[str, Any]:
    """Extract only the decision-relevant options for ``analysis``."""
    keys = DECISION_OPTION_KEYS.get(analysis, set())
    return {k: options[k] for k in sorted(keys) if k in options}


def build_plan(
    *,
    analysis: str,
    dataset: str,
    inputs: dict[str, Any],
    options: dict[str, Any],
    hypothesis: str,
    prediction: str = "",
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Construct an (uncommitted) analysis plan dictionary.

    Args:
        analysis: Name of the confirmatory analysis (must produce a p-value).
        dataset: Dataset the hypothesis is about.
        inputs: Input-role mapping, exactly as it will appear in the spec.
        options: Analysis options; only decision-relevant keys are locked.
        hypothesis: Free-text statement of the hypothesis being tested.
        prediction: Optional directional prediction.
        alpha: Pre-declared significance threshold.
    """
    if not isinstance(hypothesis, str) or not hypothesis.strip():
        raise ValueError("A plan must include a non-empty hypothesis statement.")
    if not (0.0 < float(alpha) < 1.0):
        raise ValueError("alpha must be between 0 and 1.")

    return {
        "plan_version": PLAN_VERSION,
        "analysis": analysis,
        "dataset": dataset,
        "inputs": _canonical_inputs(inputs),
        "decision_options": decision_options(analysis, options),
        "hypothesis": hypothesis.strip(),
        "prediction": prediction.strip(),
        "alpha": float(alpha),
    }


def canonicalize_plan(plan: dict[str, Any]) -> str:
    """Stable JSON representation of the locked portion of a plan.

    Only fields that define the plan's identity are hashed — timestamps and the
    committed flag are deliberately excluded so committing doesn't change the id.
    """
    locked = {
        "plan_version": plan.get("plan_version", PLAN_VERSION),
        "analysis": plan["analysis"],
        "dataset": plan["dataset"],
        "inputs": _canonical_inputs(plan.get("inputs", {})),
        "decision_options": plan.get("decision_options", {}),
        "hypothesis": plan.get("hypothesis", ""),
        "prediction": plan.get("prediction", ""),
        "alpha": plan.get("alpha", 0.05),
    }
    return json.dumps(locked, sort_keys=True, separators=(",", ":"))


def compute_plan_hash(plan: dict[str, Any]) -> str:
    """Deterministic SHA-256 hash identifying a plan."""
    return hashlib.sha256(canonicalize_plan(plan).encode("utf-8")).hexdigest()


def plan_id(plan: dict[str, Any]) -> str:
    """Short, stable identifier (hash prefix) used to reference a plan."""
    return compute_plan_hash(plan)[:16]


def spec_matches_plan(spec: dict[str, Any], plan: dict[str, Any]) -> list[str]:
    """Return a list of human-readable deviations between a spec and its plan.

    An empty list means the confirmatory spec faithfully executes the plan.
    """
    deviations: list[str] = []

    if spec.get("analysis") != plan.get("analysis"):
        deviations.append(f"analysis declared '{plan.get('analysis')}' but spec runs '{spec.get('analysis')}'")
    if spec.get("dataset") != plan.get("dataset"):
        deviations.append(f"dataset declared '{plan.get('dataset')}' but spec uses '{spec.get('dataset')}'")

    declared_inputs = _canonical_inputs(plan.get("inputs", {}))
    spec_inputs = _canonical_inputs(spec.get("inputs", {}))
    if declared_inputs != spec_inputs:
        deviations.append(f"inputs declared {declared_inputs} but spec uses {spec_inputs}")

    analysis = spec.get("analysis", plan.get("analysis"))
    declared_opts = plan.get("decision_options", {})
    spec_opts = decision_options(analysis, spec.get("options", {}))
    if declared_opts != spec_opts:
        deviations.append(f"decision options declared {declared_opts} but spec uses {spec_opts}")

    return deviations


def committed_now() -> str:
    """UTC ISO timestamp for marking a plan committed."""
    return datetime.now(UTC).isoformat()
