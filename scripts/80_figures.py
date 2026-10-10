"""Step 80: figures for the report (Matplotlib, written to reports/figures/).

Palette and mark conventions follow the project's data-viz method: categorical
slots in fixed order (blue = HGB / first series, orange = LR / second series,
aqua = third), one-hue sequential blue ramp for magnitude, solid hairline grid,
2 px lines, >= 8 px markers, text in ink tokens, a legend whenever there are
two or more series. No numbers are recorded here; every figure reads a table
written by an earlier step.
"""

from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from cairn import load_ledger

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "reports" / "tables"
FIGS = ROOT / "reports" / "figures"
FIGS.mkdir(parents=True, exist_ok=True)
DERIVED = ROOT / "data" / "derived"

SURFACE, INK, INK2, MUTED, GRID, AXIS = (
    "#fcfcfb",
    "#0b0b0b",
    "#52514e",
    "#898781",
    "#e1e0d9",
    "#c3c2b7",
)
S1, S2, S3 = "#2a78d6", "#eb6834", "#1baf7a"  # categorical slots 1-3 (validated)
SEQ = ["#b7d3f6", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
CMAP = LinearSegmentedColormap.from_list("seq_blue", SEQ)
FAMILY_COLOR = {"LL": S1, "SR": S2, "OR": S3}
MODEL_COLOR = {"hgb": S1, "lr": S2}
MODEL_NAME = {"hgb": "Gradient boosted trees", "lr": "Logistic regression (ILR)"}

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "sans-serif",
        "font.size": 10,
        "text.color": INK,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK2,
        "axes.titlecolor": INK,
        "axes.titleweight": "bold",
        "axes.titlesize": 11,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": INK2,
        "ytick.labelcolor": INK2,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "grid.linestyle": "-",
        "axes.axisbelow": True,
        "lines.linewidth": 2,
        "lines.markersize": 6,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "savefig.dpi": 160,
        "savefig.bbox": "tight",
    }
)
ledger = load_ledger()
L = lambda k: ledger[k]["value"]  # noqa: E731
REF_KM = float(L("moran.reference_block_km"))
REF = f"block{int(REF_KM)}"


def km(a):
    return np.asarray(a) / 1000.0


# --- fig1 coverage ------------------------------------------------------------
samples = pd.read_parquet(DERIVED / "samples_clr.parquet")
sites = pd.read_parquet(DERIVED / "sites.parquet")
fig, ax = plt.subplots(figsize=(6.4, 8.2))
for fam, g in samples.groupby("method_family"):
    ax.scatter(
        km(g.x_m),
        km(g.y_m),
        s=2.5,
        c=FAMILY_COLOR[fam],
        alpha=0.75,
        linewidths=0,
        label=f"NURE stream sediment, {fam} family (n={len(g):,})",
    )
pos = sites[sites.is_positive]
ax.scatter(
    km(pos.x_m),
    km(pos.y_m),
    s=14,
    facecolors="none",
    edgecolors=INK,
    linewidths=0.6,
    label=f"MRDS gold producer (n={len(pos):,})",
)
ax.set_aspect("equal")
ax.set_xlabel("UTM 11N easting (km)")
ax.set_ylabel("UTM 11N northing (km)")
ax.set_title("Coverage: retained stream-sediment samples and gold producers, Nevada")
ax.legend(loc="lower left", markerscale=3, handletextpad=0.4)
fig.savefig(FIGS / "fig1_coverage.png")
plt.close(fig)

# --- fig2 censored fraction by element and family -----------------------------
cens = pd.read_csv(TABLES / "censored_fraction_suite.csv")
cens["el"] = cens["element"].str.split("_").str[0].str.capitalize()
order = cens.groupby("el")["censored_fraction"].max().sort_values().index.tolist()
fams = ["LL", "SR", "OR"]
fig, ax = plt.subplots(figsize=(6.4, 4.6))
ypos = np.arange(len(order))
h = 0.26
for i, fam in enumerate(fams):
    sub = cens[cens.method_family == fam].set_index("el").loc[order]
    ax.barh(
        ypos + (i - 1) * h,
        sub["censored_fraction"] * 100,
        height=h - 0.04,
        color=FAMILY_COLOR[fam],
        label=f"{fam} family",
        linewidth=0,
    )
