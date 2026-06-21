from __future__ import annotations

from tkstatistics.core import render


def test_render_ok_artifact():
    artifact = {
        "spec": {"analysis": "ttest_1samp", "dataset": "d", "mode": "confirmatory"},
        "spec_hash": "abcdef1234567890",
        "status": "ok",
        "result": {"test": "One-Sample Student t-test", "p_value": 0.04, "n": 10},
        "warnings": ["heads up"],
        "multiplicity": {"method": "holm-bonferroni", "adjusted_p_value": 0.08},
    }
    text = render.render_artifact(artifact)
    assert "ttest_1samp" in text
    assert "p_value" in text
    assert "Multiplicity correction" in text
    assert "heads up" in text


def test_render_refused_artifact():
    artifact = {
        "spec": {"analysis": "ttest_1samp", "dataset": "d", "mode": "confirmatory"},
        "status": "refused",
        "message": "Confirmatory mode requires a pre-registered plan.",
        "result": None,
    }
    text = render.render_artifact(artifact)
    assert "REFUSED" in text
    assert "pre-registered plan" in text
    # Must not crash or emit a stray formatting of None.
    assert "Result:" not in text


def test_render_artifact_trailer_only():
    artifact = {
        "preregistration": {
            "plan_id": "abc123",
            "hypothesis": "mean differs",
            "alpha": 0.05,
            "faithful": True,
            "deviations": [],
        },
        "multiplicity": {"method": "holm-bonferroni", "adjusted_p_value": 0.08},
        "warnings": ["careful"],
    }
    trailer = render.render_artifact_trailer(artifact)
    assert "Pre-registration" in trailer
    assert "mean differs" in trailer
    assert "Multiplicity correction" in trailer
    assert "careful" in trailer
    # The trailer must NOT include the analysis header or result body.
    assert "Analysis :" not in trailer
    assert "Result:" not in trailer


def test_render_artifact_trailer_empty_when_nothing_extra():
    assert render.render_artifact_trailer({"result": {"p_value": 0.5}}) == ""


def test_render_artifact_includes_prereg_block():
    artifact = {
        "spec": {"analysis": "ttest_1samp", "dataset": "d", "mode": "confirmatory"},
        "spec_hash": "deadbeef",
        "status": "ok",
        "result": {"test": "One-Sample Student t-test", "p_value": 0.03},
        "preregistration": {"plan_id": "p1", "hypothesis": "h", "alpha": 0.05, "faithful": True, "deviations": []},
    }
    text = render.render_artifact(artifact)
    assert "Pre-registration" in text
    assert "p1" in text


def test_render_error_result():
    artifact = {
        "spec": {"analysis": "describe", "dataset": "d"},
        "spec_hash": "00",
        "status": "ok",
        "result": {"error": "bad input", "details": "n<2"},
    }
    text = render.render_artifact(artifact)
    assert "ERROR: bad input" in text
    assert "n<2" in text
