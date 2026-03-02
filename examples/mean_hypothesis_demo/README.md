# Mean Hypothesis Demo

This example includes a tiny dataset and a runnable analysis spec.

- `dataset.csv` has 5 rows and 1 numeric variable (`score`).
- `spec.describe.json` runs `describe` on that variable.

The hypothesis context is included in the spec metadata as an example of a confirmatory plan:

- Null: mean(score) = 10
- Alternative: mean(score) != 10

Note: a one-sample mean hypothesis test is not implemented yet in `tkstatistics`, so this example uses `describe` as the current runnable placeholder.

## Run

Run the included script from repo root:

```bash
bash examples/mean_hypothesis_demo/run_demo.sh
```

The script creates `examples/mean_hypothesis_demo/demo.statproj`, imports the CSV as dataset `mean_test_demo`, then runs the spec.
