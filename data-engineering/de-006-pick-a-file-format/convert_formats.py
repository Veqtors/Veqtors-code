"""Read the official xlsx once, write CSV, JSON lines and Parquet to data/, print sizes and write times."""
import time
from pathlib import Path

import pandas as pd

DATA = Path("data")
XLSX = DATA / "online_retail_II.xlsx"


def read_xlsx(path: Path = XLSX) -> pd.DataFrame:
    # sheet_name=None reads both sheets; the default reads only the first (see DE-05)
    # Invoice and StockCode mix int and str cells in the xlsx (DE-05); 4 Description cells are numbers too; declare all three as text
    sheets = pd.read_excel(path, sheet_name=None, dtype={"Invoice": str, "StockCode": str, "Description": str})
    return pd.concat(sheets.values(), ignore_index=True)


WRITERS = {
    "csv": lambda df, p: df.to_csv(p, index=False),
    "jsonl": lambda df, p: df.to_json(p, orient="records", lines=True, date_format="iso"),
    "parquet": lambda df, p: df.to_parquet(p, engine="pyarrow", index=False),
}


def main() -> None:
    if not XLSX.exists():
        raise SystemExit("data/online_retail_II.xlsx is missing: run fetch_data.py first.")
    t = time.perf_counter()
    df = read_xlsx()
    print(f"xlsx   {XLSX.stat().st_size / 1e6:8.1f} MB   read {time.perf_counter() - t:5.1f} s   {len(df):,} rows")
    for ext, write in WRITERS.items():
        path = DATA / f"online_retail_II.{ext}"
        t = time.perf_counter()
        write(df, path)
        print(f"{ext:6} {path.stat().st_size / 1e6:8.1f} MB   write {time.perf_counter() - t:5.1f} s")


if __name__ == "__main__":
    main()
