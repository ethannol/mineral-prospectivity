"""Step 60: batch-effect checks and the labelled exploratory models.

Confirmatory: leave-one-method-family-out and leave-one-quadrangle-out for
both models. Exploratory (post-freeze, labelled): the method family added as a
covariate (the lab trap), and the sensitivity that keeps ambiguous cells as
negatives. Writes artifacts/tables/batch_metrics.csv and loqo_quads.csv.
"""

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")

from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from cairn import load_ledger, record  # noqa: E402

from prospectivity.cv import (  # noqa: E402
    block_folds,
    evaluate,
    group_folds,
    inner_folds,
    random_folds,
)
from prospectivity.features import clr_to_ilr  # noqa: E402
from prospectivity.models import oof_predictions  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "reports" / "tables"
DERIVED = ROOT / "data" / "derived"
K, INNER_K, REPS = 5, 3, 5
FAMILIES = ["LL", "SR", "OR"]
MIN_PER_CLASS_QUAD = 10

ledger = load_ledger()
REF_KM = float(ledger["moran.reference_block_km"]["value"])

cells = pd.read_parquet(DERIVED / "cells_labelled.parquet")
conf = cells[~cells["ambiguous"]].reset_index(drop=True)
clr_cols = [c for c in conf.columns if c.startswith("clr_")]
X_clr = conf[clr_cols].to_numpy()
X_ilr = clr_to_ilr(X_clr)
y = conf["label"].to_numpy().astype(int)
cx, cy = conf["cx_m"].to_numpy(), conf["cy_m"].to_numpy()
XM = {"lr": X_ilr, "hgb": X_clr}
rows = []


def stats(name, model, scheme, p, mask=None):
    m = evaluate(y[mask] if mask is not None else y, p[mask] if mask is not None else p)
    rows.append({"model": model, "scheme": scheme, "fold": name, **m})
    return m


# --- leave-one-method-family-out (confirmatory) -------------------------------
fam_codes, fam_names = group_folds(conf["method_family"])
lofo_auc = {}
for model in ["lr", "hgb"]:
    p, _ = oof_predictions(
        model,
        XM[model],
        y,
        fam_codes,
        lambda tr: inner_folds("group", tr, y, fam_codes, INNER_K, 0),
        seed=0,
    )
    m = stats("pooled", model, "lofo", p)
    lofo_auc[model] = m["auc"]
    record(f"batch.{model}.lofo.auc", round(m["auc"], 4))
    record(f"batch.{model}.lofo.ap", round(m["ap"], 4))
    record(f"batch.{model}.lofo.capture_10", round(m["capture_10"], 4))
    for code, fam in enumerate(fam_names):
        mask = fam_codes == code
        mm = stats(fam, model, "lofo", p, mask)
        record(f"batch.{model}.lofo.auc_{fam}", round(mm["auc"], 4), n=int(mask.sum()))

# --- leave-one-quadrangle-out (confirmatory) ----------------------------------
quad_codes, quad_names = group_folds(conf["quad"])
counts = conf.groupby("quad")["label"].agg(["sum", "size"])
testable = [i for i, q in enumerate(quad_names) if 0 < counts.loc[q, "sum"] < counts.loc[q, "size"]]
record("batch.loqo.n_quads_tested", len(testable))
record("batch.loqo.n_cells_tested", int(np.isin(quad_codes, testable).sum()))
quad_rows = []
for model in ["lr", "hgb"]:
    p, _ = oof_predictions(
        model,
        XM[model],
        y,
        quad_codes,
        lambda tr: inner_folds("group", tr, y, quad_codes, INNER_K, 0),
        seed=0,
        test_folds=testable,
    )
    scored = ~np.isnan(p)
    m = stats("pooled", model, "loqo", p, scored)
    record(f"batch.{model}.loqo.auc", round(m["auc"], 4), n=int(scored.sum()))
    record(f"batch.{model}.loqo.ap", round(m["ap"], 4))
    per = []
    for code in testable:
        mask = quad_codes == code
        q = quad_names[code]
        n_pos, n_tot = int(y[mask].sum()), int(mask.sum())
        auc = evaluate(y[mask], p[mask])["auc"]
        quad_rows.append(
            {"model": model, "quad": q, "n_cells": n_tot, "n_positive": n_pos, "auc": auc}
        )
        if n_pos >= MIN_PER_CLASS_QUAD and n_tot - n_pos >= MIN_PER_CLASS_QUAD:
            per.append(auc)
    record(f"batch.{model}.loqo.n_quads_reported", len(per))
    record(f"batch.{model}.loqo.auc_quad_min", round(float(min(per)), 4))
    record(f"batch.{model}.loqo.auc_quad_median", round(float(np.median(per)), 4))
    record(f"batch.{model}.loqo.auc_quad_max", round(float(max(per)), 4))
    record(f"batch.{model}.loqo.n_quads_below_half", int(sum(a < 0.5 for a in per)))
