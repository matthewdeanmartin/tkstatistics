# PEP XXXX — **tkstatistics**: A Pure-Stdlib Statistical Desktop Application

**Author:** Matthew Martin (editor), ChatGPT (scribe)
**Status:** Draft
**Type:** Standards Track (Application Specification)
**Created:** 2025-09-26
**Python-Version:** 3.12+
**Requires:** None (stdlib only)
**Discussions-To:** `tkstatistics-pep@python.org` (hypothetical)

---

## Abstract

This PEP specifies **tkstatistics**, a **desktop statistics application** implemented **exclusively with the Python standard library**. It provides an SPSS-lite / Statistica-style GUI using **tkinter**, a persistent project store using **sqlite3**, and tabular I/O via **csv** and other stdlib modules. The analytic focus is **small-sample** and **nonparametric** methods (robust to distributional assumptions), while exposing parametric tests and summaries available through the stdlib (`statistics`, `math`, `random`) and straightforward, well-documented formulas.

No third-party packages (e.g., pandas, numpy, scipy, matplotlib) are used. All functionality—UI, data management, algorithms, reporting, and reproducibility—is built from the stdlib.

---

## Motivation and Rationale

Many Python users—educators, students, analysts—need a **simple, install-free** statistical tool that:

* runs anywhere Python does;
* offers a **menu-driven GUI**;
* is **transparent and reproducible**;
* emphasizes **small-sample** correctness and **nonparametric** robustness;
* avoids heavyweight dependencies.

While Python offers superb libraries, this PEP focuses on the educational and operational value of **“only stdlib”**: everything visible, inspectable, and portable.

---

## Scope

### In Scope

* **GUI:** tkinter-based menus, dialogs, data grid, chart canvas.
* **Storage:** sqlite3 project database; CSV/TSV import/export; JSON/INI configs.
* **Tabular data:** lists/dicts/dataclasses; sqlite tables; `csv.DictReader`.
* **Analytics:** descriptive stats; exact or distribution-free tests where feasible; simple parametric tests; bootstrapping/resampling; light time-series smoothing.
* **Visualization:** basic charts with `tkinter.Canvas` and SVG generation via `xml.etree.ElementTree`.
* **Reproducibility:** JSON “analysis specs,” CLI re-runner (`argparse`), logging.
* **Performance:** tuned for small to medium datasets (e.g., ≤ ~50k rows depending on RAM/UI needs).

### Out of Scope

* Advanced modeling (GLMs, mixed effects, survival), high-dimensional inference.
* Publication-grade interactive plots; 3D graphics.
* Distributed computing; GPU; big-data IO.

---

## User Experience

### Primary Persona

* **Educator/Student/Analyst** with modest datasets, wanting GUI-first workflows and understandable outputs.

### UX Principles

* **Wizards over walls:** Dialogs explain assumptions and output interpretation.
* **Show the recipe:** Each result pane includes the **exact computation notes** and the JSON spec used.
* **Undo/Redo everywhere:** Transformations and imports included.
* **One-click export:** Tables → CSV/HTML; Charts → SVG/PNG (PNG via Pillow is *not* allowed; use Canvas postscript or SVG only).

---

## Application Layout (tkinter)

* **Main Window**

  * **Menu Bar**

    * *File:* New Project, Open, Save, Import CSV, Export CSV, Exit
    * *Data:* Define Variables, Recode/Compute, Merge/Join, Filter/Sort
    * *Analyze:* Descriptives, Compare Groups, Correlation/Association, Regression (simple/multiple), Nonparametric Tests, Resampling/Bootstrap, Time Series Smoothing
    * *Graphs:* Histogram, Boxplot, Scatter (with optional fit), Line/Area
    * *Window:* Data Editor, Output Viewer, Syntax Viewer
    * *Help:* Methods Glossary, About
  * **Status Bar**: dataset name, row/col count, active filter, selection stats.
* **Panels**

  * **Data Editor**: `ttk.Treeview` grid + in-cell `Entry` overlay for edits.
  * **Output Viewer**: Tree of results (tables, charts, logs).
  * **Syntax Viewer**: JSON analysis specs, with re-run button.

---

## Data Model

### Logical Data Types

* **Numeric** (float/decimal), **Integer**, **Categorical** (with labels), **Boolean**, **Date/Time** (via `datetime`), **String**.
* **Missing Values**: `None` sentinel (or user-defined codes; mapped to `None`).

### In-Memory Structures

* **Rows:** `list[dict[str, Any]]` or `dataclasses` for typed rows.
* **Columns:** `dict[str, list[Any]]` for columnar ops where convenient.
* **Indexes:** stored as columns; no external index structure.

