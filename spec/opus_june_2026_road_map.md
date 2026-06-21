# tkstatistics — Roadmap (June 2026)

*Author: Opus 4.8 review, 2026-06-20. Supersedes the framing in `docs/ROADMAP_TODO.md`,
which understates how much of the inferential core already works.*

## 1. The three pillars

The professor-driven vision has three product pillars. This roadmap is organized
around getting each to a credible, teachable state:

1. **Visualizations** — see the data and the model, not just a table of numbers.
2. **Model building** — declare a model, fit it, inspect it, compare alternatives.
3. **Preregistered hypothesis testing** — you must *announce* the hypothesis and
   the test before the app will reveal a p-value. This is the anti-p-hacking pillar
   and the single feature that makes tkstatistics different from every other package.

The fourth, cross-cutting pillar is the constraint that gives the project its identity:

4. **Stdlib-only, equivalence-proven.** No numpy/scipy/pandas at runtime. Every
   numeric routine ships with a test proving it matches scipy/numpy/statsmodels to
   tight tolerance. (scipy/numpy stay in the dev group purely as oracles — they are
   already there in `pyproject.toml`.)

> Honest scope note: this is explicitly *not* for large data. Pure-Python + SQLite
> row storage means we target teaching-sized datasets (≤ ~10⁴–10⁵ rows). Performance
> work is about not being embarrassing, not about competing with vectorized engines.

## 2. Where the code actually is today

A fair assessment, because it changes what's worth doing next.

### Solid / working
- **Inferential core is real, not stubs.** `parametric.ttest_1samp` / `ttest_ind`
  ship a hand-rolled Student-t CDF/PPF (continued-fraction regularized incomplete
  beta) that **matches scipy to `rel_tol=1e-8`** — there are passing equivalence
  tests in `tests/test_parametric.py`. This is the quality bar for the whole project.
- **Reproducible headless runner works end-to-end.** `cli.py --run <spec> --project <proj>`
  → `specs.run_spec` → validated, seeded, hashed run artifact persisted to SQLite
  (`analysis_runs`, keyed by `spec_hash` with UPSERT). The old roadmap's "CLI prints
  Not yet implemented" is stale.
- **Spec validation is thorough** — per-analysis input-role rules, option whitelists,
  type checks, dataset/column existence (`core/specs.py`).
- **Multiplicity correction is wired in** — Holm-Bonferroni + Bonferroni
  (`stats/multiplicity.py`), and `run_spec_payload` auto-adjusts each p-value against
  *all prior runs on the same dataset*. This is a genuine anti-p-hacking primitive.
- Regression: `ols` (from-scratch normal equations via `linalg_small`) and
  `stdlib_simple_regression`. Nonparametric: Mann-Whitney U, Wilcoxon signed-rank,
  Fisher exact 2×2. Descriptives + frequency table.
- GUI shell exists: project explorer, data grid, output viewer, dialogs (~1090 LOC).

### Gaps that block the three pillars
- **Preregistration does not exist.** `spec` carries `mode` (`exploratory`/
  `confirmatory`) and a `plan_id`, but there is **no `AnalysisPlan` table, no gate,
  no UI, and nothing enforces confirmatory mode**. The headline feature is currently
  just two unused fields. *This is the highest-leverage gap.*
- **No visualizations.** Menu placeholder only; no Canvas rendering, no SVG export.
- **No model-building workflow.** OLS exists as a function but there's no notion of a
  named, saved, inspectable, comparable *model* object.
