import numpy as np
import pandas as pd
import pytest

from prospectivity.features import (
    aggregate_cells,
    cell_index,
    censored_fraction,
    censored_to_value,
    closure,
    clr,
    clr_inverse,
    clr_to_ilr,
    helmert_basis,
    ilr,
    ilr_coef_to_clr,
)


def test_closure_sums_to_one():
    X = np.array([[1.0, 2.0, 7.0], [5.0, 5.0, 10.0]])
    assert np.allclose(closure(X).sum(axis=1), 1.0)


def test_closure_rejects_nonpositive():
    with pytest.raises(ValueError):
        closure(np.array([[1.0, 0.0, 2.0]]))
    with pytest.raises(ValueError):
        closure(np.array([[1.0, np.nan, 2.0]]))


def test_clr_rows_sum_to_zero_and_is_scale_invariant():
    X = np.array([[1.0, 2.0, 7.0], [0.3, 0.3, 0.4], [100.0, 1.0, 10.0]])
    Z = clr(X)
    assert np.allclose(Z.sum(axis=1), 0.0)
    assert np.allclose(clr(X * 1000.0), Z)


def test_clr_recovers_hand_built_composition():
    comp = np.array([[0.2, 0.3, 0.5]])
    Z = clr(comp)
    # hand computation: log parts minus their mean
    expected = np.log(comp) - np.log(comp).mean()
    assert np.allclose(Z, expected)
    assert np.allclose(clr_inverse(Z), comp)


def test_helmert_basis_orthonormal_and_in_hyperplane():
    V = helmert_basis(10)
    assert V.shape == (10, 9)
    assert np.allclose(V.T @ V, np.eye(9))
    assert np.allclose(V.sum(axis=0), 0.0)


def test_ilr_round_trip_and_coefficient_mapping():
    X = np.array([[1.0, 2.0, 7.0, 4.0], [3.0, 3.0, 3.0, 1.0]])
    Z = clr(X)
    coords = ilr(X)
    assert coords.shape == (2, 3)
    assert np.allclose(clr_to_ilr(Z), coords)
    # distances are preserved (isometry) and CLR is recovered through the basis
    V = helmert_basis(4)
    assert np.allclose(coords @ V.T, Z)
    # a linear score on ILR equals the mapped score on CLR
    beta = np.array([0.5, -1.0, 2.0])
    assert np.allclose(coords @ beta, Z @ ilr_coef_to_clr(beta, 4))


def test_censored_substitution_and_fraction_match_fixture():
    # fixture: 3 detects, 2 censored at limits 2 and 0.5, 1 zero, 1 missing
    v = pd.Series([4.0, 10.0, 1.5, -2.0, -0.5, 0.0, np.nan])
    out = censored_to_value(v, factor=0.5)
    assert np.allclose(out[:5], [4.0, 10.0, 1.5, 1.0, 0.25])
    assert np.isnan(out[5]) and np.isnan(out[6])
    # 2 censored of 6 non-null
    assert censored_fraction(v) == pytest.approx(2 / 6)
    assert np.isnan(censored_fraction(pd.Series([np.nan, np.nan])))


def test_cell_index_and_aggregation_is_mean_of_clr():
    x = np.array([1000.0, 2000.0, 7000.0])
    y = np.array([1000.0, 4000.0, 1000.0])
    ci = cell_index(x, y, size_km=5.0)
    assert ci.cell_id.tolist() == ["0_0", "0_0", "1_0"]
    assert np.allclose(ci.cx_m, [2500.0, 2500.0, 7500.0])
    comp = np.array([[1.0, 2.0, 7.0], [2.0, 2.0, 6.0], [5.0, 1.0, 4.0]])
    Z = clr(comp)
    df = pd.concat(
        [
            ci,
            pd.DataFrame(Z, columns=["clr_a", "clr_b", "clr_c"]),
            pd.DataFrame(
                {
                    "longitude": [-117.0, -117.0, -116.9],
                    "latitude": [39.0, 39.0, 39.1],
                    "method_family": ["LL", "SR", "SR"],
                    "quad": ["RENO", "RENO", "ELY"],
                }
            ),
        ],
        axis=1,
    )
    cells = aggregate_cells(df, ["clr_a", "clr_b", "clr_c"])
    assert len(cells) == 2
    first = cells[cells.cell_id == "0_0"].iloc[0]
    assert np.allclose(first[["clr_a", "clr_b", "clr_c"]].astype(float), Z[:2].mean(axis=0))
    # mean of CLR equals CLR of the geometric-mean composition
    geo = np.exp(np.log(comp[:2]).mean(axis=0, keepdims=True))
    assert np.allclose(first[["clr_a", "clr_b", "clr_c"]].astype(float), clr(geo)[0])
    assert first.n_samples == 2
