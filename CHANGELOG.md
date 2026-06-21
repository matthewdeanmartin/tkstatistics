# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- `stats/distributions.py`: shared stdlib-only special functions and CDFs/PPFs
  (Student-t, normal, chi-square, F, regularized incomplete beta), equivalence-tested
  against scipy.
- Coefficient p-values and confidence intervals for `ols` and `stdlib_simple_regression`,
  computed via the shared Student-t distribution.
- Pre-registration / anti-p-hacking workflow: `AnalysisPlan` (`core/plans.py`) with
  deterministic plan hashing, a committed-plan table, and a confirmatory gate in
  `run_spec_payload` that refuses to reveal a p-value unless a matching plan was
  committed first. Deviations from a plan are recorded, not silently blocked.
- Transparency audit report (`specs.audit_dataset`) flagging undisclosed/exploratory
  inferential testing.
- CLI: `--format {json,text}`, `--commit-plan`, and `--audit`; shared human-readable
  artifact renderer (`core/render.py`).
- Equivalence test suites for distributions, regression, nonparametric tests, and
  descriptives.
- Visualization layer (`viz/`): backend-agnostic chart scenes rendered to both an
  SVG string (exportable, testable) and a Tk Canvas. First chart: histogram, with
  `compute_bins` equivalence-tested against numpy.histogram.
- Working **Histogram** menu item (previously a no-op): variable/bin dialog opens a
  chart window with SVG export.
- Additional charts under the Graphs menu, all sharing the scene/SVG/Canvas pipeline:
  **box plot** (Tukey quartiles, 1.5·IQR whiskers, outliers), **scatter plot** with an
  optional OLS fitted line, and a **normal Q-Q plot** (Blom plotting positions, using
  the from-scratch `normal_ppf`). `compute_box_stats` and `compute_qq_points` are
  cross-checked against `statistics`/scipy.
- Shared `viz/axes.py` plot-area + tick helpers; the histogram builder was refactored
  onto them.
- **Much more of the backend is now reachable from the GUI.** New Analyze menu surface:
  - **Hypothesis Tests** submenu wiring the five existing tests (one-sample t,
    independent t, Mann-Whitney U, Wilcoxon signed-rank, Fisher's exact 2×2) with
    option dialogs (alternative, variance assumption, null mean, 2×2 table entry).
  - **Pre-register Hypothesis...** / **Run Confirmatory Test...** — the anti-p-hacking
    workflow in the GUI: declare a hypothesis (sealed), then reveal the confirmatory
    result against a committed plan. Refusals surface as a clear message.
  - **Audit Report...** — the transparency report (declared vs executed, undisclosed-
    testing warnings) rendered into the output viewer.
- Project Explorer now shows a **Pre-registered Plans** node; selecting a plan shows
  its hypothesis and locked options.
- GUI analyses now run through the same `run_spec_payload` pipeline as the CLI, so they
  get reproducible artifacts, multiplicity correction, and the confirmatory gate for
  free; results render via the shared `core.render` text (no more per-analysis drift).
- Regression output table now shows coefficient p-values (added in this release) and
  tolerates missing values.
- `Makefile` (`make install` → `uv sync --all-extras --all-groups`, plus `test`,
  `lint`, `run`); `statsmodels` added to the dev group as a test oracle.

### Changed
- `describe()` no longer errors on single-value samples (quantiles guarded for n<2).
- Nonparametric tests now drop missing/non-finite values (and incomplete pairs for
  Wilcoxon) before computing.
- Multiplicity pooling now includes nonparametric/exact p-values, not just `p_value`.

## [0.1.0] - 2026-06-20
### Added
- Initial release of `tkstatistics`, a statistics application using only the Python Standard Library.
