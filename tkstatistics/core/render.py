# tkstatistics/core/render.py

"""
Human-readable rendering of run artifacts.

The same renderer is used by the CLI (``--format text``) and, in time, the GUI
output viewer, so that headless and interactive output never drift apart.
"""

from __future__ import annotations

from typing import Any


def _fmt_value(value: Any) -> str:
    """Format a single scalar/list value for display."""
    if value is None:
        return "—"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float):
        if value != value:  # NaN
            return "nan"
        return f"{value:.6g}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_fmt_value(v) for v in value) + "]"
    return str(value)


def _render_result(result: dict[str, Any], indent: str = "  ") -> list[str]:
    """Render the analysis result dict as aligned key/value lines."""
    lines: list[str] = []
    width = max((len(str(k)) for k in result), default=0)
    for key, value in result.items():
        lines.append(f"{indent}{str(key).ljust(width)} : {_fmt_value(value)}")
    return lines


def _fmt_cell(value: Any) -> str:
    """Format a correlation/p-value cell into a fixed 8-char field."""
    if value is None:
        return f"{'—':>8}"
    return f"{value:>8.4f}"


def render_correlation_matrix(result: dict[str, Any]) -> list[str]:
    """Render a correlation_matrix result as aligned coefficient + p-value tables."""
    names = result.get("names") or []
    corr = result.get("correlations") or []
    pvals = result.get("p_values") or []
    label_w = max((len(str(n)) for n in names), default=4)

    lines: list[str] = [f"Method: {result.get('method', '')}", ""]

    header = " " * label_w + "".join(f"{str(n):>9}" for n in names)
    lines.append("Correlation coefficients (r):")
    lines.append(header)
    for i, row_name in enumerate(names):
        cells = "".join(" " + _fmt_cell(corr[i][j]) for j in range(len(names)))
        lines.append(f"{str(row_name):<{label_w}}{cells}")

    lines.append("")
    lines.append("Two-sided p-values:")
    lines.append(header)
    for i, row_name in enumerate(names):
        cells = "".join(" " + _fmt_cell(pvals[i][j]) for j in range(len(names)))
        lines.append(f"{str(row_name):<{label_w}}{cells}")

    return lines


def render_artifact_trailer(artifact: dict[str, Any]) -> str:
    """Render only the pre-registration / multiplicity / warnings sections.

    Used when a caller renders the result body itself (e.g. the GUI's rich
    regression table) but still wants the shared trailer blocks.
    """
    lines: list[str] = []

    prereg = artifact.get("preregistration")
    if prereg:
        lines.append("Pre-registration:")
        lines.append(f"  plan id    : {prereg.get('plan_id', '')}")
        lines.append(f"  hypothesis : {prereg.get('hypothesis', '')}")
        if prereg.get("prediction"):
            lines.append(f"  prediction : {prereg['prediction']}")
        lines.append(f"  alpha      : {_fmt_value(prereg.get('alpha'))}")
        lines.append(f"  faithful   : {_fmt_value(prereg.get('faithful'))}")
        for deviation in prereg.get("deviations", []):
            lines.append(f"  deviation  : {deviation}")

    multiplicity = artifact.get("multiplicity")
    if multiplicity:
        if lines:
            lines.append("")
        lines.append("Multiplicity correction:")
        lines.extend(_render_result(multiplicity))

    warnings = artifact.get("warnings") or []
    if warnings:
        if lines:
            lines.append("")
        lines.append("Warnings:")
        for warning in warnings:
            lines.append(f"  - {warning}")

    return "\n".join(lines)


def render_artifact(artifact: dict[str, Any]) -> str:
    """Render a run artifact (from ``run_spec_payload``) as readable text."""
    spec = artifact.get("spec", {})
    lines: list[str] = []

    analysis = spec.get("analysis", "<unknown>")
    dataset = spec.get("dataset", "<unknown>")
    mode = spec.get("mode", "exploratory")

    lines.append(f"Analysis : {analysis}")
    lines.append(f"Dataset  : {dataset}")
    lines.append(f"Mode     : {mode}")
    status = artifact.get("status")
    if status and status != "ok":
        lines.append(f"Status   : {status}")
    spec_hash = artifact.get("spec_hash") or ""
    if spec_hash:
        lines.append(f"Spec hash: {spec_hash[:12]}")

    # A refused confirmatory run carries no result, only a refusal message.
    if status == "refused":
        lines.append("")
        lines.append(f"REFUSED: {artifact.get('message', 'confirmatory gate')}")
        return "\n".join(lines)

    lines.append("")

    result = artifact.get("result", {})
    if isinstance(result, dict) and result.get("error"):
        lines.append(f"ERROR: {result['error']}")
        if result.get("details"):
            lines.append(f"  {result['details']}")
    elif isinstance(result, dict) and spec.get("analysis") == "correlation_matrix":
        lines.append("Result:")
        lines.extend(render_correlation_matrix(result))
    elif isinstance(result, dict):
        lines.append("Result:")
        lines.extend(_render_result(result))
    else:
        lines.append(f"Result: {_fmt_value(result)}")

    trailer = render_artifact_trailer(artifact)
    if trailer:
        lines.append("")
        lines.append(trailer)

    return "\n".join(lines)
