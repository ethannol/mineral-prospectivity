# Recorded exploratory buffered validation

Matched block allocations, baseline grids, and distance exclusion in both inner and outer folds.

| Model | Buffer (km) | Mean AUC | Repetition range | Mean removed training cells per fold |
| --- | --- | --- | --- | --- |
| hgb | 0 | 0.577 | 0.559 to 0.590 | 0.0 |
| hgb | 5 | 0.574 | 0.563 to 0.584 | 141.5 |
| hgb | 10 | 0.571 | 0.568 to 0.578 | 329.9 |
| hgb | 25 | 0.559 | 0.549 to 0.565 | 971.1 |
| lr | 0 | 0.568 | 0.547 to 0.583 | 0.0 |
| lr | 5 | 0.565 | 0.544 to 0.579 | 141.5 |
| lr | 10 | 0.564 | 0.547 to 0.573 | 329.9 |
| lr | 25 | 0.551 | 0.534 to 0.561 | 971.1 |

The range is variation across matched repetition allocations, not a confidence interval. Distance exclusion also reduces training support, so differences cannot be attributed to leakage alone.

This exploratory sensitivity preserves the frozen primary metrics and decision rule. The zero-buffer comparator uses fewer repetitions than the original baseline and should be compared within this matched suite.

Recorded source `183fc248b69af0ae37cf3dc1822313073b8bc857`, seeds from repetition index. [Methods](buffered-validation.md), [metrics](../reports/exploratory/buffered_cv/metrics.csv), [fold attrition and minimum separation](../reports/exploratory/buffered_cv/folds.csv), [cell predictions](../reports/exploratory/buffered_cv/predictions.csv).
