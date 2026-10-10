"""Cross-validation schemes, spatial autocorrelation and ranking metrics.

Every fold assignment is an integer array aligned with the unit table. Block
folds are built from a square block grid with a random offset; blocks are dealt
to folds by a random permutation so every unit in a block is in one fold.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold

BLOCK_SIZES_KM = [5, 10, 25, 50, 100]
CAPTURE_FRACTIONS = [0.01, 0.05, 0.10, 0.20]


# ---------------------------------------------------------------------------
# Fold assignment
# ---------------------------------------------------------------------------


def block_ids(
    x_m: np.ndarray,
    y_m: np.ndarray,
    block_km: float,
    offset_x_m: float = 0.0,
    offset_y_m: float = 0.0,
) -> np.ndarray:
    """Integer block id per unit for a square grid of side ``block_km`` with an offset."""
    s = block_km * 1000.0
    bx = np.floor((np.asarray(x_m) - offset_x_m) / s).astype(np.int64)
    by = np.floor((np.asarray(y_m) - offset_y_m) / s).astype(np.int64)
    codes, _ = pd.factorize(pd.Series(list(zip(bx.tolist(), by.tolist(), strict=True))))
    return codes.astype(int)


def deal_groups_to_folds(groups: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    """Randomly permute the distinct groups and deal them round-robin into ``k`` folds."""
    uniq = np.unique(groups)
    perm = rng.permutation(uniq)
    fold_of = {g: i % k for i, g in enumerate(perm)}
    return np.array([fold_of[g] for g in groups], dtype=int)


def block_folds(
    x_m: np.ndarray, y_m: np.ndarray, block_km: float, k: int, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """Spatial block folds: random grid offset in [0, block) and random block allocation.

    Returns (fold per unit, block id per unit).
    """
    rng = np.random.default_rng(seed)
    s = block_km * 1000.0
    ox, oy = rng.uniform(0.0, s, size=2)
    b = block_ids(x_m, y_m, block_km, ox, oy)
    return deal_groups_to_folds(b, k, rng), b


def random_folds(y: np.ndarray, k: int, seed: int) -> np.ndarray:
    folds = np.empty(len(y), dtype=int)
    for i, (_, te) in enumerate(StratifiedKFold(k, shuffle=True, random_state=seed).split(y, y)):
        folds[te] = i
    return folds


def group_folds(groups: pd.Series | np.ndarray) -> tuple[np.ndarray, list]:
    """Leave-one-group-out: one fold per distinct group. Returns (folds, group names)."""
    codes, names = pd.factorize(pd.Series(np.asarray(groups)), sort=True)
    return codes.astype(int), list(names)


def inner_folds(
    scheme: str, idx: np.ndarray, y: np.ndarray, groups: np.ndarray | None, k: int, seed: int
) -> np.ndarray:
    """Fold assignment for the training subset ``idx`` under the same grouping scheme.

    ``scheme`` is "random" (stratified) or "group" (blocks or categorical groups,
    dealt randomly into ``k`` folds; ``k`` is capped at the number of groups).
    """
    rng = np.random.default_rng(seed + 1_000_003)
    if scheme == "random":
        return random_folds(y[idx], k, seed + 7)
    g = np.asarray(groups)[idx]
    kk = min(k, len(np.unique(g)))
    return deal_groups_to_folds(g, kk, rng)


def check_folds(folds: np.ndarray, groups: np.ndarray | None = None) -> None:
    """Every unit in exactly one fold; a group never spans two folds."""
    if (folds < 0).any():
        raise ValueError("unassigned units")
    if groups is not None:
        t = pd.DataFrame({"g": np.asarray(groups), "f": folds}).groupby("g")["f"].nunique()
        if (t > 1).any():
            raise ValueError("a group appears in more than one fold")


# ---------------------------------------------------------------------------
# Spatial autocorrelation
# ---------------------------------------------------------------------------


def moran_correlogram(
    x_m: np.ndarray, y_m: np.ndarray, z: np.ndarray, edges_m: np.ndarray, chunk: int = 1000
) -> pd.DataFrame:
    """Moran's I of ``z`` for pairs whose distance falls in each (lo, hi] bin.

    Binary weights within the bin; self-pairs excluded. I = (n / n_pairs) *
    sum_{pairs} z_i z_j / sum z_i^2 with z centred. Computed in row chunks so the
    full distance matrix is never held in memory.
    """
    x = np.asarray(x_m, float)
    y = np.asarray(y_m, float)
    zc = np.asarray(z, float) - np.mean(z)
    n = len(zc)
    denom = float((zc**2).sum())
    edges = np.asarray(edges_m, float)
    nb = len(edges) - 1
    num = np.zeros(nb)
    cnt = np.zeros(nb, dtype=np.int64)
    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        d = np.sqrt((x[s:e, None] - x[None, :]) ** 2 + (y[s:e, None] - y[None, :]) ** 2)
        prod = zc[s:e, None] * zc[None, :]
        idx = np.arange(s, e)
        d[idx - s, idx] = -1.0  # exclude self pairs from every bin
        which = np.searchsorted(edges, d, side="left") - 1  # bin index, -1 below lo
        valid = (which >= 0) & (which < nb) & (d > edges[0])
        num += np.bincount(which[valid], weights=prod[valid], minlength=nb)
        cnt += np.bincount(which[valid], minlength=nb)
    with np.errstate(invalid="ignore", divide="ignore"):
        moran = (n / cnt) * (num / denom)
    return pd.DataFrame({"lo_m": edges[:-1], "hi_m": edges[1:], "n_pairs": cnt, "moran_i": moran})


def first_lag_below(corr: pd.DataFrame, threshold: float) -> float | None:
    """Upper edge (m) of the first bin whose Moran's I is below ``threshold``."""
    below = corr[corr["moran_i"] < threshold]
    return float(below["hi_m"].iloc[0]) if len(below) else None


def reference_block_size(range_m: float | None, sizes_km: list[float]) -> float:
    """Smallest block size at or above the range; the largest size if none."""
    if range_m is None:
        return float(max(sizes_km))
    for s in sorted(sizes_km):
        if s * 1000.0 >= range_m:
            return float(s)
    return float(max(sizes_km))


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def capture(y: np.ndarray, p: np.ndarray, frac: float) -> float:
    """Share of positives among the top ``frac`` of units ranked by ``p`` (stable ties)."""
    y = np.asarray(y)
    p = np.asarray(p)
    n_top = int(np.ceil(frac * len(p)))
    order = np.argsort(-p, kind="stable")
    top = order[:n_top]
    return float(y[top].sum() / max(y.sum(), 1))


def calibration_table(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    df = pd.DataFrame({"y": np.asarray(y), "p": np.asarray(p)})
    df["bin"] = pd.qcut(df["p"].rank(method="first"), n_bins, labels=False)
    t = df.groupby("bin").agg(n=("y", "size"), mean_pred=("p", "mean"), obs_rate=("y", "mean"))
    return t.reset_index()


def evaluate(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    y = np.asarray(y)
    p = np.asarray(p)
    out = {
        "auc": float(roc_auc_score(y, p)),
        "ap": float(average_precision_score(y, p)),
        "brier": float(np.mean((p - y) ** 2)),
        "base_rate": float(y.mean()),
    }
    for f in CAPTURE_FRACTIONS:
        out[f"capture_{int(round(f * 100))}"] = capture(y, p, f)
    return out