### Persistence (sqlite3)

* Project file is a single **SQLite** DB (e.g., `myproj.statproj`).
* **Schema (minimal):**

  * `datasets(id INTEGER PK, name TEXT UNIQUE, created_at, updated_at)`
  * `variables(id PK, dataset_id FK, name, label, type, fmt, missing_code TEXT)`
  * `data_cells(dataset_id FK, row_idx INT, col_name TEXT, value TEXT)`
    (Option: one row per cell for simplicity; or a row-wise JSON blob table:
    `rows(dataset_id, row_idx, payload_json)` for performance.)
  * `analyses(id PK, dataset_id FK, spec_json TEXT, created_at)`
  * `results(id PK, analysis_id FK, kind TEXT, payload_json TEXT, svg BLOB NULL, created_at)`
  * `settings(key TEXT PK, value TEXT)`

*(Exact storage form is an implementation detail; the PEP mandates portability and human-readable specs, not a fixed schema.)*

---

## Import/Export

* **CSV/TSV:** `csv` with sniffing (`csv.Sniffer`), encoding handling (`io.TextIOWrapper`).
* **JSON:** for dataset snapshots and analysis specs.
* **HTML:** simple table export via string templates (no external CSS required).
* **SVG:** charts via `xml.etree.ElementTree`; Canvas → PostScript for quick print.

---

## Analysis Catalogue (Stdlib-Only)

### Descriptives

* N, missing, mean, median, mode(s), variance (population/sample), stdev, min, max, quartiles/percentiles, IQR, MAD (median absolute deviation).

  * Use `statistics` where available (`mean`, `median`, `pstdev`, `stdev`, `quantiles`), otherwise simple implementations.

### Association & Correlation

* **Pearson** (with guarding for small n and zero variance).
* **Spearman** (rank via sorting; average ranks on ties).
* **Kendall’s tau-b** (optional; O(n²) pair counting acceptable for small n).
* **Chi-square** tests:

  * Goodness-of-fit (one-way).
  * Independence (two-way crosstabs). Offer **Fisher’s exact test** for 2×2 (exact enumeration; viable for small counts).

### Group Comparisons

* **Parametric:**

  * 1-sample t (CI for mean; uses `math`, `statistics`).
  * 2-sample t (independent; pooled/unpooled variance).
  * Paired t.
  * One-way ANOVA (balanced/unbalanced; simple sums of squares).
* **Nonparametric:**

  * **Sign test** (binomial, small-sample exact).
  * **Wilcoxon signed-rank** (paired).
  * **Mann–Whitney U** (independent two-sample).
  * **Kruskal–Wallis** (k groups).
  * **Median test** (simple).
  * **Fisher’s exact** (2×2).
* **Effect Sizes** (where applicable, e.g., Cohen’s d, rank-biserial, Cliff’s delta) computed via formulas (no distributions required).

### Regression (Educational)

* **Simple Linear Regression** (closed-form; slope/intercept, SE, t for slope, R², CI).
* **Multiple Linear Regression** (small k): solve normal equations `(XᵀX)^{-1}Xᵀy` with a tiny, well-tested pure-Python linear algebra helper (Gauss-Jordan or Cholesky with checks). Warn on multicollinearity (condition number heuristic).

  * *Intended for small problems (e.g., ≤ 20 predictors, ≤ few thousand rows).*

### Resampling

* **Bootstrap** (mean, median, difference in means, regression coefficients).
* **Permutation tests** for group differences and correlation (user-set iterations).

### Time Series (Light)

* Moving average, exponentially weighted moving average (EWMA).
* Simple lag/lead transformations.

### Power (Optional, Small-n Heuristics)

* Back-of-envelope calculators using normal approximations—clearly labeled as **approximate**.

---

## Algorithms and Accuracy

* All tests include **assumption notes**, **small-sample caveats**, and **exact/approximate** designation.
* p-values:

  * Where exact enumerations are feasible (sign test, Fisher 2×2, small-n Wilcoxon via exact tables/enumeration), do exact.
  * Otherwise, rely on **distribution approximations** covered by closed-form CDFs we can implement (e.g., Student-t via `math` plus series/continued fractions) or **resampling** (bootstrap/permutation) when analytic CDFs are out of scope.
  * The app must **clearly mark** when a p-value is from resampling vs analytic approximation.

---

## Visualization (Stdlib Only)

* **Histogram** (bin rules: Sturges, Scott, Freedman–Diaconis).
* **Boxplot** (with outlier marks).
* **Scatter** (optional fit line, with CI shading approximated).
* **Line/Area** (for time series).

