import numpy as np
import pandas as pd
import pytest
from scipy.ndimage import gaussian_filter

from prospectivity.cv import (
    block_folds,
    block_ids,
    calibration_table,
    capture,
    check_folds,
    deal_groups_to_folds,
    evaluate,
    first_lag_below,
    group_folds,
    inner_folds,
    moran_correlogram,
    random_folds,
    reference_block_size,
)
from prospectivity.models import oof_predictions


def _grid(n=40, cell_m=2000.0):
    ix, iy = np.meshgrid(np.arange(n), np.arange(n), indexing="ij")
    x = (ix.ravel() + 0.5) * cell_m
    y = (iy.ravel() + 0.5) * cell_m
    return x, y


def test_block_assignment_no_overlap_contiguous_and_sized():
    x, y = _grid(40)  # 80 km square of 2 km cells
    folds, blocks = block_folds(x, y, block_km=10, k=5, seed=3)
    check_folds(folds, blocks)
    for f in range(5):
        assert not set(np.where(folds == f)[0]) & set(np.where(folds != f)[0])
    # every block is contiguous and no larger than 10 km on a side
    df = pd.DataFrame({"b": blocks, "x": x, "y": y})
    ext = df.groupby("b").agg(x0=("x", "min"), x1=("x", "max"), y0=("y", "min"), y1=("y", "max"))
    assert ((ext.x1 - ext.x0) <= 10_000 - 2000 + 1e-6).all()
    assert ((ext.y1 - ext.y0) <= 10_000 - 2000 + 1e-6).all()
    # a block never spans two folds
    assert (df.assign(f=folds).groupby("b").f.nunique() == 1).all()
    # the offset changes with the seed
    _, b2 = block_folds(x, y, block_km=10, k=5, seed=4)
    assert not np.array_equal(blocks, b2)


def test_block_ids_cover_units_in_consistent_squares():
    x = np.array([0.0, 4_999.0, 5_001.0, 10_000.0])
    y = np.zeros(4)
    b = block_ids(x, y, block_km=5, offset_x_m=0.0, offset_y_m=0.0)
    assert b[0] == b[1] and b[1] != b[2] and b[2] != b[3]


def test_deal_groups_round_robin_balances_counts():
    g = np.repeat(np.arange(12), 3)
    f = deal_groups_to_folds(g, 4, np.random.default_rng(0))
    assert sorted(np.bincount(f).tolist()) == [9, 9, 9, 9]


def test_random_group_and_inner_folds():
    y = np.array([0] * 90 + [1] * 10)
    f = random_folds(y, 5, 0)
    assert np.bincount(f).tolist() == [20] * 5
    assert all(y[f == k].sum() == 2 for k in range(5))
    gf, names = group_folds(np.array(["b", "a", "b", "c"]))
    assert names == ["a", "b", "c"] and gf.tolist() == [1, 0, 1, 2]
    inner = inner_folds("group", np.arange(4), y[:4], np.array([0, 0, 1, 2]), k=3, seed=0)
    assert inner[0] == inner[1]


def test_capture_curve_hand_computed():
    # 10 units, 3 positives; ranked by p the positives sit at ranks 1, 4 and 9
    p = np.array([0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.05])
    y = np.array([1, 0, 0, 1, 0, 0, 0, 0, 1, 0])
    assert capture(y, p, 0.10) == pytest.approx(1 / 3)  # top 1 unit
    assert capture(y, p, 0.40) == pytest.approx(2 / 3)  # top 4 units
    assert capture(y, p, 0.90) == pytest.approx(3 / 3)  # top 9 units
    m = evaluate(y, p)
    assert m["capture_10"] == pytest.approx(1 / 3) and m["capture_20"] == pytest.approx(1 / 3)
    assert 0.0 < m["auc"] < 1.0 and m["base_rate"] == pytest.approx(0.3)
    t = calibration_table(y, p, n_bins=2)
    assert t.n.tolist() == [5, 5]


def test_moran_correlogram_signs():
    x, y = _grid(20, 1000.0)
    ix = (x / 1000.0 - 0.5).astype(int)
    iy = (y / 1000.0 - 0.5).astype(int)
    checker = ((ix + iy) % 2).astype(float)
    smooth = (ix + iy).astype(float)
    edges = np.array([0.0, 1001.0, 2001.0])
    c1 = moran_correlogram(x, y, checker, edges)
    c2 = moran_correlogram(x, y, smooth, edges)
    assert c1.moran_i.iloc[0] < -0.9  # neighbours always opposite
    assert c2.moran_i.iloc[0] > 0.9  # neighbours always similar
    assert c1.n_pairs.iloc[0] == 2 * (2 * 20 * 19)  # ordered 4-neighbour pairs
    assert first_lag_below(c2, 0.05) is None
    assert first_lag_below(c1, 0.05) == 1001.0
    assert reference_block_size(None, [5, 10, 25]) == 25
    assert reference_block_size(12_000.0, [5, 10, 25]) == 25
    assert reference_block_size(10_000.0, [5, 10, 25]) == 10


def test_synthetic_leakage_random_cv_shows_skill_block_cv_does_not():
    """A smooth field unrelated to a smooth target still scores under random CV."""
    n = 40  # 80 km square of 2 km cells
    rng = np.random.default_rng(7)
    sigma = 3.0  # correlation range about 3 sigma = 9 cells = 18 km
    target_field = gaussian_filter(rng.normal(size=(n, n)), sigma)
    feat_fields = [gaussian_filter(rng.normal(size=(n, n)), sigma) for _ in range(3)]
    y = (target_field > np.quantile(target_field, 0.8)).astype(int).ravel()
    X = np.column_stack([f.ravel() for f in feat_fields])
    x_m, y_m = _grid(n)
    # random stratified 5-fold
    f_r = random_folds(y, 5, 0)
    p_r, _ = oof_predictions(
        "hgb", X, y, f_r, lambda tr: inner_folds("random", tr, y, None, 3, 0), seed=0
    )
    # blocks of 40 km, above the correlation range
    f_b, blocks = block_folds(x_m, y_m, block_km=40, k=4, seed=0)
    p_b, _ = oof_predictions(
        "hgb", X, y, f_b, lambda tr: inner_folds("group", tr, y, blocks, 3, 0), seed=0
    )
    auc_r = evaluate(y, p_r)["auc"]
    auc_b = evaluate(y, p_b)["auc"]
    assert auc_r > 0.65, auc_r
    assert auc_b < 0.58, auc_b
