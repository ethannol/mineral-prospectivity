# How much of a prospectivity model's skill is spatial leakage?

_Rendered by `cairn render`; every figure below is a ledger value produced by a script under `scripts/`. Do not edit `reports/report.md`._

## Question

Given NURE stream-sediment geochemistry over Nevada aggregated to 5 km grid cells, how well can cells containing a known gold producer (an MRDS site with development status Producer or Past Producer and gold as a primary commodity) be distinguished from the other sampled cells, and how much of the apparent skill under random k-fold cross-validation disappears under spatial block cross-validation at block sizes above the autocorrelation range of the target?

**Answer.** Under random 5-fold cross-validation the gradient boosted model reaches an AUC of 0.638 (standard deviation 0.008, range 0.627 to 0.648 over 5 repetitions). Under spatial block cross-validation with 100 km blocks, the reference size fixed by the pre-registered autocorrelation rule, the same model reaches 0.571 (standard deviation 0.015, range 0.554 to 0.590). The drop of 0.068 is "substantial" by the frozen decision rule, and the block-CV result falls under the frozen rule's reading "no demonstrated skill beyond chance once spatial structure is respected". Only 51 percent of the random-CV skill above chance survives. The logistic regression behaves the same way (0.610 random, 0.559 at 100 km, drop 0.051, "substantial"). The leave-one-analytical-family-out check is worse still (pooled AUC 0.488 for the boosted model), so part of what the random-CV model learns is the laboratory, not the geology.

## Data and comparability

- **NURE sediment extract** (`data/raw/nure_nv_sediment.csv`): 27630 Nevada sediment records across 18 one-by-two-degree quadrangles. One row is one analytical record of one sample. Population filters in order: stream sediment only (10112 soil, playa, lake and other records excluded), missing coordinates (5), no analyses in the record (520), additional records of the same sample (1247; the lowest record number is kept), leaving 15746 stream-sediment samples. The analytical method family (LL 6785, SR 4425, OR 4536 samples) is the batch variable: Savannah River samples were analysed either by its own neutron-activation methods or by Oak Ridge methods, with different element suites, so the DOE laboratory is not the right grouping.
- **Element suite.** The pre-registered rule (non-null in at least 75 percent of records and censored in at most 25 percent of non-null records in every family) selects exactly the ten pre-registered elements (Al, Ce, Fe, La, Mn, Na, Sc, Th, Ti, V; rule matches the pre-registration: True). Complete-case on the suite excludes 1975 samples, leaving 13771 (LL 6485, SR 2750, OR 4536), collected 1976/05/03 to 1980/09/02. This is a lithological suite: the classic Nevada gold pathfinders (As, Sb, Hg, W, Tl) are absent or heavily censored in at least one family and could not be used. That limitation applies to every result below.
- **Censoring.** NURE reports a value below the detection limit as a negative number whose magnitude is the limit. Across the ten elements and 13771 samples 3.61 percent of values are censored; the worst case is Ti in the LL family at 20.9 percent (`fig2_censoring.png` and `reports/tables/censored_fraction_suite.csv`). Censored values are substituted by 0.5 times the limit for the log-ratio transform; this is a labelled substitution, not an estimate, and the per-element shares are reported so a reader can judge it. No zero values occur in the suite (0), and nothing is filled with zero.
- **MRDS extract** (`data/raw/mrds_nv.csv`): 15408 Nevada site records, none without coordinates. 2850 are positive sites (2506 past producers, 344 producers), at 2643 distinct coordinates, so duplicate records exist and are absorbed by the cell-level join. 4937 further sites mention gold at some rank or status (prospects, occurrences, by-product gold) and define the ambiguous cells.
- **Units.** 6378 cells of 5 km on UTM zone 11N (EPSG 32611) hold at least one retained sample (median 2 samples per cell, maximum 13; 38 percent of cells hold a single sample). A cell's features are the mean of its samples' centred log-ratio vectors. 671 ambiguous cells are excluded from the confirmatory population, leaving 5707 cells with 553 positives (base rate 9.69 percent). Only 66 percent of positive sites fall in a cell that has any retained sample; the rest cannot be scored and are not in the population. The deposit-to-cell join is a per-cell count merged one-to-one; the row count is unchanged and a planted duplicate of every positive site leaves the labels unchanged (True). Negatives are unlabelled cells, not known-barren ground.

