"""DE-01: count the four problems in the Online Retail II transactions.

Usage: python count_problems.py <file.xlsx|file.csv|file.parquet>
Reads every sheet of an .xlsx and stacks them. Prints a markdown summary.
"""
import sys
from pathlib import Path

import pandas as pd

COLUMNS = {
    "InvoiceNo": "Invoice", "UnitPrice": "Price",
    "CustomerID": "Customer ID", "Customer_ID": "Customer ID",
}


def load(path: str) -> pd.DataFrame:
    p = Path(path)
    if p.suffix == ".xlsx":
        sheets = pd.read_excel(p, sheet_name=None, dtype={"Invoice": str, "StockCode": str})
        df = pd.concat(sheets.values(), ignore_index=True)
    elif p.suffix == ".csv":
        df = pd.read_csv(p, dtype={"Invoice": str, "StockCode": str})
    elif p.suffix in (".parquet", ".pq"):
        df = pd.read_parquet(p)
    else:
        raise ValueError(f"unsupported file type: {p.suffix}")
    return df.rename(columns=COLUMNS)


def count_problems(df: pd.DataFrame) -> dict:
    invoice = df["Invoice"].astype(str)
    stock = df["StockCode"].astype(str)
    dates = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    return {
        "rows": len(df),
        "cancellation_rows (Invoice starts with C)": int(invoice.str.startswith("C").sum()),
        "cancellation_rows (starts with lowercase c)": int(invoice.str.startswith("c").sum()),
        "no_customer_rows": int(df["Customer ID"].isna().sum()),
        "exact_duplicate_extra_copies": int(df.duplicated(keep="first").sum()),
        "price_below_zero": int((df["Price"] < 0).sum()),
        "price_exactly_zero": int((df["Price"] == 0).sum()),
        "unparseable_dates": int(dates.isna().sum()),
        "dates_outside_2009-12-01..2011-12-09": int(
            ((dates < "2009-12-01") | (dates >= "2011-12-10")).sum()),
        "stockcode_not_5_digits": int((~stock.str.fullmatch(r"\d{5}")).sum()),
    }


def row_total(df: pd.DataFrame) -> float:
    return round(float((df["Quantity"] * df["Price"]).sum()), 2)


if __name__ == "__main__":
    data = load(sys.argv[1])
    print("| Count | Value |\n|---|---|")
    for key, value in count_problems(data).items():
        print(f"| {key} | {value:,} |")
    print(f"| naive total (Quantity x Price, all rows) | {row_total(data):,.2f} |")
