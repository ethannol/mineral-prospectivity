# Note: this study as a cairn trap task (a spatial-leakage sensor)

Not built. This describes how the project could become `t7_spatial_leak` in
cairn's eval suite, which currently has six synthetic trap tasks (join fan-out,
filtered denominator, target leak, time leak, censored units, null-effect framing).

## The failure mode

An agent asked to "fit a model that predicts mineralised cells from geochemistry
and report its held-out AUC" reaches for `StratifiedKFold` or `train_test_split`,
fits a tree ensemble, and reports an AUC well above one half. Both the features and
the target are spatially autocorrelated, so random folds let the model match each
test cell to its neighbours in training. The reported number is real in the sense
that the code ran, and wrong in the sense that it does not transfer to new ground.
Practitioners in prospectivity, species distribution modelling and soil mapping
report this failure constantly; the published benchmarks do not measure it.

## The synthetic task

Generate a square of cells (say two hundred by two hundred) with coordinates. Draw
three features as Gaussian random fields with a correlation range of about ten
cells. Draw the target as an independent Gaussian random field with the same range,
thresholded at its top twenty percent. The features have no relationship to the
target except that both are smooth in space. Optionally add one weakly predictive
feature so the honest answer is "small but non-zero skill" rather than "none",
which makes the grader harder to satisfy by always answering zero.

- Prompt: "Using `cells.csv` (x, y, f1, f2, f3, target), fit a classifier and
  report its held-out AUC with a spread."
- Gold answer: block cross-validation at a block size above the range (or
  buffered leave-one-out) gives AUC within a stated tolerance of one half (or of
  the planted weak signal's true AUC, computed on a fresh independent draw).
- Trap answer: random k-fold AUC above six tenths.
- Grader: parse the reported AUC and the described split; pass if the AUC is within
  tolerance of the truth and the split is spatial; fail if the AUC exceeds the trap
  threshold. The test suite proves the grader passes the gold answer and fails the
  trap answer, as the other six tasks do.

`tests/test_cv.py::test_synthetic_leakage_random_cv_shows_skill_block_cv_does_not`
in this project is the kernel of this generator and already demonstrates the
separation with the project's own block-CV code.

## The sensor

Two deterministic additions would make the harness catch this without a grader:

1. `cairn.spatial_split_check(train, test, x="x", y="y", range_m=...)`: for each
   test unit, the distance to the nearest training unit; fails (or warns) if the
   median is below the stated range, and records the distribution in
   `checks.jsonl`. The range can come from a `cairn.autocorrelation_range(df, x,
   y, target)` helper that returns the first lag at which Moran's I falls below a
   threshold, the rule this project pre-registered.
2. A script lint: `StratifiedKFold`, `KFold`, `train_test_split` or
   `cross_val_score` on a frame that has columns named like coordinates
   (`x`, `y`, `lat`, `lon`, `latitude`, `longitude`, `easting`, `northing`)
   without a `GroupKFold`, a block id, or a `spatial_split_check` call in the
   same script. Same shape as the existing C301 time-split warning.

The analysis-workflow skill would gain one line under "Leakage": "If rows have
coordinates, split by spatial block above the autocorrelation range and run
`cairn.spatial_split_check`."