## Method

Everything in this section was frozen in `docs/prereg.md` before any model was fitted. Two models: an L2 logistic regression on isometric log-ratio coordinates (C chosen from a four-value grid) and a `HistGradientBoostingClassifier` on centred log-ratios (four-entry grid over learning rate and leaf count, fixed iteration budget). Selection uses an inner 3-fold split of the training folds under the same grouping scheme as the outer split; standardisation is fitted on training folds only. Schemes: random stratified 5-fold (5 repetitions); square spatial blocks of 5, 10, 25, 50, 100 km with a random grid offset and random block-to-fold allocation (5 repetitions per size); leave-one-method-family-out; leave-one-quadrangle-out. Metrics are computed on the pooled out-of-fold predictions of each repetition, so the spread is across repetitions. The whole protocol runs in a few minutes on one thread.

## Results

### Spatial autocorrelation sets the reference block size

Moran's I of the cell label is 0.35 for cell pairs within 5 km, 0.22 in the next 5 km bin, and first falls below 0.05 at 70 km (`fig3_moran.png`; null expectation -0.0002). By the pre-registered rule the reference block size is the smallest size in the grid at or above that distance: 100 km. Known gold producers in Nevada cluster in districts tens of kilometres across; a random split puts cells from the same district on both sides of the split.

### Headline: random versus spatial cross-validation (`fig4_auc_vs_block_size.png`)

| Model | Scheme | AUC mean | sd | min | max | AP mean | AP min | AP max |
|---|---|---|---|---|---|---|---|---|
| Boosted trees | random 5-fold | 0.638 | 0.008 | 0.627 | 0.648 | 0.172 | 0.167 | 0.182 |
| Boosted trees | blocks, five km (5707 blocks, one cell each) | 0.643 | 0.005 | 0.638 | 0.649 | 0.176 | 0.169 | 0.185 |
| Boosted trees | blocks, ten km (2234 blocks) | 0.633 | 0.009 | 0.621 | 0.641 | 0.172 | 0.169 | 0.177 |
| Boosted trees | blocks, twenty-five km (453 blocks) | 0.613 | 0.009 | 0.600 | 0.624 | 0.158 | 0.148 | 0.169 |
| Boosted trees | blocks, fifty km (131 blocks) | 0.605 | 0.005 | 0.598 | 0.611 | 0.156 | 0.151 | 0.158 |
| Boosted trees | blocks, one hundred km (42 blocks, reference) | 0.571 | 0.015 | 0.554 | 0.590 | 0.142 | 0.126 | 0.152 |
| Logistic (ILR) | random 5-fold | 0.610 | 0.004 | 0.606 | 0.615 | 0.138 | 0.135 | 0.140 |
| Logistic (ILR) | blocks, ten km | 0.610 | 0.005 | 0.602 | 0.615 | 0.138 | 0.136 | 0.142 |
| Logistic (ILR) | blocks, twenty-five km | 0.601 | 0.006 | 0.596 | 0.612 | 0.133 | 0.130 | 0.139 |
| Logistic (ILR) | blocks, fifty km | 0.590 | 0.012 | 0.577 | 0.608 | 0.129 | 0.125 | 0.136 |
| Logistic (ILR) | blocks, one hundred km (reference) | 0.559 | 0.018 | 0.541 | 0.583 | 0.117 | 0.109 | 0.128 |

The base rate, and so the average precision of a random ranking, is 9.69 percent. The AUC falls monotonically with block size from ten km upward for both models. The five-km rows are a check, not a result: 5 km blocks coincide with single cells, so block-5 CV is random CV without stratification. The random-CV and reference block-CV ranges do not overlap for either model (boosted: False; logistic: False). Average precision drops by 0.031 (boosted) and 0.021 (logistic).