- **Regression inference is incomplete.** `ols`/`stdlib_simple_regression` compute
  t-statistics but explicitly punt on p-values/CIs ("requires a t-distribution CDF,
  not available in stdlib"). But we **already have that CDF** in `parametric.py` —
  it just needs to be shared. Low-effort, high-value.
- **Equivalence tests cover only parametric.** No golden-value tests for
  nonparametric, OLS, or descriptives against scipy/statsmodels.
- Known correctness nits: `describe()` calls `statistics.quantiles(n=4)` unguarded
  (errors on n<2); nonparametric functions don't sanitize `None`/non-finite; MWU/
  Wilcoxon offer only the normal approximation (no exact small-sample p, no tie/
  continuity correction).

## 3. Guiding principles

- **Every numeric function gets an equivalence test before it's "done."** Pattern is
  already established: `pytest.importorskip("scipy.stats")`, compare to `rel_tol=1e-8`.
  Pick scipy/numpy/statsmodels as the oracle per routine.
- **Share the special-function kernels.** The t-CDF/PPF, incomplete beta, erf-based
  normal CDF, etc. belong in one `stats/distributions.py`, used by tests *and*
  regression *and* the future chi-square/F routines. Don't reimplement per module.
- **The spec is the source of truth.** Anything the GUI can do, the headless runner
  must be able to reproduce from a spec + project. This is what makes preregistration
  auditable.
- **Confirmatory results are gated, exploratory results are free.** Exploration stays
  frictionless; the ceremony only applies when you ask for a confirmatory p-value.

## 4. Phased plan

### Phase 0 — Correctness & foundations (1–2 weeks)
*Make the existing core trustworthy and unblock everything downstream.*

- [ ] Extract `stats/distributions.py`: move `_student_t_cdf/_ppf`,
      `_regularized_incomplete_beta`, `_betacf`, add `normal_cdf/ppf` (erf-based) and
      `chi2_cdf`, `f_cdf`. One home for special functions.
- [ ] Use that CDF to add **p-values + confidence intervals to `ols` and
      `stdlib_simple_regression`** (the "not available in stdlib" note is now false).
- [ ] Harden inputs: `describe()` guards small-n quantiles; nonparametric functions
      run `_clean_numeric` like parametric does.
- [ ] Equivalence-test backfill: golden tests vs scipy/statsmodels for `ols`,
      `mann_whitney_u`, `wilcoxon_signed_rank`, `fisher_exact_2x2`, `describe`.
- [ ] Add `--format {json,text}` to the CLI and a human-readable result renderer
      (shared with the GUI output viewer).
- [ ] Roundtrip tests: project save/load, spec create→validate→run→persist→reload.

**Exit:** every shipped analysis has a passing equivalence test; regression reports
full inference; CLI runs are reproducible and pretty-printable.

### Phase 1 — Preregistration / anti-p-hacking MVP (2–3 weeks) — *the differentiator*
*Turn `mode`/`plan_id` from dead fields into an enforced workflow.*

- [ ] **`AnalysisPlan` schema + table.** Fields: hypothesis statement (free text),
      directional prediction, analysis name, dataset, input roles, options
      (alpha, sidedness), planned exclusions/covariates, `created_at`, and a
      **`plan_hash`** (sha256 of canonicalized plan, mirroring `compute_spec_hash`).
- [ ] **Pre-registration ceremony.** A plan, once committed, is immutable; its hash is
      recorded. The data may already be loaded, but the *result is sealed*.
- [ ] **The gate.** In `run_spec_payload`, when `mode == "confirmatory"`:
      require a matching committed `plan_id`; verify the spec's analysis/inputs/options
      are consistent with the plan; **only then compute & reveal the p-value.** A
      confirmatory spec with no plan → refusal, not a result.
- [ ] **The reveal.** GUI: "Declare hypothesis" dialog → plan saved (result hidden) →
      explicit "Reveal result" action runs the sealed test and shows it once. Mirror
      the SPM "announce, then reveal" demo flow in `examples/mean_hypothesis_demo`.
- [ ] **Audit / transparency report.** Per dataset: declared confirmatory tests vs all
      executed tests, with an **"undisclosed extra tests" warning** when exploratory
      runs outnumber declarations. Surface the existing Holm-Bonferroni adjusted p
      alongside the raw p in every confirmatory result.
- [ ] **Deviation log.** If an executed confirmatory spec differs from its plan, record
      the diff rather than silently allowing or blocking it — preregistration is about
      *transparency*, not handcuffs.

**Exit:** you cannot obtain a confirmatory p-value without a prior committed plan; the
audit report makes p-hacking visible; the whole flow is reproducible headlessly.

### Phase 2 — Visualizations (2–3 weeks)
*Pure-Tk Canvas rendering + SVG export, no plotting deps.*

- [ ] `viz/` module producing chart models (data → drawable primitives), rendered to
      **both** a Tk `Canvas` and an **SVG string** from the same model (SVG = export +
      headless/testable output without a display).
- [ ] Core charts: histogram, box plot, scatter, scatter-with-fitted-line,
      residual-vs-fitted, Q-Q plot (uses the normal PPF from Phase 0).
- [ ] Each analysis result can declare its "natural" plot(s); output viewer offers them.
- [ ] Charts are spec-addressable (`"analysis": "histogram"`, etc.) so they're
      reproducible and exportable headlessly.
- [ ] Snapshot-test SVG output (string compare / structural assertions) — no GUI needed.

**Exit:** every descriptive/regression result has at least one one-click plot;
plots export to SVG; plots are reproducible from a spec.

### Phase 3 — Model building (2–3 weeks)
*Promote "run a regression" into "build, inspect, and compare models."*

- [ ] A **`Model`** concept: named, saved (new table), re-fittable from spec. Holds
      formula/inputs, fitted coefficients, inference, diagnostics, fit metrics.
- [ ] OLS upgrades: standardized coefficients, AIC/BIC, F-test for overall
      significance, VIF/multicollinearity warning, diagnostics (residual normality,
      heteroscedasticity hint). All equivalence-tested vs statsmodels.
- [ ] One-way (and ideally two-way) **ANOVA** + the F-distribution CDF (Phase 0).
- [ ] **Correlation matrix** (Pearson/Spearman/Kendall) with per-pair p-values.
- [ ] **Model comparison view:** side-by-side fit metrics; nested-model F-test.
- [ ] Models integrate with Phase 1: a confirmatory model can be preregistered the
      same way a single test is.

**Exit:** user can declare a model, fit it, read full inference + diagnostics, and
compare two models — all stdlib, all equivalence-tested.

### Phase 4 — Data management & ergonomics (ongoing)
*The SPSS/Stata-like grind that makes it usable for real coursework.*

- [ ] Variable metadata editor (labels, measurement level, missing-value codes).
- [ ] Editable grid + transforms: compute, recode, filter, sort.
- [ ] Config (`toml`/`ini`, per `docs/TODO.md`): choose stdlib vs own algorithm,
      exact vs approximate p-value methods.
- [ ] Fix logged UI bugs: duplicate analysis-history entries, re-run-on-select,
      modal-on-error ("it isn't 1995"), auto-select univariate when only one var.
- [ ] Export: result → text/JSON (done-ish) → HTML report bundling plots + audit trail.

## 5. Suggested next 1–2 weeks (concrete)

1. Create `stats/distributions.py`; move the special functions; add `normal_cdf/ppf`,
   `chi2_cdf`, `f_cdf` with scipy equivalence tests.
2. Wire regression p-values/CIs through it; delete the "not available in stdlib" notes.
3. Backfill equivalence tests for OLS + the three nonparametric tests.
4. Spike the `AnalysisPlan` table + `plan_hash` and the confirmatory gate in
   `run_spec_payload` (no GUI yet) — prove the "no plan ⇒ no p-value" rule headlessly.
5. Guard `describe()` small-n quantiles; sanitize nonparametric inputs.

## 6. Definition of "usable first release"

- `tkstatistics --run <spec.json> --project <file.statproj>` works end-to-end with
  human-readable or JSON output. ✅ (mostly there — needs `--format`)
- **Confirmatory mode is impossible without a prior committed plan**, and the audit
  report makes undisclosed testing visible. ⬜ *(the headline feature)*
- ≥ 10 analyses, each with a consistent result schema **and a passing equivalence
  test vs scipy/numpy/statsmodels**. 🔶 (have the analyses, missing most tests)
- At least one plot per result type, exportable to SVG. ⬜
- GUI flow: import → declare hypothesis → reveal result → view plot → export. ⬜
