# tkstatistics

Statistical package that uses only python's standard library.

- GUI
- Surface anything in the `statistics`, `random` and `math` packages related to statistics.
- Small data statistics (nonparametric methods, nonnormality, etc)

## Installation

Doesn't have to run in a virtual environment because doesn't depend on any libraries.

`pip install tkstatistics`

## Usage

Run app.

Load datasets.

- TODO: persist dataset to Sqlite

Datasets are used by analysis, represented by a spec.

- TODO: save analysis files to a folder to make an analysis repeatable

A run is saved in memory.

- TODO: allow export of everything, data, spec, output, etc as a repeatable science feature.

## Output

Not Implement, but on the road map

- Text output
- LaxTeX output
- SVG chart

## Design goals

- Use only the standard library. So it will never be as good or performant as numpy, pandas and so on
- Target canned, small data statistics. Won't involve infinite programmability like R.
- Match results of other 3rd party libraries because I don't actually have a Ph D in stats, but I can use LLM and hack
  until the code matches other 3rd party libraries
