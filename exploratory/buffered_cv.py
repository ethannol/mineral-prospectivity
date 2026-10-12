"""Standalone supplementary analysis; run on the remote analysis machine only.

Same 100km blocks and fixed model grids as baseline. Outer AND inner train sets
exclude centres within the requested radius of test centres. No baseline writes.
"""
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")
import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from sklearn.metrics import roc_auc_score

from prospectivity.buffered import buffered_train_indices
from prospectivity.cv import block_folds, evaluate, inner_folds
from prospectivity.features import clr_to_ilr
from prospectivity.models import GRIDS, make_model

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--buffers-km", type=float, nargs="+", default=[0, 5, 10, 25])
    args = parser.parse_args()
    cells = pd.read_parquet(ROOT / "data/derived/cells_labelled.parquet")
    cells = cells.loc[~cells.ambiguous].reset_index(drop=True)
    xy = cells[["cx_m", "cy_m"]].to_numpy()
    y = cells.label.to_numpy(int)
    clr = cells.filter(regex="^clr_").to_numpy()
    rows, predictions = [], []
    for rep in range(args.reps):
        folds, groups = block_folds(*xy.T, 100, 5, rep)
        for radius in args.buffers_km:
            for name, X in [("lr", clr_to_ilr(clr)), ("hgb", clr)]:
                p = np.full(len(y), np.nan)
                for fold in range(5):
                    test = np.flatnonzero(folds == fold)
                    original = np.flatnonzero(folds != fold)
                    train = buffered_train_indices(xy, original, test, radius * 1000)
                    if len(np.unique(y[train])) < 2:
                        raise ValueError("buffer leaves an unidentifiable outer fold")
                    inner = inner_folds("group", train, y, groups, 3, rep)
                    best, score = None, -np.inf
                    for config in GRIDS[name]:
                        scores = []
                        for f in np.unique(inner):
                            val = train[inner == f]
                            tr = buffered_train_indices(xy, train[inner != f], val, radius * 1000)
                            if len(np.unique(y[tr])) < 2 or len(np.unique(y[val])) < 2:
                                continue
                            model = make_model(name, config, rep).fit(X[tr], y[tr])
                            scores.append(roc_auc_score(y[val], model.predict_proba(X[val])[:, 1]))
                        candidate = np.mean(scores) if scores else -np.inf
                        if candidate > score:
                            best, score = config, candidate
                    if best is None:
                        raise ValueError("no valid buffered inner folds; refusing untuned fallback")
                    model = make_model(name, best, rep).fit(X[train], y[train])
                    p[test] = model.predict_proba(X[test])[:, 1]
                    rows.append(dict(rep=rep, buffer_km=radius, model=name, fold=fold,
                                     n_test=len(test), n_train=len(train),
                                     n_removed=len(original)-len(train),
                                     chosen=str(best), n_train_positive=int(y[train].sum()),
                                     minimum_train_test_km=float(
                                         cKDTree(xy[test]).query(xy[train])[0].min()/1000)))
                predictions.append(pd.DataFrame(dict(cell_id=cells.cell_id, rep=rep,
                                                      buffer_km=radius, model=name, y=y, p=p)))
                print(rep, radius, name, evaluate(y, p), flush=True)
    out = ROOT / "reports/exploratory/buffered_cv"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out / "folds.csv", index=False)
    pred = pd.concat(predictions, ignore_index=True)
    pred.to_csv(out / "predictions.csv", index=False)
    summary = []
    for (name, radius, rep), g in pred.groupby(["model", "buffer_km", "rep"]):
        summary.append(dict(model=name, buffer_km=radius, rep=rep, **evaluate(g.y, g.p)))
    pd.DataFrame(summary).to_csv(out / "metrics.csv", index=False)
    metadata = dict(exploratory=True, source_revision=subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(), repetitions=args.reps,
        buffer_km=args.buffers_km, block_km=100, seed_rule="rep index", baseline_unchanged=True)
    (out / "provenance.json").write_text(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