pd.DataFrame(quad_rows).to_csv(TABLES / "loqo_quads.csv", index=False)
record("batch.loqo.min_per_class", MIN_PER_CLASS_QUAD)


# --- EXPLORATORY: method family as a covariate (the lab trap) -----------------
def run_scheme(model, X, yy, cxx, cyy, scheme, size, rep):
    if scheme == "random":
        folds = random_folds(yy, K, rep)
        return oof_predictions(
            model,
            X,
            yy,
            folds,
            lambda tr: inner_folds("random", tr, yy, None, INNER_K, rep),
            seed=rep,
        )[0]
    folds, blocks = block_folds(cxx, cyy, size, K, rep)
    return oof_predictions(
        model, X, yy, folds, lambda tr: inner_folds("group", tr, yy, blocks, INNER_K, rep), seed=rep
    )[0]


dummies = pd.get_dummies(conf["method_family"])[FAMILIES].to_numpy().astype(float)
for model in ["lr", "hgb"]:
    Xc = np.hstack([XM[model], dummies])
    for scheme in ["random", "blockref"]:
        aucs, aps = [], []
        for rep in range(REPS):
            p = run_scheme(
                model, Xc, y, cx, cy, "random" if scheme == "random" else "block", REF_KM, rep
            )
            m = stats(f"rep{rep}", model, f"labcov_{scheme}", p)
            aucs.append(m["auc"])
            aps.append(m["ap"])
        for stat, fn in [("mean", np.mean), ("std", np.std), ("min", np.min), ("max", np.max)]:
            record(f"explore.labcov.{model}.{scheme}.auc.{stat}", round(float(fn(aucs)), 4), n=REPS)
            record(f"explore.labcov.{model}.{scheme}.ap.{stat}", round(float(fn(aps)), 4), n=REPS)
    base_random = float(ledger[f"cv.{model}.random.auc.mean"]["value"])
    base_ref = float(ledger[f"cv.{model}.block{int(REF_KM)}.auc.mean"]["value"])
    gain = (
        float(
            np.mean(
                [r["auc"] for r in rows if r["model"] == model and r["scheme"] == "labcov_random"]
            )
        )
        - base_random
    )
    record(f"explore.labcov.{model}.random_gain", round(gain, 4))
    lofo_drop = base_ref - lofo_auc[model]
    record(f"batch.{model}.lofo_minus_blockref", round(-lofo_drop, 4))
    record(f"batch.{model}.lab_trap_present", bool(gain >= 0.02 or lofo_drop >= 0.05))

# --- EXPLORATORY: ambiguous cells kept as negatives ----------------------------
allc = cells.reset_index(drop=True)
y_all = allc["label"].to_numpy().astype(int)
X_all = allc[clr_cols].to_numpy()
record("explore.ambneg.n_cells", len(allc), n=len(allc))
record("explore.ambneg.base_rate_pct", round(float(y_all.mean()) * 100, 2), unit="%")
for scheme in ["random", "blockref"]:
    aucs = []
    for rep in range(REPS):
        p = run_scheme(
            "hgb",
            X_all,
            y_all,
            allc["cx_m"].to_numpy(),
            allc["cy_m"].to_numpy(),
            "random" if scheme == "random" else "block",
            REF_KM,
            rep,
        )
        m = evaluate(y_all, p)
        rows.append({"model": "hgb", "scheme": f"ambneg_{scheme}", "fold": f"rep{rep}", **m})
        aucs.append(m["auc"])
    for stat, fn in [("mean", np.mean), ("std", np.std), ("min", np.min), ("max", np.max)]:
        record(f"explore.ambneg.hgb.{scheme}.auc.{stat}", round(float(fn(aucs)), 4), n=REPS)

pd.DataFrame(rows).to_csv(TABLES / "batch_metrics.csv", index=False)
print(pd.DataFrame(rows).groupby(["model", "scheme"])[["auc", "ap"]].mean().round(3).to_string())
