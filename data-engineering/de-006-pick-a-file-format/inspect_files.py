"""Show the facts behind the issue: the xlsx is a zip, what is inside the Parquet file, and why the first Parquet write fails."""
import zipfile
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

DATA = Path("data")

print("== xlsx is a zip archive; parts and compression type (8 = deflate) ==")
for info in zipfile.ZipFile(DATA / "online_retail_II.xlsx").infolist()[:8]:
    print(f"  {info.filename:32} compress_type={info.compress_type}")

print("\n== Parquet footer ==")
meta = pq.ParquetFile(DATA / "online_retail_II.parquet").metadata
print("  row groups:", [meta.row_group(i).num_rows for i in range(meta.num_row_groups)])
rg = meta.row_group(0)
for j in range(rg.num_columns):
    c = rg.column(j)
    print(f"  {c.path_in_schema:12} {c.compression:7} compressed {c.total_compressed_size:>9,} of {c.total_uncompressed_size:>9,} bytes")
df = pd.read_parquet(DATA / "online_retail_II.parquet")
print("  distinct Country:", df["Country"].nunique(), " distinct InvoiceDate:", df["InvoiceDate"].nunique())

print("\n== why the first Parquet write failed (xlsx read WITHOUT dtype=str) ==")
raw = pd.concat(pd.read_excel(DATA / "online_retail_II.xlsx", sheet_name=None).values(), ignore_index=True)
print("  Invoice cell types:", raw["Invoice"].map(lambda v: type(v).__name__).value_counts().to_dict())
for col in ("Invoice", "Description"):
    try:
        raw[[col]].to_parquet(DATA / "probe.parquet", engine="pyarrow")
        print(f"  {col}: wrote fine")
    except Exception as e:  # show the real error text
        print(f"  {col}: {type(e).__name__}: {str(e)[:90]}")
print("  Description cell types:", raw["Description"].map(lambda v: type(v).__name__).value_counts().to_dict())
(DATA / "probe.parquet").unlink(missing_ok=True)
