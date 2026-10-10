"""MRDS site classification and the deposit-to-cell join."""

from __future__ import annotations

import re

import numpy as np
import pandas as pd

GOLD = re.compile(r"\bGold\b")
PRODUCER_STATUS = {"Producer", "Past Producer"}


def classify_sites(mrds: pd.DataFrame, commodity_re: re.Pattern = GOLD) -> pd.DataFrame:
    """Add ``is_positive`` and ``is_ambiguous`` flags to MRDS site rows.

    Positive: Producer/Past Producer with the commodity in ``commod1`` (primary
    list). Ambiguous: any other row that mentions the commodity in commod1, 2 or 3.
    """
    df = mrds.copy()
    c1 = df["commod1"].fillna("").astype(str)
    c2 = df["commod2"].fillna("").astype(str)
    c3 = df["commod3"].fillna("").astype(str)
    in1 = c1.str.contains(commodity_re)
    any_rank = in1 | c2.str.contains(commodity_re) | c3.str.contains(commodity_re)
    producer = df["dev_stat"].isin(PRODUCER_STATUS)
    df["is_positive"] = (in1 & producer).to_numpy()
    df["is_ambiguous"] = (any_rank & ~(in1 & producer)).to_numpy()
    return df


def site_counts_per_cell(sites: pd.DataFrame) -> pd.DataFrame:
    """Per cell: number of positive and ambiguous sites. One row per cell_id."""
    g = sites.groupby("cell_id", sort=True)
    out = g.agg(n_positive_sites=("is_positive", "sum"), n_ambiguous_sites=("is_ambiguous", "sum"))
    return out.astype(int).reset_index()


def label_cells(cells: pd.DataFrame, counts: pd.DataFrame) -> pd.DataFrame:
    """Left-join site counts onto cells (1:1 on cell_id) and derive the label.

    Returns cells with ``n_positive_sites``, ``n_ambiguous_sites``, ``label``
    (1 positive, 0 negative) and ``ambiguous`` (True = excluded from the
    confirmatory population). Row count must equal ``len(cells)``.
    """
    from cairn import checked_merge, unique_key

    unique_key(cells, "cell_id", name="unique_key(cells.cell_id)")
    unique_key(counts, "cell_id", name="unique_key(site_counts.cell_id)")
    out = checked_merge(
        cells, counts, on="cell_id", how="left", expect="1:1", name="join_check(cells+site_counts)"
    )
    if len(out) != len(cells):
        raise ValueError(f"label join changed row count {len(cells)} -> {len(out)}")
    # a cell with no MRDS site has no row in counts: zero sites, not missing
    out["n_positive_sites"] = out["n_positive_sites"].fillna(0).astype(int)
    out["n_ambiguous_sites"] = out["n_ambiguous_sites"].fillna(0).astype(int)
    out["label"] = (out["n_positive_sites"] > 0).astype(int)
    out["ambiguous"] = (out["label"] == 0) & (out["n_ambiguous_sites"] > 0)
    return out


def planted_duplicate_check(sites: pd.DataFrame, cells: pd.DataFrame) -> bool:
    """True if duplicating every positive site leaves the cell labels unchanged."""
    dup = pd.concat([sites, sites[sites.is_positive]], ignore_index=True)
    a = label_cells(cells, site_counts_per_cell(sites))["label"].to_numpy()
    b = label_cells(cells, site_counts_per_cell(dup))["label"].to_numpy()
    return bool(np.array_equal(a, b))
