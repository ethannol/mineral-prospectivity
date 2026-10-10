"""The two pre-registered models, their small fixed grids, and inner selection."""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

LR_GRID: list = [0.01, 0.1, 1.0, 10.0]  # C
HGB_GRID: list = [(0.05, 7), (0.05, 15), (0.1, 7), (0.1, 15)]  # (learning_rate, max_leaf_nodes)
GRIDS = {"lr": LR_GRID, "hgb": HGB_GRID}
HGB_MAX_ITER = 100


def make_model(name: str, cfg, seed: int = 0):
    if name == "lr":
        return make_pipeline(
            StandardScaler(),
            LogisticRegression(C=float(cfg), solver="lbfgs", max_iter=2000),
        )
    if name == "hgb":
        lr, leaves = cfg
        return HistGradientBoostingClassifier(
            learning_rate=lr,
            max_leaf_nodes=leaves,
            max_iter=HGB_MAX_ITER,
            early_stopping=False,
            min_samples_leaf=20,
            l2_regularization=1.0,
            random_state=seed,
        )
    raise ValueError(name)


def select_config(name: str, Xtr: np.ndarray, ytr: np.ndarray, inner: np.ndarray, seed: int):
    """Pick the grid entry with the best mean inner-fold AUC (ties: first entry)."""
    best_cfg, best_score = None, -np.inf
    for cfg in GRIDS[name]:
        scores = []
        for f in np.unique(inner):
            tr, va = inner != f, inner == f
            if len(np.unique(ytr[va])) < 2 or len(np.unique(ytr[tr])) < 2:
                continue
            m = make_model(name, cfg, seed).fit(Xtr[tr], ytr[tr])
            scores.append(roc_auc_score(ytr[va], m.predict_proba(Xtr[va])[:, 1]))
        score = float(np.mean(scores)) if scores else -np.inf
        if score > best_score:
            best_cfg, best_score = cfg, score
    return best_cfg if best_cfg is not None else GRIDS[name][0]


def oof_predictions(
    name: str,
    X: np.ndarray,
    y: np.ndarray,
    folds: np.ndarray,
    inner_fn,
    seed: int = 0,
    test_folds=None,
) -> tuple[np.ndarray, list]:
    """Out-of-fold probabilities with inner selection on the training folds only.

    ``inner_fn(train_idx) -> inner fold array`` encodes the grouping scheme.
    ``test_folds`` restricts which folds are held out (others are train-only;
    their predictions stay NaN). Returns (probabilities aligned with X, chosen
    config per outer fold).
    """
    p = np.full(len(y), np.nan)
    chosen = []
    for f in np.unique(folds) if test_folds is None else list(test_folds):
        tr = np.where(folds != f)[0]
        te = np.where(folds == f)[0]
        cfg = select_config(name, X[tr], y[tr], inner_fn(tr), seed)
        m = make_model(name, cfg, seed).fit(X[tr], y[tr])
        p[te] = m.predict_proba(X[te])[:, 1]
        chosen.append(cfg)
    return p, chosen