ax.axvline(float(L("prep.suite_rule_max_censored_pct")), color=MUTED, linewidth=1)
ax.text(
    float(L("prep.suite_rule_max_censored_pct")) + 0.4,
    len(order) - 0.6,
    "suite rule: at most this share censored",
    color=INK2,
    fontsize=8.5,
    va="top",
)
ax.set_yticks(ypos, order)
ax.set_xlabel("Share of retained samples below detection limit (%)")
ax.set_title("Censoring by element and analytical method family")
ax.grid(axis="y", visible=False)
ax.legend(loc="lower right")
fig.savefig(FIGS / "fig2_censoring.png")
plt.close(fig)

# --- fig3 Moran's I correlogram -----------------------------------------------
ml = pd.read_csv(TABLES / "moran_label.csv")
mr = pd.read_csv(TABLES / "moran_residual.csv")
fig, ax = plt.subplots(figsize=(6.4, 4.0))
mid = (ml.lo_km + ml.hi_km) / 2
ax.plot(
    mid,
    ml.moran_i,
    color=S1,
    marker="o",
    markeredgecolor=SURFACE,
    markeredgewidth=1.2,
    label="Cell label (gold producer present)",
)
ax.plot(
    mid,
    mr.moran_i,
    color=S2,
    marker="o",
    markeredgecolor=SURFACE,
    markeredgewidth=1.2,
    label="Random-CV residual, boosted model (exploratory)",
)
ax.axhline(float(L("moran.threshold")), color=MUTED, linewidth=1)
ax.axhline(0, color=AXIS, linewidth=0.8)
rng_km = L("moran.range_km")
if isinstance(rng_km, (int, float)):
    ax.axvline(rng_km, color=MUTED, linewidth=1)
    ax.text(
        rng_km + 1.5,
        0.19,
        f"I < {L('moran.threshold')} beyond {rng_km:g} km\nreference block {REF_KM:g} km",
        color=INK2,
        fontsize=8.5,
        va="top",
    )
ax.set_xlabel("Distance between cell centroids (km)")
ax.set_ylabel("Moran's I")
ax.set_title("Spatial autocorrelation of the target, by distance bin")
ax.legend(loc="upper right")
fig.savefig(FIGS / "fig3_moran.png")
plt.close(fig)

# --- fig4 headline: AUC and AP against block size ------------------------------
summ = pd.read_csv(TABLES / "cv_summary.csv")
sizes = sorted(summ.loc[summ.block_km > 0, "block_km"].unique())
fig, axes = plt.subplots(1, 2, figsize=(9.6, 4.2))
for ax, met, name in [(axes[0], "auc", "AUC"), (axes[1], "ap", "Average precision")]:
    for model in ["hgb", "lr"]:
        b = summ[(summ.model == model) & (summ.block_km > 0)].sort_values("block_km")
        r = summ[(summ.model == model) & (summ.scheme == "random")].iloc[0]
        c = MODEL_COLOR[model]
        ax.fill_between(
            b.block_km, b[f"{met}_min"], b[f"{met}_max"], color=c, alpha=0.12, linewidth=0
        )
        ax.plot(
            b.block_km,
            b[f"{met}_mean"],
            color=c,
            marker="o",
            markeredgecolor=SURFACE,
            markeredgewidth=1.2,
            label=f"{MODEL_NAME[model]}, block CV (mean, min-max)",
        )
        ax.axhspan(r[f"{met}_min"], r[f"{met}_max"], color=c, alpha=0.08, linewidth=0)
        ax.axhline(
            r[f"{met}_mean"],
            color=c,
            linewidth=1.2,
            alpha=0.9,
            label=f"{MODEL_NAME[model]}, random 5-fold (mean, range)",
        )
    chance = 0.5 if met == "auc" else float(L("cv.base_rate_pct")) / 100
    ax.axhline(chance, color=MUTED, linewidth=1)
    ax.text(
        sizes[-1],
        chance,
        "chance" if met == "auc" else "base rate",
        color=INK2,
        fontsize=8.5,
        va="bottom",
        ha="right",
    )
    ax.set_xscale("log")
    ax.set_xticks(sizes, [f"{int(s)}" for s in sizes])
    ax.minorticks_off()
    ax.set_xlabel("Spatial block size (km)")
    ax.set_ylabel(name)
    ax.set_title(f"{name} of held-out cells against block size")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=2, fontsize=8.5, bbox_to_anchor=(0.5, -0.02))
fig.savefig(FIGS / "fig4_auc_vs_block_size.png")
plt.close(fig)

