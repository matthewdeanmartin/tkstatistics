# tkstatistics

`tkstatistics` is a small-data statistics desktop application and headless
runner built with the Python standard library. Its defining workflow is
pre-registration: a confirmatory analysis must match a committed hypothesis
plan before the application reveals its p-value.

The project is alpha software intended for teaching and reproducible analysis
on modest datasets. It is not a replacement for NumPy, SciPy, pandas, R, or a
validated clinical statistics system.

## Features

- Tkinter desktop application with CSV import and SQLite project files.
- Reproducible JSON analysis specifications and persisted run artifacts.
- Committed analysis plans, confirmatory-result gating, and dataset audit
  reports.
- Descriptives, frequency tables, t-tests, nonparametric tests, Fisher's exact
  test, ANOVA, correlations, and linear regression.
- Histogram, box plot, scatter plot, and normal Q-Q plot rendering with SVG
  export.
- No third-party runtime dependencies. Numerical routines are cross-checked
  against established scientific Python libraries in the test suite.

## Installation

Python 3.11 or newer is required.

```console
python -m pip install tkstatistics
```

Tkinter is included with standard Python installers on Windows and macOS. Some
Linux distributions package it separately, for example as `python3-tk`.

## Desktop usage

Launch the application with either command:

```console
tkstatistics
python -m tkstatistics
```

Create or open a `.statproj` project, import a CSV dataset, then use the
**Analyze** and **Graphs** menus. Confirmatory analyses follow a two-step flow:
first choose **Pre-register Hypothesis...**, then **Run Confirmatory Test...**.

## Headless usage

Run a JSON specification against an existing project:

```console
tkstatistics --run analysis.json --project study.statproj --format text
```

Machine-readable output is the default and can also be saved to a file:

```console
tkstatistics --run analysis.json --project study.statproj \
  --format json --output run-artifact.json
```

Pre-registration and auditing are available without the GUI:

```console
tkstatistics --commit-plan plan.json --project study.statproj
tkstatistics --audit dataset_name --project study.statproj
```

See `tkstatistics --help` and the
[`examples/mean_hypothesis_demo`](https://github.com/matthewdeanmartin/tkstatistics/tree/main/examples/mean_hypothesis_demo)
walkthrough.

## Development

```console
uv sync --all-extras --all-groups
make check-ci
make publish-check
```

The package is MIT licensed. See the
[release history](https://github.com/matthewdeanmartin/tkstatistics/blob/main/CHANGELOG.md).
