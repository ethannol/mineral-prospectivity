"""Step 70: headline numbers, decision-rule outcomes, and which elements carry the signal.

Confirmatory arithmetic: leakage inflation and the pre-registered labels.
Exploratory (labelled): logistic coefficients in CLR space, held-out permutation
importance of the boosted model, class contrasts, calibration tables, the full
capture curve, the residual correlogram and the prospectivity-map table.
"""

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")

from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from cairn import load_ledger, record  # noqa: E402
from sklearn.inspection import permutation_importance  # noqa: E402

from prospectivity.cv import (  # noqa: E402
    BLOCK_SIZES_KM,
    block_folds,
    calibration_table,
    capture,
    inner_folds,
    moran_correlogram,
)
from prospectivity.features import clr_to_ilr, ilr_coef_to_clr  # noqa: E402
from prospectivity.models import make_model, select_config  # noqa: E402
from prospectivity.util import commas

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "reports" / "tables"
DERIVED = ROOT / "data" / "derived"
ledger = load_ledger()
L = lambda k: ledger[k]["value"]  # noqa: E731
REF_KM = float(L("moran.reference_block_km"))
REF = f"block{int(REF_KM)}"
METRICS = ["auc", "ap", "capture_1", "capture_5", "capture_10", "capture_20", "brier"]

# --- headline arithmetic and decision rule (confirmatory) ---------------------
for model in ["lr", "hgb"]:
    for met in METRICS:
        for stat in ["mean", "std", "min", "max"]:
            record(f"cv.{model}.ref.{met}.{stat}", L(f"cv.{model}.{REF}.{met}.{stat}"), n=5)
    a_r, a_b = float(L(f"cv.{model}.random.auc.mean")), float(L(f"cv.{model}.{REF}.auc.mean"))
    infl = a_r - a_b
    record(f"headline.{model}.auc_inflation", round(infl, 4))
    record(
        f"headline.{model}.ap_inflation",
        round(float(L(f"cv.{model}.random.ap.mean")) - float(L(f"cv.{model}.{REF}.ap.mean")), 4),
    )
    overlap = float(L(f"cv.{model}.random.auc.min")) <= float(L(f"cv.{model}.{REF}.auc.max"))
    record(f"headline.{model}.ranges_overlap", bool(overlap))
    label = (
        "substantial"
        if (infl >= 0.05 and not overlap)
        else ("small" if infl < 0.02 else "moderate")
    )
    record(f"headline.{model}.leakage_label", label)
    skill = a_b >= 0.60 and float(L(f"cv.{model}.{REF}.auc.min")) > 0.55
    record(f"headline.{model}.skill_beyond_chance", bool(skill))
    record(
        f"headline.{model}.skill_label",
        "has skill beyond the base rate under spatial cross-validation"
        if skill
        else "no demonstrated skill beyond chance once spatial structure is respected",
    )
    record(
        f"headline.{model}.pct_skill_surviving", round((a_b - 0.5) / (a_r - 0.5) * 100, 1), unit="%"
    )
    # capture relative to chance: top 10% of cells would capture 10% of positives by luck
    record(
        f"headline.{model}.capture_10_lift_random",
        round(float(L(f"cv.{model}.random.capture_10.mean")) / 0.10, 2),
    )
    record(
        f"headline.{model}.capture_10_lift_ref",
        round(float(L(f"cv.{model}.{REF}.capture_10.mean")) / 0.10, 2),
    )
    # the largest block size whose mean AUC still satisfies the skill rule
    ok_sizes = [
        s
        for s in BLOCK_SIZES_KM
        if float(L(f"cv.{model}.block{s}.auc.mean")) >= 0.60
        and float(L(f"cv.{model}.block{s}.auc.min")) > 0.55
    ]
    record(
        f"headline.{model}.largest_block_with_skill_km",
        max(ok_sizes) if ok_sizes else "none",
        unit="km",
    )
