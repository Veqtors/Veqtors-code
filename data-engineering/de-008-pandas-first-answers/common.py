from pathlib import Path
import pandas as pd

DATA = Path(__file__).parent / "data" / "online_retail_II.parquet"  # DE-06's Parquet copy
NEEDED = ["Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Country"]
SLICE = (554733, 554742)  # ten consecutive rows, 14 Dec 2010 (row labels of DE-06's frame)


def load(columns=None, path=DATA):
    return pd.read_parquet(path, columns=columns)


def december_uk(df):
    in_dec = (df["InvoiceDate"] >= "2010-12-01") & (df["InvoiceDate"] < "2011-01-01")
    return df[in_dec & (df["Country"] == "United Kingdom")]


def top_five(df):
    revenue = (df["Quantity"] * df["Price"]).rename("revenue")
    return (
        df.assign(revenue=revenue)
        .groupby(["StockCode", "Description"], as_index=False)["revenue"].sum()
        .sort_values("revenue", ascending=False)
        .head(5)
    )
