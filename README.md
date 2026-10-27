# Mineral Prospectivity: how much of a model's skill is spatial leakage?

Can stream-sediment chemistry distinguish areas containing known gold producers in
Nevada, and how much does the answer depend on the way the model is evaluated?

## What the analysis shows

Predictive performance drops when nearby locations are kept together during
validation. The model does not meet the useful-skill threshold set before fitting.
Its remaining signal reflects rock type, and differences between laboratory methods
and regions complicate transfer to new areas. This is a study of model evaluation;
it does not identify exploration targets.

The analysis combines geochemical feature preparation, spatial cross-validation,
and checks for laboratory effects using public USGS data.

[Read the report](reports/report.md) · [Five-minute walkthrough](docs/walkthrough.md) · [Reproduce the analysis](#setup)

![AUC and average precision against spatial block size](reports/figures/fig4_auc_vs_block_size.png)

Full report: [`reports/report.md`](reports/report.md). Pre-registration (frozen before any model was fitted): [`docs/prereg.md`](docs/prereg.md). Decisions: [`docs/decisions.md`](docs/decisions.md). Five-minute walkthrough: [`docs/walkthrough.md`](docs/walkthrough.md).

## Model performance

AUC measures how well a model ranks known-producer cells above other cells; a value
of 0.5 is chance ranking. Average precision also depends on how common the labelled
producer cells are. The ranges below describe repeated fold allocations.


| | Boosted trees | Logistic regression |
|---|---|---|
| AUC, random 5-fold (mean, min to max) | 0.638 (0.627 to 0.648) | 0.610 (0.606 to 0.615) |
| AUC, 100 km blocks | 0.571 (0.554 to 0.590) | 0.559 (0.541 to 0.583) |
| Average precision, random / blocks | 0.172 / 0.142 | 0.138 / 0.117 |
| Positives captured in top ten percent, random / blocks | 20.9% / 18.4% | 16.9% / 13.7% |
| Positives captured in top five percent, random / blocks | 11.8% / 10.6% | 8.6% / 6.6% |
| Leave-one-method-family-out AUC | 0.488 | 0.475 |
| Leave-one-quadrangle-out AUC (pooled) | 0.533 | 0.532 |

<details>
<summary>Interpretation and study population</summary>

The gradient boosted model's AUC is 0.638 under random 5-fold CV (range 0.627 to 0.648 over 5 repetitions) and 0.571 under 100 km spatial block CV (range 0.554 to 0.590), the block size the pre-registered autocorrelation rule selected. Average precision falls from 0.172 to 0.142 against a base rate of 9.7 percent. Under the frozen decision rule the leakage is "substantial" and at the reference block size the frozen label is "no demonstrated skill beyond chance once spatial structure is respected": the model fails the useful-skill threshold, not a statistical test of equality to chance. Leaving out an entire analytical laboratory family is worse still (AUC 0.488), and adding the family as a covariate raises random-CV AUC by 0.031: the model can learn the lab. The elements that carry what signal there is (V, Sc, Fe up; La, Ce, Th down) describe lithology, not ore.


Population: 5707 cells, 553 positive, from 13771 stream-sediment samples and 2850 producer sites. Moran's I of the label is 0.35 within 5 km and falls below 0.05 beyond 70 km.

</details>

## Setup

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/). The baseline harness
is cairn commit `a184e0732989373856039dea2919ccd96a88e8b1`. Install it in a
dedicated sibling without changing an existing cairn checkout:

```bash
python3 scripts/bootstrap.py
```

This stdlib helper clones the pinned SDK into its dedicated folder and runs
`uv sync --locked --group dev`. It refuses an existing checkout with a different
HEAD or any uncommitted changes, and never resets or checks out an existing
working tree. The project lockfile pins the remaining packages.

## Commands

Deterministic, no network, from the committed extract:

```bash
uv run cairn run               # scripts/10 .. 90 in order; rebuilds artifacts/numbers.json
uv run cairn render            # reports/report.md from report.tmpl.md and the ledger
uv run cairn verify            # all sensors, including the clean re-execution
uv run pytest                  # tests (log-ratio, blocks, label join, censoring, capture, synthetic leakage)
uv run python -m prospectivity.extract --check   # recompute the extract from the archives (needs data/archive/)
```

Network (only to re-download the archives; the extract is committed):

```bash
uv run python -m prospectivity.acquire           # downloads both archives to data/archive/, saves headers
uv run python -m prospectivity.acquire --verify  # SHA-256 against data/raw/manifest.json
```

## Data provenance

- NURE HSSR sediment database, whole-country CSV: https://mrdata.usgs.gov/nure/sediment/nuresed-csv.zip (public domain), retrieved 2026-10-09; 27630 Nevada sediment rows extracted from the full table. Metadata: `data/raw/nurehssr.met`.
- MRDS flattened CSV: https://mrdata.usgs.gov/mrds/mrds-csv.zip (public domain), retrieved 2026-10-09; 15408 Nevada rows. Metadata: `data/raw/mrds.met`.
- URLs, HTTP response headers, archive SHA-256, row counts and extract SHA-256: `data/raw/manifest.json`. The archives (about 65 MB) are not committed; the extract is written once by `prospectivity.extract` as verbatim text rows and never modified. Field definitions and quirks: `docs/data_dictionary.md`.

## What is not claimed

- No exploration recommendation. The held-out ranking at the reference block size does not meet the pre-registered skill rule, probabilities sit in a narrow band around the base rate, and the negatives are unlabelled cells, not known-barren ground.
- No pathfinder geochemistry. The ten-element suite common to the three analytical method families is lithological; As, Sb, Hg, W and Tl were not measured consistently and were excluded by the frozen rule.
- No separation of laboratory from region: the method families occupy different quadrangles, so the batch effect and the regional effect are confounded in these data.
- No confidence intervals: the reported spread is across repetitions of the fold allocation and block offset.

## How AI was used

This project was built in a Claude Code session with Claude Fable 5.1 from a written brief, under the cairn harness: the agent downloaded and profiled the data, chose the region after inspecting both candidates, wrote the pre-registration and froze it before fitting anything, wrote the pipeline, tests, figures and report, and ran `cairn verify` including the clean re-execution. The author reviewed the pre-registration, the tests and the findings. Every number in the report, this README and the walkthrough is a ledger value produced by a script; none was typed by hand.

## Layout

```
data/raw/            committed extract, metadata, manifest (frozen; never modified)
data/archive/        downloaded archives (gitignored)
data/derived/        sample, cell and prediction tables (regenerated; parquet gitignored)
src/prospectivity/   acquire, extract, prepare, features, labels, cv, models, util
scripts/             10 prepare, 20 features, 30 labels, 40 autocorrelation, 50 cv,
                     60 batch checks and exploratory, 70 interpret, 80 figures, 90 render docs
artifacts/           numbers.json (ledger), checks.jsonl
reports/             report.md (rendered), figures/, tables/
profiles/            cairn profile output for the two extracts
docs/                prereg.md (frozen), decisions.md, data_dictionary.md, walkthrough.md,
                     resume_bullet.md, cairn_trap_task.md
tests/               pytest suite
```


The frozen skill label is an operational decision rule, not a statistical test that AUC equals 0.5. The reference model does not meet the pre-registered useful-skill threshold. Family indicators are learnable proxies for both method and region; this dataset cannot isolate a causal laboratory effect. See [the supplementary distance-buffer sensitivity](docs/buffered-validation.md) for a stricter exploratory separation check.

_Rendered from `README.tmpl.md` by `scripts/90_render_docs.py`; every number is a ledger value. Edit the template, not this file._
