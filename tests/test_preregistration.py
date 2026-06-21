from __future__ import annotations

import pytest

from tkstatistics.core import plans, specs
from tkstatistics.core.dataset import TabularData
from tkstatistics.core.project import Project
from tkstatistics.core.specs import ConfirmatoryGateError


def _make_project(tmp_path):
    project_path = tmp_path / "sample.statproj"
    project = Project(project_path)
    dataset = TabularData.from_list_of_dicts(
        "demo",
        [
            {"x": 1.0, "y": 2.5, "grp": "a"},
            {"x": 2.0, "y": 4.1, "grp": "b"},
            {"x": 3.0, "y": 5.9, "grp": "a"},
            {"x": 4.0, "y": 8.2, "grp": "b"},
            {"x": 5.0, "y": 9.8, "grp": "a"},
        ],
    )
    project.save_dataset(dataset)
    return project, project_path


# ---------------------------------------------------------------------------
# Plan hashing
# ---------------------------------------------------------------------------


def test_plan_hash_is_stable_and_excludes_cosmetic_options():
    p1 = plans.build_plan(
        analysis="ttest_1samp",
        dataset="demo",
        inputs={"data": "y"},
        options={"null_mean": 5.0, "alternative": "greater", "conf_level": 0.95},
        hypothesis="Mean of y exceeds 5.",
        alpha=0.05,
    )
    # conf_level is cosmetic (not a decision option) → should not change the id.
    p2 = plans.build_plan(
        analysis="ttest_1samp",
        dataset="demo",
        inputs={"data": "y"},
        options={"null_mean": 5.0, "alternative": "greater", "conf_level": 0.99},
        hypothesis="Mean of y exceeds 5.",
        alpha=0.05,
    )
    assert plans.plan_id(p1) == plans.plan_id(p2)


def test_changing_decision_option_changes_plan_id():
    base = dict(analysis="ttest_1samp", dataset="demo", inputs={"data": "y"}, hypothesis="h")
    p1 = plans.build_plan(options={"null_mean": 5.0, "alternative": "greater"}, **base)
    p2 = plans.build_plan(options={"null_mean": 5.0, "alternative": "less"}, **base)
    assert plans.plan_id(p1) != plans.plan_id(p2)


def test_build_plan_rejects_empty_hypothesis():
    with pytest.raises(ValueError):
        plans.build_plan(analysis="ttest_1samp", dataset="demo", inputs={"data": "y"}, options={}, hypothesis="  ")


# ---------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------


def test_confirmatory_run_without_plan_is_refused(tmp_path):
    project, _ = _make_project(tmp_path)
    try:
        spec = specs.create_spec(
            "ttest_1samp", "demo", inputs={"data": "y"},
            options={"null_mean": 5.0}, mode="confirmatory", seed=1,
        )
        with pytest.raises(ConfirmatoryGateError):
            specs.run_spec_payload(spec, project)
    finally:
        project.close()


def test_confirmatory_run_with_unknown_plan_is_refused(tmp_path):
    project, _ = _make_project(tmp_path)
    try:
        spec = specs.create_spec(
            "ttest_1samp", "demo", inputs={"data": "y"},
            options={"null_mean": 5.0}, mode="confirmatory", plan_id="deadbeefdeadbeef", seed=1,
        )
        with pytest.raises(ConfirmatoryGateError):
            specs.run_spec_payload(spec, project)
    finally:
        project.close()


def test_confirmatory_run_with_committed_plan_reveals_pvalue(tmp_path):
    project, _ = _make_project(tmp_path)
    try:
        plan = plans.build_plan(
            analysis="ttest_1samp", dataset="demo", inputs={"data": "y"},
            options={"null_mean": 5.0, "alternative": "two-sided"},
            hypothesis="Mean of y differs from 5.",
        )
        pid = project.commit_plan(plan)

        spec = specs.create_spec(
            "ttest_1samp", "demo", inputs={"data": "y"},
            options={"null_mean": 5.0, "alternative": "two-sided"},
            mode="confirmatory", plan_id=pid, seed=1,
        )
        artifact = specs.run_spec_payload(spec, project)
    finally:
        project.close()

    assert artifact["status"] == "ok"
    assert "p_value" in artifact["result"]
    assert artifact["preregistration"]["faithful"] is True
    assert artifact["preregistration"]["deviations"] == []


