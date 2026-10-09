# Pre-registration

Written before computing any result. Frozen by `cairn freeze`; a changed hash
fails verification. Anything not described here is exploratory and must be
labelled as such in the report.

## Question

Given NURE stream-sediment geochemistry over Nevada aggregated to 5 km grid cells,
how well can cells containing a known gold producer (MRDS development status
Producer or Past Producer with gold as a primary commodity) be distinguished from
the other sampled cells, and how much of the apparent skill under random k-fold
cross-validation disappears under spatial block cross-validation at block sizes
above the spatial autocorrelation range of the target?

## Primary quantity

For each of the two models (L2 logistic regression; HistGradientBoostingClassifier):

1. AUC under random stratified 5-fold cross-validation, as the mean over 5
   repetitions with the standard deviation and the min-max range.
2. AUC under spatial block cross-validation at the reference block size, as the mean
   over 5 repetitions (new random block-grid offset and new random block-to-fold
   allocation each time) with the standard deviation and the min-max range.
3. The leakage inflation: (1) minus (2).

The same three quantities are reported for average precision. Secondary
quantities: the full AUC and average-precision curves against block size (5, 10,
25, 50, 100 km); capture of held-out positives in the top 1, 5, 10 and 20 percent
of cells ranked by predicted probability; calibration (reliability in 10
quantile bins and the Brier score) of the pooled out-of-fold predictions;
leave-one-method-family-out and leave-one-quadrangle-out AUC.

Reference block size: the smallest block size in {5, 10, 25, 50, 100} km that is at
or above the distance at which Moran's I of the cell label (correlogram in 5 km
distance bins from 0 to 150 km, computed on cell centroids before any model is
fitted) first falls below 0.05. If Moran's I does not fall below 0.05 within 100
km, the reference block size is 100 km. The headline model is the gradient boosted
tree; the logistic regression is reported alongside it.

## Unit of analysis

The unit is a 5 km by 5 km grid cell in UTM zone 11N (EPSG:32611). Both datasets
are projected as WGS84 (the NAD27 to WGS84 shift in Nevada is on the order of 100
m, far below the cell size). A cell's feature vector is the mean of the per-sample
centred log-ratio vectors of the stream-sediment samples that fall in it, which
equals the centred log-ratio of the geometric-mean composition of the cell. One row
per cell; repeated samples at one site or in one cell are averaged, so within-cell
pseudo-replication is removed, and cells (grouped into blocks) are the units that
are split by cross-validation. Cells with no retained sample are not in the
population because they cannot be scored.

## Population and comparability

NURE records (`data/raw/nure_nv_sediment.csv`, Nevada sediment extract):

- Keep `sampsrc == STREAM` (stream sediment). Exclude soil, playa, lake and other
  sources.
- Exclude records with missing coordinates and records with `methods == NONE`
  (no analyses).
- Collapse multiple records per sample (`doelab`, `prime_id`) to the record with the
  lowest `rec_no`.
- Analytical method family from the first method code: LL (Livermore), SR (Savannah
  River), OR (Oak Ridge methods on SRL-W samples). The family is the batch variable.
- Element suite, fixed by the rule "non-null in at least 75% of records and censored
  in at most 25% of non-null records in every family": Al (pct), Fe (pct), Mn, Na
  (pct), Sc, Th, V, Ce, La, Ti (ppm). Records missing any suite element are
  excluded (complete-case on the ten elements); the count is recorded. Percent
  fields are converted to ppm (times 10,000) before closure.
- Every exclusion is logged with its reason and count in
  `data/derived/exclusion_log.csv`.

MRDS records (`data/raw/mrds_nv.csv`, Nevada extract):

- Positive site: `dev_stat` in {Producer, Past Producer} and the whole word "Gold"
  in `commod1` (primary commodity list). Sites with missing coordinates are
  excluded.
- Ambiguous site: any other site that mentions gold in `commod1`, `commod2` or
  `commod3` (prospects, occurrences, unknown status, plants, and producers with gold
  only as a secondary or tertiary commodity).
- Positive cell: contains at least one positive site. Ambiguous cell: no positive
  site and at least one ambiguous site; excluded from the confirmatory population.
  Negative cell: every other sampled cell. Negatives are unlabelled, not known
  barren: a negative cell may contain undiscovered or unrecorded mineralisation, so
  precision, average precision and calibrated probabilities are lower bounds on the
  true values and the problem is positive-unlabelled learning, not supervised
  classification with verified negatives.
