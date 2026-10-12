"""Summarize recorded buffered predictions; no fitting or primary ledger writes."""

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    output = ROOT / "reports/exploratory/buffered_cv"
    metrics = pd.read_csv(output / "metrics.csv")
    folds = pd.read_csv(output / "folds.csv")
    provenance = json.loads((output / "provenance.json").read_text())
    summary = {"repetitions": provenance["repetitions"], "models": {}}
    lines = [
        "# Recorded exploratory buffered validation",
        "",
        "Matched baseline blocks and grids; distance exclusion in inner and outer folds.",
        "",
        "| Model | Buffer (km) | Mean AUC | Repetition range | Mean training cells removed |",
        "| --- | --- | --- | --- | --- |",
    ]
    for (model, radius), group in metrics.groupby(["model", "buffer_km"]):
        support = folds.loc[(folds.model == model) & (folds.buffer_km == radius)]
        result = dict(
            auc_mean=float(group.auc.mean()),
            auc_min=float(group.auc.min()),
            auc_max=float(group.auc.max()),
            ap_mean=float(group.ap.mean()),
            removed_mean=float(support.n_removed.mean()),
            min_separation_km=float(support.minimum_train_test_km.min()),
        )
        summary["models"].setdefault(model, {})[f"buffer{radius:g}"] = result
        lines.append(
            f"| {model} | {radius:g} | {result['auc_mean']:.3f} | "
            f"{result['auc_min']:.3f} to {result['auc_max']:.3f} | {result['removed_mean']:.1f} |"
        )
    lines += [
        "",
        "The range is variation across matched repetition allocations, not a confidence interval. "
        "Buffers reduce support too; differences cannot be attributed to leakage alone.",
        "",
        "This exploratory sensitivity preserves the frozen primary metrics and decision rule. "
        "The zero-buffer arm uses fewer repetitions than the baseline; compare results "
        "within this matched suite.",
        "",
        f"Recorded source `{provenance['source_revision']}`, seeds from repetition index. "
        "[Methods](buffered-validation.md), "
        "[metrics](../reports/exploratory/buffered_cv/metrics.csv), "
        "[fold attrition and minimum separation](../reports/exploratory/buffered_cv/folds.csv), "
        "[cell predictions](../reports/exploratory/buffered_cv/predictions.csv).",
        "",
    ]
    (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (ROOT / "docs/buffered-results.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
