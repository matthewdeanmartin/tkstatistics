# tkstatistics Roadmap and Gap Review

## What the code currently does

- Launches a Tkinter GUI with a project explorer, data grid, and output history panel.
- Provides menus for project creation/opening and CSV import.
- Automatically creates a temporary demo project/dataset at startup.
- Stores project data in SQLite (`datasets`, `rows`, `analyses` tables).
- Saves analysis specs (JSON blobs) in SQLite.
- Supports these analyses today: `describe`, `frequency_table` (dispatcher only), `mann_whitney_u` (dispatcher only), `wilcoxon_signed_rank` (dispatcher only), `fisher_exact_2x2` (dispatcher only), `stdlib_simple_regression` (GUI), `ols` (GUI).
- Can execute analyses from saved spec selections in the GUI.

## Highest-priority gaps

## 1) Anti-p-hacking controls are not implemented

- No preregistration gate before inferential tests.
- No locked analysis plan or immutable run ordering.
- No distinction between exploratory vs confirmatory analysis modes.
- No multiplicity controls or warnings for repeated testing.
- No audit report that flags "many tests run, few reported".

## 2) Headless reproducibility path is incomplete

- CLI `--run` only prints "Not yet implemented".
- `core.specs.run_spec(...)` exists, but is not wired to CLI output/export.
- Spec seed is generated, but not consistently used for deterministic execution.
- No spec validation schema/version migration logic.
- No "export complete run artifact" (data + spec + results).

## 3) Statistical scope is much smaller than intended

- Missing planned coverage: parametric tests (t-tests/ANOVA), correlations (Pearson/Spearman/Kendall), chi-square family, resampling/permutation/bootstrap, time-series summaries/smoothing, richer descriptives.
- Current p-values are mostly approximate; no exact/approx mode controls for most tests.
- Assumption checks and warnings are minimal.
- No confidence intervals or p-values for OLS coefficients.

## 4) Quality and correctness hardening is incomplete

- Test suite is effectively a smoke import test only.
- No numerical correctness validation against reference values/golden outputs.
- No regression tests for project persistence and replay behavior.
- No property tests for invariants in nonparametric methods.
- No UI behavior tests for duplicate history/re-run bugs noted in docs.

## 5) Product workflow gaps (SPSS/STATA-like usability)

- No variable metadata editor (labels, types, missing codes, formats).
- Data grid is read-only; no recode/compute/filter/sort/transform workflow.
- No output export formats (HTML/SVG/etc.) yet.
- No graphing implementation despite menu placeholder.
- No analysis wizard UX for assumptions/options/explanations.

## Key observed technical issues to track

- Duplicate method definition in `app/main.py`: `_on_dataset_selected` appears twice.
- Analysis replay appends new output entries each time selection occurs, likely causing duplicate history growth.
- `describe()` uses `statistics.quantiles(..., n=4)` unguarded; very small samples can error.
- Nonparametric functions do not sanitize `None`/non-finite inputs.
- CLI script entry points to `tkstatistics.__main__:main`, but `__main__.py` does not define `main`.

## Proposed implementation roadmap

## Phase 1: Reproducible core and correctness baseline

- Wire CLI `--run` to `core.specs.run_spec`.
- Add JSON output for headless run results.
- Add strict spec validation (`analysis`, dataset existence, inputs/options typing).
- Use spec seed during stochastic procedures.
- Add tests for project save/load roundtrips.
- Add tests for spec creation and replay.
- Add tests for deterministic seeded behavior.
- Fix obvious correctness/packaging issues (entry point, quantile edge cases).

## Phase 2: Anti-p-hacking MVP

- Add an `AnalysisPlan` object in project DB with hypothesis, primary outcomes, test choice, alpha/sidedness, planned covariates/exclusions, and preregistration timestamp/hash.
- Enforce confirmatory mode by blocking p-value computation unless a plan exists.
- Lock key plan fields once the first confirmatory run executes.
- Log all executed analyses with timestamps and spec hashes.
- Add multiple-testing helpers: Benjamini-Hochberg FDR, Bonferroni, and Holm.
- Add transparency output showing declared vs executed tests and undisclosed-extra-tests warnings.

## Phase 3: Broaden statistics coverage (stdlib-only)

- Add parametric module (`ttest_1samp`, `ttest_ind`, `ttest_rel`, one-way ANOVA).
- Add correlation/association functions.
- Add bootstrap and permutation tests with seeded RNG.
- Add effect sizes where applicable.
- Expand nonparametric exact vs approximate choices and tie handling diagnostics.
- Standardize result payload schema across all tests.

## Phase 4: GUI workflow parity with analysis tools

- Add analysis dialogs for new stats modules.
- Add assumptions/options panels per test.
- Add explainability blocks in output covering what ran, assumptions, exact vs approximate method, and interpretation hints.
- Implement graphing (histogram, box, scatter) with Canvas + SVG export.
- Add output export (plain text + JSON first; SVG/HTML next).

## Phase 5: Data management and project ergonomics

- Editable grid with validation.
- Variable metadata editor and missing-value handling policy.
- Data transforms (compute/recode/filter).
- Persistent app settings (recent files, defaults).
- Improve project explorer/output history sync to avoid duplicated entries.

## Acceptance criteria for "usable first release"

- `python -m tkstatistics --run <spec.json> --project <file.statproj>` works end-to-end.
- Confirmatory mode requires preregistration and produces an auditable trail.
- At least 10 core analyses implemented with consistent output schema.
- Deterministic test coverage for stats math and spec replay.
- GUI allows: import data -> run analysis -> inspect assumptions -> export result.

## Suggested immediate next tasks (next 1-2 weeks)

- Fix packaging/entry point and CLI run wiring.
- Implement spec validation + deterministic seed handling.
- Add a minimal `AnalysisPlan` schema and preregistration gate for p-value tests.
- Add baseline numeric tests for `describe`, `mann_whitney_u`, `wilcoxon`, `ols`.
- Fix duplicate history behavior in output/project explorer interactions.