- The deposit-to-cell join is a per-cell count of positive and ambiguous sites
  merged 1:1 onto the cell table with `cairn.checked_merge`; the cell count must not
  change. Duplicate MRDS records in one cell cannot create two positives.

## Handling of missing and censored values

- A negative element value is a censored value below the detection limit whose
  absolute value is the detection limit (NURE metadata). For the log-ratio
  transform censored values are substituted by half the detection limit. This is a
  labelled substitution; the censored fraction of each suite element in each
  method family is recorded and shown in the report, and the suite rule above
  already excludes any element censored in more than 25% of a family's records.
- Null element values are not filled. A record missing any suite element is
  excluded and counted.
- Zero element values are treated as missing (none are expected in the suite).
- Log-ratio transform: closure of the ten-element subcomposition, centred log-ratio
  (CLR) for the tree model and for interpretation; isometric log-ratio (ILR,
  orthonormal Helmert basis) for the logistic regression, with coefficients mapped
  back to CLR space for interpretation. Standardisation of ILR coordinates is fitted
  on the training folds only.

## Models and cross-validation protocol

- Logistic regression: L2 penalty, `C` chosen from {0.01, 0.1, 1, 10} by an inner
  3-fold cross-validation on the training folds using the same grouping scheme as
  the outer split (random strata or spatial blocks), maximising AUC.
- Gradient boosted trees: `HistGradientBoostingClassifier`, `max_iter` 100, early
  stopping off, `min_samples_leaf` 20, `l2_regularization` 1.0, fixed random state;
  (`learning_rate`, `max_leaf_nodes`) chosen from {0.05, 0.1} x {7, 15} by the same
  inner 3-fold scheme. No other tuning. No class weighting (the metrics are ranking
  metrics).
- Scheme 1, random: stratified 5-fold, 5 repetitions with seeds 0 to 4.
- Scheme 2, spatial blocks: square blocks of 5, 10, 25, 50 and 100 km on the UTM
  grid with a random offset uniform in [0, block size) in x and y; blocks are
  allocated to 5 folds by a random permutation dealt round-robin; 5 repetitions per
  block size (seeds 0 to 4 give the offset and the permutation).
- Scheme 3, batch check: leave-one-method-family-out (3 folds) and
  leave-one-quadrangle-out (one fold per quadrangle that has at least one
  positive and one negative cell).
- Within every outer fold the inner model selection, the standardisation and the
  fit use training cells only. `cairn.split_overlap` is run on every outer split.
- Metrics are computed on the pooled out-of-fold predictions of each repetition
  (every cell is scored exactly once per repetition); the spread is across
  repetitions. Spatial autocorrelation of the label is measured before modelling
  with a Moran's I correlogram on cell centroids (5 km bins to 150 km).

## Decision rule

With A_r the mean random-CV AUC and A_b the mean block-CV AUC at the reference block
size for the gradient boosted model:

- Leakage is "substantial" if A_r - A_b >= 0.05 and the min-max ranges of the two
  schemes do not overlap; "small" if A_r - A_b < 0.02; "moderate" otherwise.
- The model "has skill beyond the base rate under spatial cross-validation" if A_b
  >= 0.60 and the minimum block-CV AUC over the 5 repetitions is above 0.55;
  otherwise the conclusion is "no demonstrated skill beyond chance once spatial
  structure is respected".
- The batch trap is "present" if the exploratory model with the method-family
  indicator added gains at least 0.02 random-CV AUC over the confirmatory model, or
  the leave-one-method-family-out AUC is below the block-CV AUC at the reference
  size by 0.05 or more.
- Abstain from the headline comparison if fewer than 150 positive cells or fewer
  than 1,000 cells remain after exclusions, or if any method family contributes
  fewer than 10 positive cells (the batch check would then be uninterpretable). The
  report would then stop at the descriptive statistics and the reason.
- The result is reported whichever way it falls; a small leakage effect or a model
  with no skill are both valid findings.

## Confirmatory vs exploratory

Confirmatory: everything above, for both models: the random-versus-block AUC and
average-precision comparison with spread, the AUC-against-block-size curve, capture
at the four thresholds, calibration, the Moran's I correlogram of the label, and the
two batch checks.

Exploratory (labelled as such in the report): the model with the method-family
indicator added as a covariate (the lab trap); the sensitivity analysis that keeps
ambiguous cells as negatives; the correlogram of random-CV residuals; permutation
importance and coefficient interpretation of which elements carry the signal; the
prospectivity map of held-out predictions; any model, feature or threshold not
listed above.
