"""Step 20: censored substitution, CLR per sample, UTM grid, cell aggregation.

Reads data/derived/samples.parquet, writes data/derived/cells.parquet.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from cairn import record

from prospectivity.features import (
    CELL_KM,
    UTM_EPSG,
    aggregate_cells,
    cell_index,
    censored_to_value,
    clr,
    project_utm,
)
from prospectivity.prepare import SUITE

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived"
SUBSTITUTION_FACTOR = 0.5  # labelled substitution: half the detection limit

samples = pd.read_parquet(DERIVED / "samples.parquet")
suite = sorted(SUITE)
record("features.substitution_factor", SUBSTITUTION_FACTOR)
record("features.cell_km", CELL_KM, unit="km")
record("features.utm_epsg", UTM_EPSG)

# concentrations in ppm, censored -> factor * detection limit
conc = np.column_stack(
    [censored_to_value(samples[e], SUBSTITUTION_FACTOR) * SUITE[e] for e in suite]
)
assert not np.isnan(conc).any(), "complete-case filter failed upstream"
Z = clr(conc)
clr_cols = [f"clr_{e.split('_')[0]}" for e in suite]
feat = pd.DataFrame(Z, columns=clr_cols)

x, y = project_utm(samples["longitude"].to_numpy(), samples["latitude"].to_numpy())
grid = cell_index(x, y, CELL_KM)
df = pd.concat([samples.reset_index(drop=True), grid, feat], axis=1)
df["x_m"], df["y_m"] = x, y
df.to_parquet(DERIVED / "samples_clr.parquet", index=False)

cells = aggregate_cells(df, clr_cols)
cells.to_parquet(DERIVED / "cells.parquet", index=False)

record("features.n_cells", len(cells), n=len(cells))
record("features.samples_per_cell_median", float(cells["n_samples"].median()))
record("features.samples_per_cell_max", int(cells["n_samples"].max()))
record("features.n_cells_single_sample", int((cells["n_samples"] == 1).sum()))
record(
    "features.pct_cells_single_sample",
    round(float((cells["n_samples"] == 1).mean()) * 100, 1),
    unit="%",
)
record("features.n_cells_mixed_family", int((cells["family_share"] < 1).sum()))
record(
    "features.extent_x_km",
    round(float((cells["cx_m"].max() - cells["cx_m"].min()) / 1000), 0),
    unit="km",
)
record(
    "features.extent_y_km",
    round(float((cells["cy_m"].max() - cells["cy_m"].min()) / 1000), 0),
    unit="km",
)
for fam, n in cells["method_family"].value_counts().items():
    record(f"features.n_cells_{fam}", int(n))
print(f"{len(cells)} cells from {len(df)} samples")