record("headline.reference_block_km", REF_KM, unit="km")
record(
    "headline.random_vs_block5_note",
    "5 km blocks coincide with single cells, so block-5 CV is random CV without stratification",
)

# --- data ---------------------------------------------------------------------
cells = pd.read_parquet(DERIVED / "cells_labelled.parquet")
conf = cells[~cells["ambiguous"]].reset_index(drop=True)
clr_cols = [c for c in conf.columns if c.startswith("clr_")]
elements = [c.replace("clr_", "").capitalize() for c in clr_cols]
X_clr = conf[clr_cols].to_numpy()
X_ilr = clr_to_ilr(X_clr)
y = conf["label"].to_numpy().astype(int)
cx, cy = conf["cx_m"].to_numpy(), conf["cy_m"].to_numpy()
oof = pd.read_parquet(DERIVED / "oof_predictions.parquet")
cvm = pd.read_csv(TABLES / "cv_metrics.csv")

# --- EXPLORATORY: class contrast and LR coefficients in CLR space --------------
pos, neg = X_clr[y == 1], X_clr[y == 0]
contrast = pd.DataFrame(
    {
        "element": elements,
        "mean_clr_positive": pos.mean(axis=0),
        "mean_clr_negative": neg.mean(axis=0),
        "standardised_difference": (pos.mean(axis=0) - neg.mean(axis=0)) / X_clr.std(axis=0),
    }
)
folds_ref, blocks_ref = block_folds(cx, cy, REF_KM, 5, 0)
inner_ref = lambda tr: inner_folds("group", tr, y, blocks_ref, 3, 0)  # noqa: E731
c_lr = select_config("lr", X_ilr, y, inner_ref(np.arange(len(y))), 0)
lr = make_model("lr", c_lr, 0).fit(X_ilr, y)
scale = lr.named_steps["standardscaler"].scale_
beta_ilr = lr.named_steps["logisticregression"].coef_[0] / scale  # per unit ILR
beta_clr = ilr_coef_to_clr(beta_ilr, len(elements))
contrast["lr_clr_coefficient"] = beta_clr
record("explore.lr_C_selected", c_lr)

# --- EXPLORATORY: held-out permutation importance of the boosted model ---------
c_hgb = select_config("hgb", X_clr, y, inner_ref(np.arange(len(y))), 0)
record("explore.hgb_config_selected", f"learning rate {c_hgb[0]}, {c_hgb[1]} leaves")
imp = np.zeros((5, len(elements)))
for f in range(5):
    tr, te = folds_ref != f, folds_ref == f
    m = make_model("hgb", c_hgb, 0).fit(X_clr[tr], y[tr])
    r = permutation_importance(m, X_clr[te], y[te], scoring="roc_auc", n_repeats=5, random_state=0)
    imp[f] = r.importances_mean
contrast["hgb_permutation_importance_auc"] = imp.mean(axis=0)
contrast["hgb_permutation_importance_sd_folds"] = imp.std(axis=0)
contrast.to_csv(TABLES / "element_signal.csv", index=False)
top_imp = contrast.sort_values("hgb_permutation_importance_auc", ascending=False)
record("explore.top_elements_hgb", commas(top_imp["element"].head(3)))
record(
    "explore.top_element_hgb_importance",
    round(float(top_imp["hgb_permutation_importance_auc"].iloc[0]), 4),
)
record(
    "explore.third_element_hgb_importance",
    round(float(top_imp["hgb_permutation_importance_auc"].iloc[2]), 4),
)
by_coef = contrast.sort_values("lr_clr_coefficient")
record("explore.lr_most_negative_elements", commas(by_coef["element"].head(3)))
record("explore.lr_most_positive_elements", commas(by_coef["element"].tail(3)[::-1]))
record("explore.lr_coef_max_element", by_coef["element"].iloc[-1])
record("explore.lr_coef_max", round(float(by_coef["lr_clr_coefficient"].iloc[-1]), 3))
record("explore.lr_coef_min_element", by_coef["element"].iloc[0])
record("explore.lr_coef_min", round(float(by_coef["lr_clr_coefficient"].iloc[0]), 3))
by_d = contrast.sort_values("standardised_difference")
record("explore.contrast_most_enriched", commas(by_d["element"].tail(3)[::-1]))
record("explore.contrast_most_depleted", commas(by_d["element"].head(3)))
record("explore.contrast_max_d", round(float(by_d["standardised_difference"].iloc[-1]), 3))
record("explore.contrast_min_d", round(float(by_d["standardised_difference"].iloc[0]), 3))

