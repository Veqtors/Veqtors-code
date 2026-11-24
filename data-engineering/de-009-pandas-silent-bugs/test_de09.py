import pandas as pd
import pytest
from pandas.errors import MergeError

from common import SLICE, expected_rows, load, lookup


def test_rule_counts_rows_out():
    left = pd.DataFrame({"k": ["a", "a", "b", "c"]})
    right = pd.DataFrame({"k": ["a", "b", "b", "b"], "v": [1, 2, 3, 4]})
    out = left.merge(right, on="k", how="left")
    assert len(out) == expected_rows(left, right, "k") == 2 * 1 + 1 * 3 + 1  # a: 2x1, b: 1x3, c: unmatched keeps 1 row


def test_validate_turns_fan_out_into_an_error():
    left = pd.DataFrame({"k": ["a"]})
    right = pd.DataFrame({"k": ["a", "a"]})
    with pytest.raises(MergeError):
        left.merge(right, on="k", validate="many_to_one")


def test_cumsum_depends_on_row_order():
    s = pd.Series([10, -5, 20], index=[0, 1, 2])
    assert s.cumsum().tolist() != s.iloc[[2, 0, 1]].cumsum().tolist()


def test_hand_slice_five_lines_become_seven_rows():  # needs data/online_retail_II.parquet (DE-06)
    df = load()
    lines = df.loc[SLICE[0]:SLICE[1], ["StockCode", "Quantity", "Price"]]
    products = lookup(df)
    products = products[products["StockCode"].isin(lines["StockCode"])]
    out = lines.merge(products, on="StockCode", how="left")
    assert (len(lines), len(out)) == (5, 7)
    assert round((out["Quantity"] * out["Price"]).sum(), 2) == 95.2
