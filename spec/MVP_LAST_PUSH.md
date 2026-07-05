# MVP last push: first PyPI release

## Recommendation

Ship the current product as **0.2.0 alpha** once the release gate below is green.
The existing GitHub draft is already `v0.2.0`, while `0.1.0` is recorded in the
changelog. Rewriting that history to make the first PyPI upload `0.1.0` would add
risk without improving the package.

The MVP is real. The code already delivers the distinctive workflow described
in the roadmap: committed pre-registration plans, a confirmatory p-value gate,
deviation recording, multiplicity adjustment, and an audit report. It also has
a useful statistical core, a GUI, a headless runner, and SVG-capable charts.
The remaining work is release hardening, not another product phase.

## Current release snapshot

- 110 tests pass with 52.5% statement coverage (35% required).
- The statistical tests include SciPy, NumPy, and statsmodels equivalence checks.
- Wheel and source distribution build successfully.
- The console entry point exposes GUI, run, plan-commit, audit, text, and JSON
  modes.
- Runtime code has no third-party package dependencies.
- Supported Python is honestly declared as 3.11 through 3.14, matching the syntax,
  standard-library APIs, and tox configuration.
- The CI workflow now runs the maintained, non-mutating `make check-ci` gate rather
  than the stale `just check` path that caused the latest GitHub failure.

## Release gate

Everything in this section is required before publishing the draft release.

- [x] Unit and equivalence tests pass.
- [x] Coverage exceeds the configured floor.
- [x] Ruff, Black, isort, mypy, pylint, and Bandit gates pass locally.
- [x] Build both wheel and sdist from standards-compliant metadata.
- [x] Synchronize `pyproject.toml` and `tkstatistics/__about__.py` metadata.
- [x] Declare the actual minimum Python version and remove the unused runtime
  backport dependency.
- [x] Replace the stale README with accurate installation, GUI, CLI,
  pre-registration, and alpha-status documentation.
- [x] Upgrade and lock development dependencies with `uv lock --upgrade`.


## Explicit MVP scope

The first PyPI version promises:

1. Teaching-sized local datasets, not large-data performance.
1. Reproducible exploratory analyses from a project plus JSON spec.
1. Confirmatory analyses that require a previously committed, matching plan.
1. An audit trail that distinguishes declared and executed testing.
1. The analyses and charts currently wired into the dispatcher and GUI.
1. Standard-library runtime operation on Python 3.11 through 3.14.

It does **not** promise a stable public Python API, exact small-sample methods for
every nonparametric test, every plot for every result type, editable data
management, or clinical/regulatory validation. Those belong after the alpha.

## Post-release priorities

These are important, but they should not hold the first package upload:

1. Raise coverage around GUI behavior, CSV import, and CLI error paths.
1. Add exact/tie/continuity-corrected modes for Mann-Whitney and Wilcoxon.
1. Standardize every analysis result payload and document it as a public schema.
1. Add installed-wheel smoke testing to CI on Windows and Linux.
1. Improve data editing, metadata, transforms, and report export.
1. Expand model diagnostics and model-comparison workflows.
