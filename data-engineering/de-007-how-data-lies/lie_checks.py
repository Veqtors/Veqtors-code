"""One finding per layer on the full file. Usage: uv run python lie_checks.py [--data PATH] [--sample]"""
import argparse
import math
import time
from decimal import Decimal
from pathlib import Path

import pandas as pd

from sample_rows import sample_frame

DEFAULT = Path("data/online_retail_II.xlsx")
CLOCK_CHANGES = {  # UK local hour that does not exist (spring) or happens twice (autumn); checked with zoneinfo in test_de07.py
    "spring": ["2010-03-28 01:00", "2011-03-27 01:00"],
    "autumn": ["2010-10-31 01:00", "2011-10-30 01:00"],
}


def load(path: Path) -> pd.DataFrame:
    sheets = pd.read_excel(path, sheet_name=None, dtype={"Invoice": str, "StockCode": str, "Description": str})
    return pd.concat(sheets.values(), ignore_index=True)


def layer1_encoding(df: pd.DataFrame) -> dict:
    cols = ["Description", "Country"]
    non_ascii = {c: int(df[c].dropna().map(lambda s: not s.isascii()).sum()) for c in cols}
    desc = df["Description"].dropna()
    distinct_non_ascii = int(desc[~desc.map(str.isascii)].nunique())
    sample = "Â£"  # UCI's page shows the pound sign this way: UTF-8 bytes read as Latin-1
    return {
        "non_ascii_cells": non_ascii,
        "distinct_non_ascii_descriptions": distinct_non_ascii,
        "utf8_bytes_of_pound": "£".encode("utf-8").hex(),
        "those_bytes_read_as_latin1": "£".encode("utf-8").decode("latin-1"),
        "page_text_matches": sample == "£".encode("utf-8").decode("latin-1"),
    }


def layer2_type(df: pd.DataFrame) -> dict:
    cust = df["Customer ID"]
    keyed = df.dropna(subset=["Customer ID"])
    lookup = pd.DataFrame({"Customer ID": keyed["Customer ID"].astype("int64").astype(str).unique()})  # keys as text: "14062"
    float_as_text = keyed.assign(**{"Customer ID": keyed["Customer ID"].astype(str)})  # the quiet bug: "14062.0"
    int_as_text = keyed.assign(**{"Customer ID": keyed["Customer ID"].astype("int64").astype(str)})
    try:
        keyed.merge(lookup, on="Customer ID")
        raw = "merged"
    except ValueError as e:
        raw = f"pandas refuses: {str(e)[:60]}..."
    return {
        "dtype": str(cust.dtype),
        "missing": int(cust.isna().sum()),
        "rows_with_customer": len(keyed),
        "float_column_vs_text_lookup": raw,
        "float_as_text_vs_text_lookup_matched": len(float_as_text.merge(lookup, on="Customer ID")),
        "int_as_text_vs_text_lookup_matched": len(int_as_text.merge(lookup, on="Customer ID")),
        "as_text_of_first_float": str(keyed["Customer ID"].astype(str).iloc[0]),
        "nullable_int_dtype_keeps_gaps": str(cust.astype("Int64").dtype) + f", {int(cust.astype('Int64').isna().sum())} <NA>",
    }


def layer3_absence(df: pd.DataFrame) -> dict:
    desc, price, cust = df["Description"], df["Price"], df["Customer ID"]
    empty = int((desc.dropna().str.strip() == "").sum())
    missing_desc = desc.isna()
    return {
        "missing_customer": int(cust.isna().sum()),
        "missing_description": int(missing_desc.sum()),
        "empty_description_strings": empty,
        "zero_price": int((price == 0).sum()),
        "missing_desc_and_zero_price": int((missing_desc & (price == 0)).sum()),
        "missing_desc_and_no_customer": int((missing_desc & cust.isna()).sum()),
        "mean_price_all_rows": round(float(price.mean()), 4),
        "mean_price_excluding_zero": round(float(price[price > 0].mean()), 4),
        "rows_price_positive": int((price > 0).sum()),
    }


def layer4_time(df: pd.DataFrame) -> dict:
    t = df["InvoiceDate"]
    out = {"tz": str(t.dt.tz), "missing_invoice_dates": int(t.isna().sum()), "min": str(t.min()), "max": str(t.max()), "stored_hours": f"{t.dt.hour.min()} to {t.dt.hour.max()}"}
    for kind, starts in CLOCK_CHANGES.items():
        for s in starts:
            lo = pd.Timestamp(s)
            out[f"{kind}_{s[:10]}_rows_in_01:00-02:00"] = int(((t >= lo) & (t < lo + pd.Timedelta(hours=1))).sum())
    local = t.dt.tz_localize("Europe/London", nonexistent="NaT", ambiguous="NaT")
    out["rows_that_cannot_be_uk_local_time_nonexistent"] = int(local.isna().sum() - t.isna().sum())
    return out


def layer5_money(df: pd.DataFrame) -> dict:
    q, p = df["Quantity"], df["Price"]
    t = time.perf_counter()
    float_total = float((q * p).sum())
    t_float = time.perf_counter() - t
    t = time.perf_counter()
    exact = sum(Decimal(int(a)) * Decimal(repr(float(b))) for a, b in zip(q, p))  # repr gives the shortest text that round-trips
    t_dec = time.perf_counter() - t
    pennies = sum(int(a) * round(float(b) * 100) for a, b in zip(q, p))  # integer pence (prices have at most 2 decimals?)
    more_than_2dp = int(((p * 100 - (p * 100).round()).abs() > 1e-9).sum())
    return {
        "float_sum_numpy": round(float_total, 6),
        "fsum_correctly_rounded": round(math.fsum((q * p).tolist()), 6),
        "exact_decimal_sum": str(exact),
        "difference_float_minus_exact": float(Decimal(float_total) - exact),  # Decimal(float) is the float's exact binary value
        "integer_pence_sum": pennies / 100,
        "prices_with_more_than_2_decimals": more_than_2dp,
        "seconds_float_vs_decimal": (round(t_float, 3), round(t_dec, 3)),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=DEFAULT)
    ap.add_argument("--sample", action="store_true", help="run on DE-01's ten rows, no download")
    args = ap.parse_args()
    if args.sample:
        df = sample_frame()
    elif not args.data.exists():
        raise SystemExit(f"{args.data} is missing: run DE-05's fetch_data.py or pass --data.")
    else:
        df = load(args.data)
    for name, fn in (("1 bytes -> characters", layer1_encoding), ("2 characters -> type", layer2_type),
                     ("3 absence", layer3_absence), ("4 date -> moment", layer4_time), ("5 number -> money", layer5_money)):
        print(f"\n{name}")
        for k, v in fn(df).items():
            print(f"  {k:48} {v}")


if __name__ == "__main__":
    main()
