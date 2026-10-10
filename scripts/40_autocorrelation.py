"""Step 40: Moran's I correlogram of the cell label, before any model is fitted.

Fixes the reference block size by the pre-registered rule. Writes
artifacts/tables/moran_label.csv.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from cairn import record

from prospectivity.cv import (
    BLOCK_SIZES_KM,
    first_lag_below,
    moran_correlogram,
    reference_block_size,
)
from prospectivity.util import commas

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "reports" / "tables"
BIN_KM, MAX_KM, THRESHOLD = 5, 150, 0.05

cells = pd.read_parquet(ROOT / "data/derived/cells_labelled.parquet")
conf = cells[~cells["ambiguous"]].reset_index(drop=True)
edges = np.arange(0, MAX_KM * 1000 + 1, BIN_KM * 1000, dtype=float)
corr = moran_correlogram(
    conf["cx_m"].to_numpy(), conf["cy_m"].to_numpy(), conf["label"].to_numpy(), edges
)
corr["lo_km"], corr["hi_km"] = corr["lo_m"] / 1000, corr["hi_m"] / 1000
corr.to_csv(TABLES / "moran_label.csv", index=False)

record("moran.bin_km", BIN_KM, unit="km")
record("moran.max_km", MAX_KM, unit="km")
record("moran.threshold", THRESHOLD)
record("moran.expected_null", round(-1.0 / (len(conf) - 1), 5))
for i in range(4):
    record(
        f"moran.i_bin{i + 1}",
        round(float(corr["moran_i"].iloc[i]), 4),
        n=int(corr["n_pairs"].iloc[i]),
    )
record("moran.i_bin1_hi_km", float(corr["hi_km"].iloc[0]), unit="km")
rng_m = first_lag_below(corr, THRESHOLD)
record(
    "moran.range_km",
    (rng_m / 1000) if rng_m is not None else f"not reached within {MAX_KM}",
    unit="km",
)
ref = reference_block_size(rng_m, BLOCK_SIZES_KM)
record("moran.reference_block_km", ref, unit="km")
record("moran.block_sizes_km", commas(str(s) for s in BLOCK_SIZES_KM), unit="km")
# the random-CV analogue: units within one 5 km cell are neighbours at distance 5 km
print(corr[["lo_km", "hi_km", "n_pairs", "moran_i"]].head(12).to_string())
print(f"range {rng_m} m -> reference block {ref} km")
