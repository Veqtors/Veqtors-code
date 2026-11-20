"""Time a full read and a one-column read per format, then check what each format kept."""
import time
from pathlib import Path

import pandas as pd

DATA = Path("data")
ONE = "Price"

READERS = {
    "csv": (lambda p: pd.read_csv(p), lambda p: pd.read_csv(p, usecols=[ONE])),
    "jsonl": (lambda p: pd.read_json(p, lines=True), None),  # JSON lines has no column skip: every line is parsed
    "parquet": (lambda p: pd.read_parquet(p, engine="pyarrow"), lambda p: pd.read_parquet(p, columns=[ONE], engine="pyarrow")),
}


def timed(fn, path, repeats=3):
    """Best of `repeats`: the file is warm in the OS cache after the first read, so say so when quoting."""
    best = float("inf")
    for _ in range(repeats):
        t = time.perf_counter()
        out = fn(path)
        best = min(best, time.perf_counter() - t)
    return out, best


def main() -> None:
    for ext, (full, one) in READERS.items():
        path = DATA / f"online_retail_II.{ext}"
        df, secs = timed(full, path)
        line = f"{ext:8} full read {secs:6.2f} s"
        if one:
            _, secs1 = timed(one, path)
            line += f"   one column ({ONE}) {secs1:6.2f} s"
        print(line)
        print("         dtypes:", dict(df.dtypes.astype(str)))
        print("         missing Customer ID:", int(df["Customer ID"].isna().sum()))


if __name__ == "__main__":
    main()
