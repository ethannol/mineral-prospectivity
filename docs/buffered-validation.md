# Exploratory distance-buffer validation

The frozen block-CV results and preregistration remain unchanged. Different blocks can touch, so they do not guarantee distance between training and test cells.

Run on the analysis machine:

```sh
uv run python exploratory/prepare_inputs.py
uv run python exploratory/buffered_cv.py --reps 3 --buffers-km 0 5 10 25
```

This uses the baseline 100 km block allocation and both baseline model grids. Each outer training set excludes centres within the chosen radius of held-out centres. Inner tuning uses the same exclusion rule, training data only. The zero-buffer arm supplies a matched comparison; reduced training support is reported per fold. All cells retain held-out predictions. Folds with no valid inner selection cause an explicit failure rather than an arbitrary model fallback.

Outputs live separately in `reports/exploratory/buffered_cv/`: per-fold training attrition, cell predictions, repetition-level metrics, and source-revision metadata. Buffer sizes and three repetitions are exploratory choices, not a replacement decision rule or confidence interval. Interpretation must consider loss of training support as well as leakage.

[Recorded supplementary results](buffered-results.md). Regenerate its table with `uv run python exploratory/render_buffered.py`; no models are fitted by that command.

Preparation always overrides `CAIRN_LEDGER` and `CAIRN_CHECKS` into `reports/exploratory/preparation/`, even if the caller environment points at primary artifacts. Do not call the numbered preparation scripts directly for this sensitivity.
