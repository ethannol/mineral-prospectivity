import pandas as pd
import pytest

from prospectivity.labels import (
    classify_sites,
    label_cells,
    planted_duplicate_check,
    site_counts_per_cell,
)


@pytest.fixture(autouse=True)
def _checks_to_tmp(tmp_path, monkeypatch):
    # cairn checks append to artifacts/checks.jsonl; keep tests out of the project log
    monkeypatch.setenv("CAIRN_CHECKS", str(tmp_path / "checks.jsonl"))
    monkeypatch.setenv("CAIRN_LEDGER", str(tmp_path / "numbers.json"))
    yield


def _sites():
    return pd.DataFrame(
        {
            "dep_id": [1, 2, 3, 4, 5, 6],
            "commod1": [
                "Gold",
                "Silver, Gold",
                "Copper",
                "Gold",
                "Sand and Gravel, Construction",
                "Goldfield Clay",
            ],
            "commod2": [None, None, "Gold", None, None, None],
            "commod3": [None, None, None, None, None, None],
            "dev_stat": [
                "Past Producer",
                "Producer",
                "Producer",
                "Prospect",
                "Producer",
                "Producer",
            ],
            "cell_id": ["0_0", "0_0", "1_0", "2_0", "3_0", "3_0"],
        }
    )


def test_classify_sites_whole_word_and_status():
    s = classify_sites(_sites())
    assert s.is_positive.tolist() == [True, True, False, False, False, False]
    # copper mine with by-product gold and the gold prospect are ambiguous; "Goldfield" is not gold
    assert s.is_ambiguous.tolist() == [False, False, True, True, False, False]


def test_join_does_not_multiply_rows_and_zero_fills():
    s = classify_sites(_sites())
    cells = pd.DataFrame(
        {"cell_id": ["0_0", "1_0", "2_0", "3_0", "9_9"], "f": [1.0, 2.0, 3.0, 4.0, 5.0]}
    )
    out = label_cells(cells, site_counts_per_cell(s))
    assert len(out) == len(cells)
    assert out.set_index("cell_id").loc["0_0", "n_positive_sites"] == 2
    assert out.set_index("cell_id").loc["9_9", "n_positive_sites"] == 0
    assert out.label.tolist() == [1, 0, 0, 0, 0]
    assert out.ambiguous.tolist() == [False, True, True, False, False]


def test_planted_duplicate_site_does_not_create_two_positives():
    s = classify_sites(_sites())
    cells = pd.DataFrame({"cell_id": ["0_0", "1_0", "2_0", "3_0"]})
    assert planted_duplicate_check(s, cells)
    dup = pd.concat([s, s.iloc[[0]]], ignore_index=True)  # same site twice
    out = label_cells(cells, site_counts_per_cell(dup))
    assert int(out.label.sum()) == 1


def test_duplicate_cell_rows_are_refused():
    s = classify_sites(_sites())
    cells = pd.DataFrame({"cell_id": ["0_0", "0_0"]})
    with pytest.raises(ValueError):
        label_cells(cells, site_counts_per_cell(s))
