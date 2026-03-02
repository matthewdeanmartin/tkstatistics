# Mean Hypothesis Demo

This example includes a tiny dataset and a runnable hypothesis-test spec.

- `dataset.csv` has 5 rows and 1 numeric variable (`score`).
- `spec.describe.json` runs `ttest_1samp` on that variable.

The confirmatory hypothesis in the spec is:

- Null: mean(score) = 10
- Alternative: mean(score) != 10

## Run

Run the included script from repo root:

```bash
bash examples/mean_hypothesis_demo/run_demo.sh
```

The script creates `examples/mean_hypothesis_demo/demo.statproj`, imports the CSV as dataset `mean_test_demo`, then runs the spec.
