"""Step 10: population filters, element suite, censoring audit, sample table.

Reads data/raw/*, writes data/derived/samples.parquet, data/derived/exclusion_log.csv
and artifacts/tables/element_availability.csv.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from cairn import censored_values, record, recount

from prospectivity.prepare import (
    FAMILIES,
    SUITE,
    SUITE_RULE,
    apply_suite,
    element_availability,
    load_mrds,
    load_nure,
    population_filters,
    suite_rule,
)
from prospectivity.util import commas

ROOT = Path(__file__).resolve().parents[1]
DERIVED = ROOT / "data" / "derived"
TABLES = ROOT / "reports" / "tables"
DERIVED.mkdir(parents=True, exist_ok=True)
TABLES.mkdir(parents=True, exist_ok=True)

nure = load_nure(ROOT / "data/raw/nure_nv_sediment.csv")
mrds = load_mrds(ROOT / "data/raw/mrds_nv.csv")
record("extract.nure_rows", len(nure), n=len(nure))
record("extract.mrds_rows", len(mrds), n=len(mrds))
record("extract.nure_quads", int(nure["quad"].nunique()))

pop, log = population_filters(nure)
steps = {r["step"]: r for r in log.rows}
record("prep.n_sediment_rows", steps["stream_only"]["rows_before"])
record("prep.n_excluded_not_stream", steps["stream_only"]["excluded"])
record("prep.n_excluded_no_coords", steps["coords"]["excluded"])
record("prep.n_excluded_no_methods", steps["methods_none"]["excluded"])
record("prep.n_excluded_extra_records", steps["one_record_per_sample"]["excluded"])
record("prep.n_stream_samples", len(pop), n=len(pop))
recount(nure, pop, "population_filters", expect="fewer")

# Element availability by analytical method family (the pre-registered suite rule)
avail = element_availability(pop)
avail.to_csv(TABLES / "element_availability.csv", index=False)
passing = suite_rule(avail, FAMILIES, **SUITE_RULE)
prereg_suite = sorted(SUITE)
record("prep.suite_elements", commas(e.split("_")[0].capitalize() for e in prereg_suite))
record("prep.n_suite_elements", len(prereg_suite))
record("prep.suite_rule_elements", commas(passing))
record("prep.suite_rule_matches_prereg", bool(passing == prereg_suite))
record("prep.suite_rule_min_nonnull_pct", SUITE_RULE["min_nonnull"] * 100)
record("prep.suite_rule_max_censored_pct", SUITE_RULE["max_censored"] * 100)
for fam in FAMILIES:
    record(f"prep.n_family_{fam}", int((pop["method_family"] == fam).sum()))

samples = apply_suite(pop, prereg_suite, log)
record("prep.n_excluded_incomplete_suite", log.rows[-1]["excluded"])
record("prep.n_samples", len(samples), n=len(samples))
for fam in FAMILIES:
    record(f"prep.n_samples_{fam}", int((samples["method_family"] == fam).sum()))
record("prep.n_samples_quads", int(samples["quad"].nunique()))
record("prep.sampdat_min", str(samples["sampdat"].min()))
record("prep.sampdat_max", str(samples["sampdat"].max()))

# Censoring audit on the final sample population: per element and family.
# NURE codes a censored value as a negative number whose magnitude is the limit;
# cairn's sensor expects '<limit' text, so render it that way for the check.
cens = []
for e in prereg_suite:
    v = samples[e]
    as_text = pd.Series(
        np.where(v < 0, "<" + (-v).astype(str), v.astype(str)), index=v.index, name=e
    )
    censored_values(as_text, name=f"censored_values({e})", quiet=True)
    for fam in FAMILIES:
        vf = samples.loc[samples["method_family"] == fam, e]
        frac = float((vf < 0).mean())
        cens.append(
            {
                "element": e,
                "method_family": fam,
                "n": len(vf),
                "censored_fraction": frac,
                "detection_limit_mode": float((-vf[vf < 0]).mode().iloc[0])
                if (vf < 0).any()
                else np.nan,
            }
        )
        record(
            f"prep.censored_pct.{e.split('_')[0]}.{fam}", round(frac * 100, 2), unit="%", n=len(vf)
        )
cens = pd.DataFrame(cens)
cens.to_csv(TABLES / "censored_fraction_suite.csv", index=False)
worst = cens.sort_values("censored_fraction").iloc[-1]
record("prep.censored_pct_max", round(float(worst.censored_fraction) * 100, 2), unit="%")
record("prep.censored_pct_max_element", worst.element.split("_")[0].capitalize())
record("prep.censored_pct_max_family", worst.method_family)
record(
    "prep.censored_pct_overall",
    round(float((samples[prereg_suite] < 0).to_numpy().mean()) * 100, 2),
    unit="%",
)
record("prep.n_zero_values_suite", int((samples[prereg_suite] == 0).to_numpy().sum()))

keep = [
    "rec_no",
    "prime_id",
    "doelab",
    "method_family",
    "methods",
    "quad",
    "sampdat",
    "sizefrxn",
    "latitude",
    "longitude",
    *prereg_suite,
]
samples[keep].to_parquet(DERIVED / "samples.parquet", index=False)
log.frame().to_csv(DERIVED / "exclusion_log.csv", index=False)
print(log.frame().to_string())
print(f"samples: {len(samples)}; suite rule -> {passing}")