Charts render to **tkinter.Canvas** and export to **SVG** via `xml.etree.ElementTree`. No external plotting libraries.

---

## Reproducibility

* Every analysis run generates a **JSON spec**:

  ```json
  {
    "analysis": "mann_whitney_u",
    "dataset": "study1",
    "inputs": {"x": "score", "group": "treatment"},
    "options": {"alternative": "two-sided", "continuity": true, "exact": true},
    "seed": 12345,
    "version": "tkstatistics 0.1"
  }
  ```
* Specs are saved in the project DB and visible in the **Syntax Viewer**.
* A CLI (`python -m tkstatistics --run spec.json`) re-executes a spec headlessly and writes results as JSON/HTML/SVG to an output folder.
* **Logging:** `logging` with rotating handlers; each run is auditable.

---

## Internationalization and Accessibility

* All UI strings pass through a simple translation map (JSON/INI).
* Keyboard navigation, high-contrast mode, font scaling via tkinter options.
* Tooltips and “what’s this?” help for stats dialogs.

---

## Security Considerations

* **Expression evaluator** (for “Compute Variable”) uses `ast.parse` + whitelist of nodes and functions (`math` subset); **no `eval`**.
* **Project files** are SQLite; no triggers or extensions are loaded.
* **CSV import** treats text as data; no execution.
* Random seeds are user-controlled for reproducibility.

---

## Performance Considerations

* Intended for **small/medium** tables.
* Use **sqlite** for joins/filtering/aggregation when feasible; pull only necessary columns into memory.
* Long-running tasks dispatched via `concurrent.futures.ThreadPoolExecutor`; UI stays responsive; progress via queues + `after()`.

---

## Testing Strategy (Stdlib Only)

* **Unit tests:** `unittest` or `doctest` for algorithms (edge cases, small-n exacts).
* **Golden files:** JSON result samples for deterministic seeds.
* **Property-style checks:** randomized small datasets with `random` to ensure symmetries (e.g., U(x,y) + U(y,x) = n₁n₂, etc.).
* **UI smoke tests:** minimal “open → histogram → export SVG” sequence (headless where possible).

---

## Reference Package Layout

```
tkstatistics/
  __main__.py          # CLI entry
  app/
    main.py            # Tk root, menu wiring
    grid.py            # Treeview-based data editor
    charts.py          # Canvas & SVG writers
    dialogs.py         # imports, analyses, transforms
    glossary.py        # inline method docs
  core/
    project.py         # sqlite3 schema & persistence
    dataset.py         # in-memory adapters
    io_csv.py          # csv import/export
    specs.py           # JSON spec recorder/runner
    logging_cfg.py     # logging setup
    undo.py            # undo/redo stack
    utils.py
  stats/
    descriptives.py
    nonparametric.py   # sign, wilcoxon, mann-whitney, kruskal, fisher
    parametric.py      # t-tests, anova
    regression.py      # OLS (simple/multiple)
    resample.py        # bootstrap, permutation
    timeseries.py      # MA, EWMA
    linalg_small.py    # tiny, well-tested solver
  tests/
    ...
```

---

## Minimal API Sketches (Internal)

```python
# stats/nonparametric.py
def mann_whitney_u(
    x: list[float],
    y: list[float],
    *,
    alternative="two-sided",
    exact: bool | None = None
) -> dict:
    """Return U statistics, effect size, and p-value (exact if feasible)."""


# stats/parametric.py
def ttest_ind(a, b, *, equal_var=False, alternative="two-sided") -> dict:
    ...


# stats/regression.py
def ols(X: list[list[float]], y: list[float]) -> dict:
    """Return coeffs, stderr, t-stats, CI, R2; small-problem guarded solver."""
```

---

## Interpretable Output

Each result node in the Output Viewer contains:

* **Table:** neatly formatted plain table (copyable, exportable).
* **Notes:** test assumptions, exact/approximate label, small-n warnings.
* **Spec:** compact JSON spec block (view/copy).
* **Chart** (if applicable): Canvas preview + “Export SVG”.

---

## Backwards Compatibility

Not applicable (new application). The PEP imposes no changes on Python itself.

---

## Reference Implementation Notes

* Algorithms favor **clarity over micro-optimization**; well-commented math.
* For exact tests, prefer **enumeration** or **dynamic programming** with guardrails on n.
* Multiple regression uses a conservative solver with conditioning checks; surfaces warnings for ill-posed problems.

---

## Alternatives Considered

