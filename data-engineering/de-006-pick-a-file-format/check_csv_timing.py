"""Cross-check the CSV read time: two engines, and a fresh Python process for the whole run."""
import subprocess
import sys
import time

import pandas as pd

PATH = "data/online_retail_II.csv"

for engine in ("c", "pyarrow"):
    t = time.perf_counter()
    df = pd.read_csv(PATH, engine=engine)
    print(f"read_csv engine={engine:8} {time.perf_counter() - t:5.2f} s  {len(df):,} rows")

t = time.perf_counter()
subprocess.run([sys.executable, "-c", f"import pandas as pd; pd.read_csv('{PATH}')"], check=True)
print(f"fresh process (start-up + pandas import + read) {time.perf_counter() - t:5.2f} s")