def test_confirmatory_deviation_is_recorded_not_blocked(tmp_path):
    project, _ = _make_project(tmp_path)
    try:
        plan = plans.build_plan(
            analysis="ttest_1samp", dataset="demo", inputs={"data": "y"},
            options={"null_mean": 5.0, "alternative": "two-sided"},
            hypothesis="Mean of y differs from 5.",
        )
        pid = project.commit_plan(plan)

        # Same plan_id, but the executed spec changes the null mean — a deviation.
        spec = specs.create_spec(
            "ttest_1samp", "demo", inputs={"data": "y"},
            options={"null_mean": 6.0, "alternative": "two-sided"},
            mode="confirmatory", plan_id=pid, seed=1,
        )
        artifact = specs.run_spec_payload(spec, project)
    finally:
        project.close()

    assert artifact["status"] == "ok"
    assert artifact["preregistration"]["faithful"] is False
    assert artifact["preregistration"]["deviations"]
    assert any("DEVIATES" in w for w in artifact["warnings"])


def test_confirmatory_mode_rejects_non_inferential_analysis(tmp_path):
    project, _ = _make_project(tmp_path)
    try:
        spec = specs.create_spec(
            "describe", "demo", inputs={"data": "y"}, options={},
            mode="confirmatory", seed=1,
        )
        with pytest.raises(ConfirmatoryGateError):
            specs.run_spec_payload(spec, project)
    finally:
        project.close()


def test_exploratory_run_needs_no_plan(tmp_path):
    project, _ = _make_project(tmp_path)
    try:
        spec = specs.create_spec(
            "ttest_1samp", "demo", inputs={"data": "y"},
            options={"null_mean": 5.0}, mode="exploratory", seed=1,
        )
        artifact = specs.run_spec_payload(spec, project)
    finally:
        project.close()

    assert artifact["status"] == "ok"
    assert "preregistration" not in artifact


def test_commit_plan_is_idempotent_but_rejects_collision(tmp_path):
    project, _ = _make_project(tmp_path)
    try:
        plan = plans.build_plan(
            analysis="ttest_1samp", dataset="demo", inputs={"data": "y"},
            options={"null_mean": 5.0}, hypothesis="h",
        )
        pid1 = project.commit_plan(plan)
        pid2 = project.commit_plan(plan)  # idempotent
        assert pid1 == pid2
    finally:
        project.close()


# ---------------------------------------------------------------------------
# run_spec refusal artifact + audit report
# ---------------------------------------------------------------------------


def test_run_spec_returns_refusal_artifact(tmp_path):
    import json

    project, project_path = _make_project(tmp_path)
    project.close()

    spec_path = tmp_path / "spec.json"
    spec = specs.create_spec(
        "ttest_1samp", "demo", inputs={"data": "y"},
        options={"null_mean": 5.0}, mode="confirmatory", seed=1,
    )
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    artifact = specs.run_spec(spec_path, project_path)
    assert artifact["status"] == "refused"
    assert artifact["reason"] == "confirmatory_gate"

    # The refused run must NOT have been persisted as a completed run.
    project = Project(project_path)
    try:
        count = project.conn.execute("SELECT COUNT(*) FROM analysis_runs").fetchone()[0]
    finally:
        project.close()
    assert count == 0


def test_audit_flags_undisclosed_exploratory_testing(tmp_path):
    project, _ = _make_project(tmp_path)
    try:
        # Run two exploratory inferential tests, no pre-registration.
        for col, seed in [("y", 1), ("x", 2)]:
            spec = specs.create_spec(
                "ttest_1samp", "demo", inputs={"data": col},
                options={"null_mean": 0.0}, mode="exploratory", seed=seed,
            )
            artifact = specs.run_spec_payload(spec, project)
            project.save_run_artifact(artifact)

        report = specs.audit_dataset(project, "demo")
    finally:
        project.close()

    assert report["num_plans_declared"] == 0
    assert report["num_inferential_runs"] == 2
    assert report["num_exploratory_inferential_runs"] == 2
    assert report["warnings"]
