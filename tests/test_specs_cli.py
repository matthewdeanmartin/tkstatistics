from __future__ import annotations

import json

from tkstatistics import cli
from tkstatistics.core import specs
from tkstatistics.core.dataset import TabularData
from tkstatistics.core.project import Project


def _make_project(tmp_path):
    project_path = tmp_path / "sample.statproj"
    project = Project(project_path)
    dataset = TabularData.from_list_of_dicts(
        "demo",
        [
            {"x": 1.0, "y": 2.0, "grp": "a"},
            {"x": 2.0, "y": 4.0, "grp": "b"},
            {"x": 3.0, "y": 6.0, "grp": "a"},
            {"x": 4.0, "y": 8.0, "grp": "b"},
        ],
    )
    project.save_dataset(dataset)
    project.close()
    return project_path


def test_validate_spec_normalizes_legacy_fields(tmp_path):
    project_path = _make_project(tmp_path)
    project = Project(project_path)
    try:
        legacy_spec = {
            "analysis": "describe",
            "dataset": "demo",
            "inputs": {"data": "x"},
            "options": {},
            "version": "tkstatistics 0.1.0",
        }
        normalized = specs.validate_spec(legacy_spec, project)
    finally:
        project.close()

    assert normalized["spec_version"] == specs.SUPPORTED_SPEC_VERSION
    assert normalized["mode"] == "exploratory"
    assert normalized["plan_id"] is None
    assert isinstance(normalized["seed"], int)
    assert normalized["app_version"] == "tkstatistics 0.1.0"


def test_run_spec_payload_is_deterministic_for_same_seed(tmp_path):
    project_path = _make_project(tmp_path)
    project = Project(project_path)
    try:
        spec = specs.create_spec(
            "stdlib_simple_regression",
            "demo",
            inputs={"x": "x", "y": "y"},
            options={},
            seed=42,
        )
        run_one = specs.run_spec_payload(spec, project)
        run_two = specs.run_spec_payload(spec, project)
    finally:
        project.close()

    assert run_one["spec_hash"] == run_two["spec_hash"]
    assert run_one["dataset_fingerprint"] == run_two["dataset_fingerprint"]
    assert run_one["result"] == run_two["result"]


def test_cli_run_emits_json_and_writes_output_file(tmp_path, capsys):
    project_path = _make_project(tmp_path)
    spec_path = tmp_path / "run_spec.json"
    output_path = tmp_path / "artifact.json"

    spec = specs.create_spec("describe", "demo", inputs={"data": "x"}, options={}, seed=123)
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    rc = cli.main(["--run", str(spec_path), "--project", str(project_path), "--output", str(output_path)])
    captured = capsys.readouterr()

    assert rc == 0
    printed = json.loads(captured.out)
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert printed["status"] == "ok"
    assert printed == written


def test_replay_uses_single_run_record_per_spec_hash(tmp_path):
    project_path = _make_project(tmp_path)
    spec_path = tmp_path / "spec.json"
    spec = specs.create_spec("describe", "demo", inputs={"data": "x"}, options={}, seed=7)
    spec_path.write_text(json.dumps(spec), encoding="utf-8")

    first = specs.run_spec(spec_path, project_path)
    second = specs.run_spec(spec_path, project_path)

    project = Project(project_path)
    try:
        count = project.conn.execute("SELECT COUNT(*) FROM analysis_runs").fetchone()[0]
    finally:
        project.close()

    assert first["spec_hash"] == second["spec_hash"]
    assert count == 1


def test_run_spec_payload_supports_one_sample_ttest(tmp_path):
    project_path = _make_project(tmp_path)
    project = Project(project_path)
    try:
        spec = specs.create_spec(
            "ttest_1samp",
            "demo",
            inputs={"data": "y"},
            options={"null_mean": 4.0, "alternative": "two-sided", "conf_level": 0.95},
            seed=99,
        )
        artifact = specs.run_spec_payload(spec, project)
    finally:
        project.close()

    assert artifact["status"] == "ok"
    assert artifact["result"]["test"] == "One-Sample Student t-test"
    assert "p_value" in artifact["result"]
