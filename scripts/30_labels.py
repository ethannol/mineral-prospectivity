"""Step 30: classify MRDS sites, join to cells, derive labels and the population.

Reads data/raw/mrds_nv.csv and data/derived/cells.parquet, writes
data/derived/cells_labelled.parquet and data/derived/sites.parquet.
"""

from pathlib import Path

import pandas as pd
from cairn import denominator, record
from cairn.checks import target_proxy

from prospectivity.features import CELL_KM, cell_index, project_utm
from prospectivity.labels import (
    classify_sites,
    label_cells,
    planted_duplicate_check,
    site_counts_per_cell,
)
from prospectivity.prepare import load_mrds

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived"
MIN_POSITIVE_CELLS, MIN_CELLS, MIN_POS_PER_FAMILY = (
    150,
    1000,
    10,
)  # pre-registered abstention thresholds

mrds = load_mrds(ROOT / "data/raw/mrds_nv.csv")
sites = classify_sites(mrds)
record("labels.n_sites", len(sites), n=len(sites))
n_before = len(sites)
sites = sites[sites["latitude"].notna() & sites["longitude"].notna()].reset_index(drop=True)
record("labels.n_sites_no_coords", n_before - len(sites))
record("labels.n_positive_sites", int(sites["is_positive"].sum()))
record("labels.n_ambiguous_sites", int(sites["is_ambiguous"].sum()))
record(
    "labels.n_positive_sites_unique_coords",
    int(sites.loc[sites.is_positive, ["latitude", "longitude"]].drop_duplicates().shape[0]),
)
record(
    "labels.n_positive_sites_producer",
    int((sites.is_positive & (sites.dev_stat == "Producer")).sum()),
)
record(
    "labels.n_positive_sites_past_producer",
    int((sites.is_positive & (sites.dev_stat == "Past Producer")).sum()),
)

x, y = project_utm(sites["longitude"].to_numpy(), sites["latitude"].to_numpy())
sites = pd.concat([sites, cell_index(x, y, CELL_KM)], axis=1)
sites["x_m"], sites["y_m"] = x, y
sites.to_parquet(DERIVED / "sites.parquet", index=False)

cells = pd.read_parquet(DERIVED / "cells.parquet")
counts = site_counts_per_cell(sites)
labelled = label_cells(cells, counts)
assert len(labelled) == len(cells)
record("labels.planted_duplicate_ok", planted_duplicate_check(sites, cells[["cell_id"]]))

# coverage: how many positive sites fall in cells that have samples at all
sampled = set(cells["cell_id"])
pos_sites = sites[sites.is_positive]
in_sampled = pos_sites["cell_id"].isin(sampled)
record("labels.n_positive_sites_in_sampled_cells", int(in_sampled.sum()))
record(
    "labels.pct_positive_sites_in_sampled_cells", round(float(in_sampled.mean()) * 100, 1), unit="%"
)
record("labels.n_cells_with_positive_site", int(labelled["label"].sum()))

record("labels.n_cells_all", len(labelled))
record("labels.n_cells_ambiguous", int(labelled["ambiguous"].sum()))
conf = labelled[~labelled["ambiguous"]].reset_index(drop=True)
record("labels.n_cells", len(conf), n=len(conf))
record("labels.n_positive_cells", int(conf["label"].sum()))
record("labels.n_negative_cells", int((conf["label"] == 0).sum()))
denominator(
    int(conf["label"].sum()),
    len(conf),
    "base_rate",
    population_desc="non-ambiguous sampled 5 km cells",
)
record("labels.base_rate_pct", round(float(conf["label"].mean()) * 100, 2), unit="%")
record(
    "labels.positive_cells_sites_median",
    float(conf.loc[conf.label == 1, "n_positive_sites"].median()),
)
for fam in ["LL", "SR", "OR"]:
    sub = conf[conf.method_family == fam]
    record(f"labels.n_positive_cells_{fam}", int(sub["label"].sum()))
    record(f"labels.base_rate_pct_{fam}", round(float(sub["label"].mean()) * 100, 2), unit="%")
quad_pos = conf.groupby("quad")["label"].agg(["sum", "size"])
record(
    "labels.n_quads_with_both_classes",
    int(((quad_pos["sum"] > 0) & (quad_pos["sum"] < quad_pos["size"])).sum()),
)

abstain = (
    int(conf["label"].sum()) < MIN_POSITIVE_CELLS
    or len(conf) < MIN_CELLS
    or any(
        int(conf.loc[conf.method_family == f, "label"].sum()) < MIN_POS_PER_FAMILY
        for f in ["LL", "SR", "OR"]
    )
)
record("labels.abstain", bool(abstain))

# the sensor for columns that alone separate the target (sample count is the one to watch)
feat_cols = [c for c in conf.columns if c.startswith("clr_")] + ["n_samples"]
target_proxy(conf[feat_cols + ["label"]], "label")
r = float(conf[["n_samples", "label"]].corr().iloc[0, 1])
record("labels.corr_n_samples_label", round(r, 3))

labelled.to_parquet(DERIVED / "cells_labelled.parquet", index=False)
print(f"{len(conf)} cells in population, {int(conf.label.sum())} positive; abstain={abstain}")
