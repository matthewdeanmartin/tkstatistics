# TODO

## Bugs

- Keeps rerunning a task. Doesn't save last results
- Keeps adding duplicates to analysis history

## New directions

- Auto select univariate if only 1
- Only show numbers?
- Don't do modal alerts on errors. It isn't 1995.
- kernel density function for monte carlo univariate statistics


## Performance

- What tool to test?
- What technique to make faster?
  - serialization/deserialization in db. Should treat univariate/bivariate data separately

## Config

- toml/.ini
- some sort of way to 
  - pick stdlib vs own algo
  - sqlite for math
  - 