# --- calibration, capture curve, prospectivity map, residual correlogram -------
for scheme in ["random", REF]:
    sub = (
        oof[(oof.model == "hgb") & (oof.scheme == scheme) & (oof.rep == 0)]
        .set_index("cell_id")
        .loc[conf["cell_id"]]
    )
    p = sub["p"].to_numpy()
    cal = calibration_table(y, p, 10)
    cal.to_csv(TABLES / f"calibration_hgb_{scheme}.csv", index=False)
    tag = "random" if scheme == "random" else "ref"
    record(
        f"calib.hgb.{tag}.top_decile_obs_rate_pct",
        round(float(cal["obs_rate"].iloc[-1]) * 100, 1),
        unit="%",
    )
    record(
        f"calib.hgb.{tag}.top_decile_mean_pred_pct",
        round(float(cal["mean_pred"].iloc[-1]) * 100, 1),
        unit="%",
    )
    record(
        f"calib.hgb.{tag}.bottom_decile_obs_rate_pct",
        round(float(cal["obs_rate"].iloc[0]) * 100, 1),
        unit="%",
    )
    record(
        f"calib.hgb.{tag}.pred_range_pct",
        f"{cal['mean_pred'].iloc[0] * 100:.1f} to {cal['mean_pred'].iloc[-1] * 100:.1f}",
        unit="%",
    )
fracs = np.arange(0.01, 1.0001, 0.01)
curves = []
for model in ["lr", "hgb"]:
    for scheme in ["random", REF]:
        for rep in range(5):
            sub = (
                oof[(oof.model == model) & (oof.scheme == scheme) & (oof.rep == rep)]
                .set_index("cell_id")
                .loc[conf["cell_id"]]
            )
            p = sub["p"].to_numpy()
            curves.append(
                pd.DataFrame(
                    {
                        "model": model,
                        "scheme": scheme,
                        "rep": rep,
                        "fraction": fracs,
                        "captured": [capture(y, p, f) for f in fracs],
                    }
                )
            )
pd.concat(curves, ignore_index=True).to_csv(TABLES / "capture_curves.csv", index=False)

sub = (
    oof[(oof.model == "hgb") & (oof.scheme == REF) & (oof.rep == 0)]
    .set_index("cell_id")
    .loc[conf["cell_id"]]
)
pmap = conf[
    ["cell_id", "cx_m", "cy_m", "lon", "lat", "label", "method_family", "quad", "n_samples"]
].copy()
pmap["p_blockref"] = sub["p"].to_numpy()
sub_r = (
    oof[(oof.model == "hgb") & (oof.scheme == "random") & (oof.rep == 0)]
    .set_index("cell_id")
    .loc[conf["cell_id"]]
)
pmap["p_random"] = sub_r["p"].to_numpy()
pmap.to_csv(TABLES / "prospectivity_map.csv", index=False)

resid = y - pmap["p_random"].to_numpy()
edges = np.arange(0, 150_001, 5_000, dtype=float)
rc = moran_correlogram(cx, cy, resid, edges)
rc["lo_km"], rc["hi_km"] = rc["lo_m"] / 1000, rc["hi_m"] / 1000
rc.to_csv(TABLES / "moran_residual.csv", index=False)
record("explore.moran_residual_bin1", round(float(rc["moran_i"].iloc[0]), 4))
record("explore.moran_residual_bin2", round(float(rc["moran_i"].iloc[1]), 4))
print(contrast.round(3).to_string())