* Using numpy/scipy/matplotlib: rejected to preserve **stdlib-only** guarantee.
* Web UI (tkinter → webview): rejected to keep deployment trivial and offline.
* Pandas-style DataFrame emulation: rejected to reduce scope/complexity.

---

## Open Questions (for discussion)

* Should we ship **pre-computed small-n exact critical values** (JSON tables) for certain tests to speed exact p-values?
* Default to **resampling** when analytic distributions are out of scope, or require the user to opt-in?
* Adopt **Decimal** for numeric stability by default, or float with optional Decimal mode?

---

## Copyright

This document has been placed in the public domain.

---

### Appendix A — Example JSON Spec

```json
{
  "analysis": "wilcoxon_signed_rank",
  "dataset": "pilot_study",
  "inputs": {"x_before": "pre", "x_after": "post"},
  "options": {"zero_method": "wilcox", "alternative": "less", "exact": true},
  "seed": 20250926,
  "version": "tkstatistics 0.1"
}
```

### Appendix B — Example SQLite DDL (illustrative)

```sql
CREATE TABLE datasets (
  id INTEGER PRIMARY KEY, name TEXT UNIQUE, created_at TEXT, updated_at TEXT
);

CREATE TABLE variables (
  id INTEGER PRIMARY KEY, dataset_id INTEGER, name TEXT, label TEXT,
  type TEXT, fmt TEXT, missing_code TEXT,
  FOREIGN KEY(dataset_id) REFERENCES datasets(id)
);

CREATE TABLE rows (
  dataset_id INTEGER, row_idx INTEGER, payload_json TEXT,
  PRIMARY KEY (dataset_id, row_idx),
  FOREIGN KEY(dataset_id) REFERENCES datasets(id)
);

CREATE TABLE analyses (
  id INTEGER PRIMARY KEY, dataset_id INTEGER, spec_json TEXT, created_at TEXT
);

CREATE TABLE results (
  id INTEGER PRIMARY KEY, analysis_id INTEGER, kind TEXT,
  payload_json TEXT, svg BLOB, created_at TEXT
);
```

---
tkstatistics/
│
├── __main__.py
│   # CLI entry point: run headless analyses via JSON specs or launch the GUI.
│
├── app/                  # Tkinter GUI layer
│   ├── main.py            # Tk root window, menu bar, status bar.
│   ├── grid.py            # Data editor: Treeview + Entry overlay for spreadsheet-like editing.
│   ├── charts.py          # Drawing primitives for Canvas charts + SVG export.
│   ├── dialogs.py         # Tkinter dialogs/wizards for import, export, analyses.
│   ├── glossary.py        # Glossary/help texts for stats methods.
│   └── syntax_viewer.py   # Panel to show JSON specs and allow re-run.
│
├── core/                 # Core infrastructure
│   ├── project.py         # SQLite schema + load/save project logic.
│   ├── dataset.py         # In-memory tabular model (list[dict], dataclass rows).
│   ├── io_csv.py          # CSV/TSV import/export (sniffer, encodings).
│   ├── specs.py           # JSON spec recorder/replayer.
│   ├── logging_cfg.py     # Logging setup (rotating file logs).
│   ├── undo.py            # Undo/redo stack management.
│   └── utils.py           # Shared helpers (formatting, validation).
│
├── stats/                # Statistical computations (stdlib only)
│   ├── descriptives.py    # Mean, median, stdev, quantiles, frequency tables.
│   ├── nonparametric.py   # Sign, Wilcoxon, Mann–Whitney, Kruskal–Wallis, Fisher exact.
│   ├── parametric.py      # t-tests, ANOVA (small-sample).
│   ├── regression.py      # Simple/multiple OLS regression (tiny pure-Python solver).
│   ├── resample.py        # Bootstrap, permutation tests.
│   ├── timeseries.py      # Moving average, EWMA.
│   └── linalg_small.py    # Minimal linear algebra routines (matrix inversion, dot products).
│
├── tests/                # Unit tests (pytest)
│   ├── test_descriptives.py
│   ├── test_nonparametric.py
│   ├── test_parametric.py
│   ├── test_regression.py
│   ├── test_resample.py
│   ├── test_timeseries.py
│   ├── test_project.py
│   └── test_grid.py       # GUI smoke tests.
│
├── data/                 # Bundled resources
│   ├── samples/           # Example CSV datasets for demos/tutorials.
│   └── help/              # Glossary text, small-n critical value tables (JSON).
│
└── cli.py
    # Argparse-based CLI for headless operation:
    #   python -m tkstatistics run spec.json
