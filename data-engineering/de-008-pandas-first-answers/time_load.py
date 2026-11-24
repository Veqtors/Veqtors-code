"""What does columns= cost? Eight columns against the seven the question needs (best of 3, warm cache)."""
import time
import pandas as pd
from common import DATA, NEEDED

for label, cols in [("all 8 columns", None), ("7 needed columns", NEEDED), ("3 columns (StockCode, Quantity, Price)", ["StockCode", "Quantity", "Price"])]:
    best = 1e9
    for _ in range(3):
        t = time.perf_counter(); d = pd.read_parquet(DATA, columns=cols); best = min(best, time.perf_counter() - t)
    print(f"{label}: {best:.3f} s, {d.memory_usage(deep=True).sum() / 1e6:.0f} MB in memory")
