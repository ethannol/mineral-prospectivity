"""Load the Nevada extracts and build the sample table with an exclusion log."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from prospectivity.features import censored_fraction

# The ten-element suite fixed in docs/prereg.md, with the factor to ppm.
SUITE: dict[str, float] = {
    "al_pct": 1e4,
    "fe_pct": 1e4,
    "mn_ppm": 1.0,
    "na_pct": 1e4,
    "sc_ppm": 1.0,
    "th_ppm": 1.0,
    "v_ppm": 1.0,
    "ce_ppm": 1.0,
    "la_ppm": 1.0,
    "ti_ppm": 1.0,
}
SUITE_RULE = {"min_nonnull": 0.75, "max_censored": 0.25}
FAMILIES = ["LL", "SR", "OR"]


def load_nure(path) -> pd.DataFrame:
    """Read the extract with identifiers as text and element fields as floats."""
    df = pd.read_csv(
        path,
        dtype={"prime_id": "string", "replc": "string", "laslid": "string", "site": "string"},
        low_memory=False,
    )
    for c in element_columns(df):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def load_mrds(path) -> pd.DataFrame:
    return pd.read_csv(path, dtype={"mrds_id": "string", "mas_id": "string"}, low_memory=False)


def element_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if (c.endswith("_ppm") or c.endswith("_pct")) and c != "orgn_pct"]


def method_family(methods: pd.Series) -> pd.Series:
    m = methods.fillna("NONE").astype(str).str.strip()
    fam = np.select(
        [m.str.startswith("LL"), m.str.startswith("SR"), m.str.startswith("OR")],
        ["LL", "SR", "OR"],
        default="NONE",
    )
    return pd.Series(fam, index=methods.index, name="method_family")


def element_availability(df: pd.DataFrame, elements: list[str] | None = None) -> pd.DataFrame:
    """Per family and element: share non-null, and share of non-null that is censored."""
    elements = elements or element_columns(df)
    rows = []
    for fam, g in df.groupby("method_family"):
        for e in elements:
            v = g[e]
            rows.append(
                {
                    "method_family": fam,
                    "element": e,
                    "n": len(g),
                    "nonnull": float(v.notna().mean()),
                    "censored": censored_fraction(v),
                    "zeros": int((v == 0).sum()),
                }
            )
    return pd.DataFrame(rows)


def suite_rule(avail: pd.DataFrame, families: list[str] = FAMILIES, **rule) -> list[str]:
    """Elements passing the pre-registered availability rule in every family."""
    r = {**SUITE_RULE, **rule}
    a = avail[avail.method_family.isin(families)]
    ok = a.groupby("element").apply(
        lambda t: bool(
            (t.nonnull >= r["min_nonnull"]).all()
            and (t.censored.fillna(1.0) <= r["max_censored"]).all()
            and len(t) == len(families)
        ),
        include_groups=False,
    )
    return sorted(ok[ok].index.tolist())


@dataclass
class ExclusionLog:
    rows: list[dict] = field(default_factory=list)

    def add(self, step: str, before: int, after: int, reason: str) -> None:
        self.rows.append(
            {
                "step": step,
                "rows_before": before,
                "rows_after": after,
                "excluded": before - after,
                "reason": reason,
            }
        )

    def frame(self) -> pd.DataFrame:
        return pd.DataFrame(self.rows)


def population_filters(nure: pd.DataFrame) -> tuple[pd.DataFrame, ExclusionLog]:
    """Pre-registered population filters, before the element-suite filter."""
    log = ExclusionLog()
    df = nure.copy()
    df["method_family"] = method_family(df["methods"])

    n0 = len(df)
    df = df[df["sampsrc"] == "STREAM"]
    log.add("stream_only", n0, len(df), "sampsrc != STREAM (soil, playa, lake, other)")

    n0 = len(df)
    df = df[df["latitude"].notna() & df["longitude"].notna()]
    log.add("coords", n0, len(df), "missing latitude or longitude")

    n0 = len(df)
    df = df[df["method_family"] != "NONE"]
    log.add("methods_none", n0, len(df), "methods == NONE (no analyses in record)")

    n0 = len(df)
    df = df.sort_values("rec_no").drop_duplicates(["doelab", "prime_id"], keep="first")
    log.add(
        "one_record_per_sample",
        n0,
        len(df),
        "additional record for a sample (replicate or second analysis); lowest rec_no kept",
    )
    return df.reset_index(drop=True), log


def apply_suite(df: pd.DataFrame, suite: list[str], log: ExclusionLog) -> pd.DataFrame:
    """Complete-case filter on the suite elements (null or zero excluded)."""
    n0 = len(df)
    complete = df[suite].notna().all(axis=1) & (df[suite] != 0).all(axis=1)
    out = df[complete]
    log.add("complete_suite", n0, len(out), "missing (or zero) value in at least one suite element")
    return out.reset_index(drop=True)


def prepare_samples(nure: pd.DataFrame, suite: list[str]) -> tuple[pd.DataFrame, ExclusionLog]:
    """Apply the pre-registered population filters in order; log every exclusion."""
    df, log = population_filters(nure)
    return apply_suite(df, suite, log), log