Caveat attached to this claim: the spread shown is across repetitions of the fold allocation and grid offset, which is the right spread for "how stable is this estimate under the protocol" but is not a confidence interval for the population AUC, and at 100 km the folds hold only 42 blocks, so the block-CV spread is wider for structural reasons.

### Capture and calibration (`fig5_capture.png`, `fig6_calibration.png`)

Under random CV the boosted model's top ten percent of cells capture 20.9% of held-out producer cells (range 19.5% to 22.6%), a lift of 2.09 over chance; the top five percent capture 11.8% and the top twenty percent 36.6%. At the reference block size the top ten percent capture 18.4% (range 16.1% to 19.7%; lift 1.84), the top five percent 10.6%, the top one percent 2.6% and the top twenty percent 31.4%. A geologist reading `fig5_capture.png` sees a curve that sits above the diagonal but not far above it: following the model's top decile would roughly double the hit rate of a random walk across sampled cells under random CV, and somewhat less than that once the model is asked about districts it has not seen.

Calibration: held-out probabilities span a narrow band (random CV decile means from 2.5 to 26.5 percent; block CV from 3.6 to 25.9 percent). In the top decile the observed producer rate is 21.9 percent under random CV against a mean prediction of 26.5 percent, and 17.2 percent against 25.9 percent under block CV; Brier scores are 0.0857 and 0.0878. Caveat attached: because negatives are unlabelled, the observed rates are lower bounds on the true rate of mineralised ground, and so is every precision figure here.

### Batch effects: the second leakage trap

Leave-one-method-family-out, which asks the model to score samples from an analytical family it never saw, gives a pooled AUC of 0.488 (boosted) and 0.475 (logistic); the difference from the reference block-CV value (leave-one-family-out minus block CV) is -0.082 and -0.084. Within each held-out family the ranking is slightly better than chance (boosted: LL 0.542, SR 0.551, OR 0.545); the pooled value is lower because the families' score distributions are offset, which is what a laboratory effect looks like. Leave-one-quadrangle-out over 17 quadrangles gives pooled AUC 0.533 (boosted) and 0.532 (logistic); among the 13 quadrangles with at least 10 cells of each class the per-quadrangle AUC runs from 0.370 to 0.595 (median 0.536) for the boosted model, with 4 quadrangles below one half. The frozen batch-trap rule (gain of at least two hundredths of AUC from adding the family, or a leave-one-family-out AUC at least five hundredths below block CV) is met for both models: boosted True, logistic True.

### Decision rule outcomes (pre-registered)

- Leakage: **substantial** for the boosted model (drop 0.068), **substantial** for the logistic regression (drop 0.051).
- Skill under spatial CV at the reference size: **no demonstrated skill beyond chance once spatial structure is respected** (boosted, mean 0.571, minimum 0.554; the rule required a mean of at least six tenths and a minimum above fifty-five hundredths). The largest block size at which the rule is still met is 50 km for the boosted model and 25 km for the logistic regression, which is where this geochemistry stops generalising.
- Batch trap: **present** for both models.
- Abstention thresholds were not triggered (False).

## Exploratory findings (not pre-registered)

### Which elements carry the signal, and are they pathfinders?

Table `reports/tables/element_signal.csv`. In a logistic fit on all cells (C = 1), the largest positive centred-log-ratio coefficients belong to Sc, V, Th (largest Sc, 0.53) and the most negative to La, Mn, Fe (most negative La, -0.42). The simple class contrast agrees: relative to the other cells, producer cells are enriched in V, Sc, Fe (largest standardised difference 0.27) and depleted in La, Ce, Th (most negative -0.21). Held-out permutation importance for the boosted model (block CV at the reference size, selected configuration: learning rate 0.1, 7 leaves) is small for every element: the top three are La, Ti, Na, with the leading element worth 0.032 AUC and the third 0.007.