# --- fig5 capture curves ------------------------------------------------------
cc = pd.read_csv(TABLES / "capture_curves.csv")
fig, ax = plt.subplots(figsize=(6.0, 4.6))
for scheme, c, lab in [
    ("random", S1, "Random 5-fold CV"),
    (REF, S2, f"Spatial block CV, {int(REF_KM)} km blocks"),
]:
    g = (
        cc[(cc.model == "hgb") & (cc.scheme == scheme)]
        .groupby("fraction")["captured"]
        .agg(["mean", "min", "max"])
        .reset_index()
    )
    ax.fill_between(
        g.fraction * 100, g["min"] * 100, g["max"] * 100, color=c, alpha=0.12, linewidth=0
    )
    ax.plot(
        g.fraction * 100, g["mean"] * 100, color=c, label=f"{lab} (mean, min-max over repetitions)"
    )
    marks = g[g.fraction.round(2).isin([0.01, 0.05, 0.10, 0.20])]
    ax.plot(
        marks.fraction * 100,
        marks["mean"] * 100,
        "o",
        color=c,
        markeredgecolor=SURFACE,
        markeredgewidth=1.2,
    )
ax.plot([0, 100], [0, 100], color=MUTED, linewidth=1, label="Chance (random ranking)")
ax.set_xlabel("Cells ranked by predicted probability, top share (%)")
ax.set_ylabel("Held-out gold-producer cells captured (%)")
ax.set_title("Capture curve, gradient boosted trees")
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.legend(loc="upper left", fontsize=8.5)
fig.savefig(FIGS / "fig5_capture.png")
plt.close(fig)

# --- fig6 calibration ---------------------------------------------------------
fig, ax = plt.subplots(figsize=(5.2, 4.8))
for scheme, c, lab in [
    ("random", S1, "Random 5-fold CV"),
    (REF, S2, f"Spatial block CV, {int(REF_KM)} km blocks"),
]:
    cal = pd.read_csv(TABLES / f"calibration_hgb_{scheme}.csv")
    ax.plot(
        cal.mean_pred * 100,
        cal.obs_rate * 100,
        color=c,
        marker="o",
        markeredgecolor=SURFACE,
        markeredgewidth=1.2,
        label=lab,
    )
lim = max(ax.get_xlim()[1], ax.get_ylim()[1])
ax.plot([0, lim], [0, lim], color=MUTED, linewidth=1, label="Perfect calibration")
ax.axhline(float(L("cv.base_rate_pct")), color=AXIS, linewidth=0.8)
ax.set_xlabel("Mean predicted probability in decile (%)")
ax.set_ylabel("Observed share of cells with a producer (%)")
ax.set_title("Reliability of held-out predictions, boosted model")
ax.legend(loc="upper left", fontsize=8.5)
fig.savefig(FIGS / "fig6_calibration.png")
plt.close(fig)

# --- fig7 prospectivity map of held-out predictions ----------------------------
pm = pd.read_csv(TABLES / "prospectivity_map.csv")
fig, ax = plt.subplots(figsize=(6.6, 8.2))
ax.set_aspect("equal")
x, y = km(pm.cx_m), km(pm.cy_m)
ax.set_xlim(x.min() - 10, x.max() + 10)
ax.set_ylim(y.min() - 10, y.max() + 10)
fig.canvas.draw()
ppk = ax.get_window_extent().width / (ax.get_xlim()[1] - ax.get_xlim()[0]) * 72 / fig.dpi
side = float(L("features.cell_km")) * ppk
vmax = float(np.quantile(pm.p_blockref, 0.99))
sc = ax.scatter(
    x, y, c=pm.p_blockref, cmap=CMAP, vmin=0, vmax=vmax, marker="s", s=side**2, linewidths=0
)
p1 = pm[pm.label == 1]
ax.scatter(
    km(p1.cx_m),
    km(p1.cy_m),
    s=side**2 * 0.9,
    facecolors="none",
    edgecolors=INK,
    linewidths=0.5,
    marker="s",
)
cb = fig.colorbar(sc, ax=ax, fraction=0.035, pad=0.02)
cb.set_label(f"Held-out predicted probability, {int(REF_KM)} km block CV")
cb.outline.set_visible(False)
ax.set_xlabel("UTM 11N easting (km)")
ax.set_ylabel("UTM 11N northing (km)")
ax.set_title("Prospectivity: out-of-fold predictions, gradient boosted trees")
ax.legend(
    handles=[
        Line2D(
            [],
            [],
            marker="s",
            markerfacecolor="none",
            markeredgecolor=INK,
            linestyle="none",
            label="Cell with a known gold producer",
        )
    ],
    loc="lower left",
)
fig.savefig(FIGS / "fig7_prospectivity_map.png")
plt.close(fig)
print("figures written:", sorted(p.name for p in FIGS.glob("*.png")))
