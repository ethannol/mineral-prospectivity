"""Compositional transforms, censored substitution and the grid.

All functions are pure numpy/pandas so they can be tested on hand-built
compositions. Concentrations enter in a common unit (ppm); the subcomposition
is closed, then centred log-ratio (CLR) or isometric log-ratio (ILR) coordinates
are computed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

CELL_KM = 5.0
UTM_EPSG = 32611  # WGS84 / UTM zone 11N


# ---------------------------------------------------------------------------
# Censored values
# ---------------------------------------------------------------------------


def censored_to_value(v: pd.Series | np.ndarray, factor: float = 0.5) -> np.ndarray:
    """Turn NURE signed codes into positive concentrations for the transform.

    NURE reports a value below the detection limit as a negative number whose
    absolute value is the limit. ``v > 0`` is kept; ``v < 0`` becomes
    ``factor * |v|`` (a labelled substitution); ``v == 0`` becomes NaN (treated
    as missing: zero is not a measurement in this dataset).
    """
    a = np.asarray(v, dtype=float)
    out = np.where(a > 0, a, np.where(a < 0, -a * factor, np.nan))
    return out


def censored_fraction(v: pd.Series | np.ndarray) -> float:
    """Share of non-null values that are censored (negative)."""
    a = np.asarray(v, dtype=float)
    a = a[~np.isnan(a)]
    return float((a < 0).mean()) if a.size else float("nan")


# ---------------------------------------------------------------------------
# Log-ratio transforms
# ---------------------------------------------------------------------------


def closure(X: np.ndarray) -> np.ndarray:
    X = np.asarray(X, dtype=float)
    if (X <= 0).any() or np.isnan(X).any():
        raise ValueError("closure needs strictly positive, non-missing parts")
    return X / X.sum(axis=1, keepdims=True)


def clr(X: np.ndarray) -> np.ndarray:
    """Centred log-ratio: log of closed parts minus the row geometric mean. Rows sum to 0."""
    L = np.log(closure(X))
    return L - L.mean(axis=1, keepdims=True)


def clr_inverse(Z: np.ndarray) -> np.ndarray:
    """Composition (closed to 1) from CLR coordinates."""
    return closure(np.exp(np.asarray(Z, dtype=float)))


def helmert_basis(D: int) -> np.ndarray:
    """Orthonormal D x (D-1) basis of the CLR hyperplane (columns sum to zero)."""
    V = np.zeros((D, D - 1))
    for i in range(1, D):
        V[:i, i - 1] = 1.0 / i
        V[i, i - 1] = -1.0
        V[:, i - 1] *= np.sqrt(i / (i + 1.0))
    return V


def ilr(X: np.ndarray) -> np.ndarray:
    """Isometric log-ratio coordinates (Helmert basis) of compositions."""
    Z = clr(X)
    return Z @ helmert_basis(Z.shape[1])


def clr_to_ilr(Z: np.ndarray) -> np.ndarray:
    return np.asarray(Z) @ helmert_basis(np.asarray(Z).shape[1])


def ilr_coef_to_clr(beta: np.ndarray, D: int) -> np.ndarray:
    """Map a linear coefficient vector on ILR coordinates to the CLR (per-element) space."""
    return helmert_basis(D) @ np.asarray(beta, dtype=float)


# ---------------------------------------------------------------------------
# Grid
# ---------------------------------------------------------------------------


def project_utm(
    lon: np.ndarray, lat: np.ndarray, epsg: int = UTM_EPSG
) -> tuple[np.ndarray, np.ndarray]:
    """Project WGS84 lon/lat to UTM metres (default zone 11N)."""
    from pyproj import Transformer

    t = Transformer.from_crs("EPSG:4326", f"EPSG:{epsg}", always_xy=True)
    x, y = t.transform(np.asarray(lon, dtype=float), np.asarray(lat, dtype=float))
    return np.asarray(x), np.asarray(y)


def cell_index(x_m: np.ndarray, y_m: np.ndarray, size_km: float = CELL_KM) -> pd.DataFrame:
    """Integer cell indices and centroids for a square grid anchored at (0, 0) metres."""
    s = size_km * 1000.0
    ix = np.floor(np.asarray(x_m) / s).astype(int)
    iy = np.floor(np.asarray(y_m) / s).astype(int)
    return pd.DataFrame(
        {
            "cell_ix": ix,
            "cell_iy": iy,
            "cell_id": [f"{a}_{b}" for a, b in zip(ix, iy, strict=True)],
            "cx_m": (ix + 0.5) * s,
            "cy_m": (iy + 0.5) * s,
        }
    )


def aggregate_cells(samples: pd.DataFrame, clr_cols: list[str]) -> pd.DataFrame:
    """One row per cell: mean CLR vector, sample count, dominant method family and quad.

    The mean of CLR vectors equals the CLR of the geometric-mean composition.
    """
    g = samples.groupby("cell_id", sort=True)
    feats = g[clr_cols].mean()
    meta = g.agg(
        n_samples=("cell_id", "size"),
        cell_ix=("cell_ix", "first"),
        cell_iy=("cell_iy", "first"),
        cx_m=("cx_m", "first"),
        cy_m=("cy_m", "first"),
        lon=("longitude", "mean"),
        lat=("latitude", "mean"),
    )
    fam = g["method_family"].agg(lambda s: s.value_counts().sort_index().idxmax())
    fam_share = g["method_family"].agg(lambda s: float(s.value_counts().iloc[0] / len(s)))
    quad = g["quad"].agg(lambda s: s.value_counts().sort_index().idxmax())
    out = meta.join(feats)
    out["method_family"] = fam
    out["family_share"] = fam_share
    out["quad"] = quad
    return out.reset_index()
