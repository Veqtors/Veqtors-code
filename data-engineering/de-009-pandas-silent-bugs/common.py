from pathlib import Path
import pandas as pd

DATA = Path(__file__).parent / "data" / "online_retail_II.parquet"  # DE-06's typed Parquet copy
SLICE = (37895, 37899)  # invoice 492521, five lines, 17 Dec 2009 (row labels of DE-06's frame)


def load(columns=None, path=DATA):
    return pd.read_parquet(path, columns=columns)


def lookup(df):
    """One row per distinct (StockCode, Description) pair, blanks dropped: a product lookup built from the table itself."""
    return df[["StockCode", "Description"]].dropna().drop_duplicates()


def checked_merge(left, right, on, value=None):
    """A left merge that fails loudly if rows (or a total) change, and says why."""
    out = left.merge(right, on=on, how="left", validate="many_to_one")
    assert len(out) == len(left), f"rows {len(left)} -> {len(out)}"
    if value:
        assert abs(out[value].sum() - left[value].sum()) < 0.005, "total moved"
    return out


def expected_rows(left, right, key):
    """Rows a left merge returns: for each left row, the number of right rows with its key (at least 1)."""
    return int(left[key].map(right[key].value_counts()).fillna(1).clip(lower=1).sum())
