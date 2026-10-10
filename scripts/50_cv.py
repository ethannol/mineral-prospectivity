"""Step 50: both models under random and spatial block cross-validation.

Pre-registered protocol: random stratified 5-fold (5 repetitions) and square
blocks of 5, 10, 25, 50, 100 km (5 repetitions each: new offset and new
block-to-fold allocation). Inner 3-fold selection on training folds only,
same grouping scheme. Metrics on pooled out-of-fold predictions per repetition.

Writes artifacts/tables/cv_metrics.csv (one row per model x scheme x rep),
artifacts/tables/cv_summary.csv and data/derived/oof_predictions.parquet.
"""

import os
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")  # deterministic histogram boosting

from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from cairn import record, split_overlap  # noqa: E402

from prospectivity.cv import (  # noqa: E402
    BLOCK_SIZES_KM,
    block_folds,
    check_folds,
    evaluate,
    inner_folds,
    random_folds,
)
from prospectivity.features import clr_to_ilr  # noqa: E402
from prospectivity.models import oof_predictions  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "reports" / "tables"
DERIVED = ROOT / "data" / "derived"
K, INNER_K, REPS = 5, 3, 5
METRICS = ["auc", "ap", "capture_1", "capture_5", "capture_10", "capture_20", "brier"]

cells = pd.read_parquet(DERIVED / "cells_labelled.parquet")
conf = cells[~cells["ambiguous"]].reset_index(drop=True)
clr_cols = [c for c in conf.columns if c.startswith("clr_")]
X_clr = conf[clr_cols].to_numpy()
X_ilr = clr_to_ilr(X_clr)
y = conf["label"].to_numpy().astype(int)
cx, cy = conf["cx_m"].to_numpy(), conf["cy_m"].to_numpy()
record("cv.k_outer", K)
record("cv.k_inner", INNER_K)
record("cv.n_repetitions", REPS)
record("cv.n_cells", len(conf), n=len(conf))

schemes = [("random", 0)] + [("block", s) for s in BLOCK_SIZES_KM]
rows, oof = [], []
t0 = time.time()
for model in ["lr", "hgb"]:
    Xm = X_ilr if model == "lr" else X_clr
    for scheme, size in schemes:
        name = scheme if scheme == "random" else f"block{size}"
        for rep in range(REPS):
            if scheme == "random":
                folds = random_folds(y, K, rep)
                groups = None

                def inner(tr, rep=rep):
                    return inner_folds("random", tr, y, None, INNER_K, rep)
            else:
                folds, groups = block_folds(cx, cy, size, K, rep)

                def inner(tr, rep=rep, groups=groups):
                    return inner_folds("group", tr, y, groups, INNER_K, rep)

            check_folds(folds, groups)
            if rep == 0 and model == "lr":
                split_overlap(conf[folds != 0], conf[folds == 0], key="cell_id", quiet=True)
            p, chosen = oof_predictions(model, Xm, y, folds, inner, seed=rep)
            m = evaluate(y, p)
            rows.append(
                {
                    "model": model,
                    "scheme": name,
                    "block_km": size,
                    "rep": rep,
                    "n_blocks": int(len(np.unique(groups))) if groups is not None else 0,
                    "chosen": str(chosen),
                    **m,
                }
            )
            oof.append(
                pd.DataFrame(
                    {"cell_id": conf["cell_id"], "model": model, "scheme": name, "rep": rep, "p": p}
                )
            )
            print(
                f"{model:3s} {name:9s} rep{rep} auc={m['auc']:.3f} ap={m['ap']:.3f} "
                f"blocks={rows[-1]['n_blocks']} [{time.time() - t0:.0f}s]",
                flush=True,
            )

metrics = pd.DataFrame(rows)
metrics.to_csv(TABLES / "cv_metrics.csv", index=False)
pd.concat(oof, ignore_index=True).to_parquet(DERIVED / "oof_predictions.parquet", index=False)

summ = metrics.groupby(["model", "scheme", "block_km"])[METRICS].agg(["mean", "std", "min", "max"])
summ.columns = [f"{a}_{b}" for a, b in summ.columns]
summ = summ.reset_index()
summ.to_csv(TABLES / "cv_summary.csv", index=False)
for _, r in summ.iterrows():
    for met in METRICS:
        for stat in ["mean", "std", "min", "max"]:
            record(
                f"cv.{r.model}.{r.scheme}.{met}.{stat}", round(float(r[f"{met}_{stat}"]), 4), n=REPS
            )
    if r.block_km:
        nb = metrics[(metrics.model == r.model) & (metrics.scheme == r.scheme)]["n_blocks"]
        record(f"cv.{r.model}.{r.scheme}.n_blocks_mean", round(float(nb.mean()), 1))
record("cv.base_rate_pct", round(float(y.mean()) * 100, 2), unit="%")
print(
    summ[
        [
            "model",
            "scheme",
            "auc_mean",
            "auc_std",
            "auc_min",
            "auc_max",
            "ap_mean",
            "capture_10_mean",
        ]
    ].to_string()
)
