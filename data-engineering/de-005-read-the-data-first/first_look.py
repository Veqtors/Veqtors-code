"""DE-05: a first look at the Online Retail II file.

    uv run python first_look.py --sample   # DE-01's ten rows, no download needed
    uv run python first_look.py            # the full official file in data/
"""
import sys
import time
from pathlib import Path

import pandas as pd

from sample_rows import sample_frame

XLSX = Path("data") / "online_retail_II.xlsx"


def load_sheets(path: Path) -> dict:
    """Read every sheet. sheet_name=None is what reads them all; the default reads only the first."""
    sheets = pd.read_excel(
        path, sheet_name=None, engine="openpyxl", dtype={"Invoice": str, "StockCode": str}
    )
    for name, frame in sheets.items():
        print(f"  sheet {name!r}: {len(frame):,} rows")
    return sheets


def sheet_overlap(first: pd.DataFrame, second: pd.DataFrame) -> dict:
    """The two sheets are meant to be consecutive years. Do they share any dates or rows?"""
    start, end = second["InvoiceDate"].min(), first["InvoiceDate"].max()
    return {
        "dates in both sheets": f"{start:%Y-%m-%d} to {end:%Y-%m-%d}" if start <= end else "none",
        "sheet 1 rows in that window": int((first["InvoiceDate"] >= start).sum()),
        "sheet 2 rows in that window": int((second["InvoiceDate"] <= end).sum()),
        "exact repeats inside each sheet": int(first.duplicated().sum() + second.duplicated().sum()),
        "exact repeats once stacked": int(pd.concat([first, second], ignore_index=True).duplicated().sum()),
    }


def order_counts(df: pd.DataFrame) -> dict:
    invoice = df["Invoice"].astype(str)
    return {
        "rows": len(df),
        "distinct invoices": int(invoice.nunique()),
        "distinct invoices not starting with C": int(invoice[~invoice.str.startswith("C")].nunique()),
        "...and with at least one sold line": int(
            invoice[~invoice.str.startswith("C") & (df["Quantity"] > 0) & (df["Price"] > 0)].nunique()
        ),
    }


def documented_vs_measured(df: pd.DataFrame) -> dict:
    """UCI documents a 6-digit invoice (lowercase c marks a cancellation) and a 5-digit stock code."""
    invoice = df["Invoice"].astype(str)
    stock = df["StockCode"].astype(str)
    return {
        "invoice is 6 digits": int(invoice.str.fullmatch(r"\d{6}").sum()),
        "invoice is C + 6 digits (uppercase)": int(invoice.str.fullmatch(r"C\d{6}").sum()),
        "invoice is c + 6 digits (lowercase, as documented)": int(invoice.str.fullmatch(r"c\d{6}").sum()),
        "invoice is anything else": int((~invoice.str.fullmatch(r"[Cc]?\d{6}")).sum()),
        "stock code is not 5 digits": int((~stock.str.fullmatch(r"\d{5}")).sum()),
        "rows with no Customer ID": int(df["Customer ID"].isna().sum()),
    }


def report(df: pd.DataFrame) -> None:
    print(f"\nshape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print("\ncolumn types and missing values:")
    for column in df.columns:
        print(f"  {column:<12} {str(df[column].dtype):<16} missing {int(df[column].isna().sum()):>8,}")
    print("\ndocumented vs measured:")
    for label, value in documented_vs_measured(df).items():
        print(f"  {label:<52} {value:>9,}")
    print("\nhow many orders?")
    for label, value in order_counts(df).items():
        print(f"  {label:<40} {value:>9,}")


def main(argv) -> int:
    if "--sample" in argv:
        report(sample_frame())
        return 0
    if not XLSX.exists():
        print(f"[FAIL] {XLSX} is missing. Run: uv run python fetch_data.py")
        return 1
    started = time.perf_counter()
    sheets = load_sheets(XLSX)
    print(f"read both sheets in {time.perf_counter() - started:.0f} s")
    first, second = list(sheets.values())[:2]
    print("\nthe two sheets:")
    for label, value in sheet_overlap(first, second).items():
        print(f"  {label:<36} {value:>22}" if isinstance(value, str) else f"  {label:<36} {value:>22,}")
    report(pd.concat(sheets.values(), ignore_index=True))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