Interpretation: a signature of more Sc, V and Fe and less La, Ce and Th is a mafic-to-intermediate versus felsic lithology contrast, not a hydrothermal one. It is consistent with many Nevada producers sitting in andesitic volcanic terrain (Walker Lane epithermal districts) rather than in rhyolite- or granite-dominated catchments, and it says nothing about the ore itself. None of these ten elements is a gold pathfinder; the elements that are (As, Sb, Hg, W, Tl) were not measured consistently across the analytical families and were excluded by the pre-registered rule. The honest reading is that this model learns regional lithology, and lithology is spatially smooth, which is exactly why random CV overstates it.

### The laboratory as a feature

Adding the three method-family indicators as covariates raises random-CV AUC from 0.638 to 0.669 for the boosted model (gain 0.031) and from 0.610 to 0.642 for the logistic regression (gain 0.032). At the reference block size the lab-covariate models score 0.596 and 0.595. The family indicator is a cheap proxy for region (each family covers a contiguous set of quadrangles) and for the family's own base rate (LL 13.4, SR 7.8, OR 6.5 percent of cells positive). A model that is allowed to see the lab learns the lab; a casual analyst who one-hot-encodes "laboratory" as a nuisance covariate and validates with random folds would report a better model that generalises worse.

### Sensitivity: ambiguous cells kept as negatives

Keeping the 671 ambiguous cells (gold prospects, occurrences and by-product producers) as negatives (6378 cells, base rate 8.67 percent) lowers the boosted model's AUC to 0.621 under random CV and 0.551 at the reference block size: the conclusion does not depend on the exclusion.

### Residual autocorrelation

Moran's I of the random-CV residuals is 0.30 in the first distance bin and 0.17 in the second, compared with 0.35 and 0.22 for the label (`fig3_moran.png`): the features explain little of the spatial structure of the target, which is what the block-CV result says in another way.

## What this model would and would not be useful for

It would be useful as a demonstration of why spatial block cross-validation is mandatory for prospectivity work, as a baseline against which a pathfinder-bearing dataset can be judged, and as a map of regional lithological contrast. It would not be useful as an exploration ranking: at the reference block size its ranking is within reach of chance on the pre-registered rule, its probabilities sit in a narrow band around the base rate, the negatives are unlabelled, and 66 percent coverage of positive sites by sampled cells means a third of known producers are outside the population altogether. This report is not an exploration recommendation.

## Caveats next to the claims they affect

- Element suite (every result): no gold pathfinder elements; the NURE program's labs measured different suites, and the cross-family common set is lithological.
- Units (every result): 38 percent of cells hold one sample, so cell features are noisy; NURE coordinates are NAD27 and MRDS WGS84, with the shift below the cell size and ignored.
- Labels (precision, calibration): positive-unlabelled; MRDS has duplicate and near-duplicate sites and its coordinates vary in precision; systematic MRDS updates stopped in 2011.
- Spread (headline): across repetitions of the protocol, not a confidence interval; the reference block size is set by one correlogram threshold chosen before modelling.
- Batch check: the three families also differ in region and in sieve fraction, so "the lab" cannot be separated from "the region" with these data.

## Figures

1. `reports/figures/fig1_coverage.png`: retained samples by method family and gold producers.
2. `reports/figures/fig2_censoring.png`: share below detection limit by element and family.
3. `reports/figures/fig3_moran.png`: Moran's I correlogram of the label and of the residuals.
4. `reports/figures/fig4_auc_vs_block_size.png`: the headline, AUC and average precision against block size with the random-CV reference.
5. `reports/figures/fig5_capture.png`: capture curves, random versus block CV.
6. `reports/figures/fig6_calibration.png`: reliability of held-out predictions.
7. `reports/figures/fig7_prospectivity_map.png`: held-out predictions with known producers overlaid.

## Decision log

See `docs/decisions.md` for every data and modelling decision, including the post-freeze exploratory additions.
