# DE-06 results (2026-11-20)

Windows 11, Python 3.13.9, pandas 3.1.1, pyarrow 26.0.1. One machine; files warm in the OS cache; reads are best of three.

Ten rows (`uv run python hand_slice.py`): CSV 968 characters, JSON lines 2,097, column lists written out 1,278.

Full table, 1,067,371 rows (`uv run python convert_formats.py`, `uv run python time_reads.py`):

| Format | Size (MB) | Write | Full read | One column (Price) |
|---|---|---|---|---|
| xlsx | 45.6 | | 29.3 to 40.3 s (three logged runs) | |
| CSV | 95.9 | 1.8 to 2.8 s | 0.06 s | 0.08 s |
| JSON lines | 212.2 | 1.8 to 2.4 s | 3.32 s | no column skip |
| Parquet | 7.2 | 0.4 to 0.5 s | 0.04 s | 0.01 s |

Round trip: CSV and JSON lines return InvoiceDate as text; Parquet returns datetime64. Customer ID is float in all three (243,007 missing).

Hand-slice counts (`hand_slice.log`): CSV 968, JSON lines 2,097, columns written out 1,278, columns with runs collapsed 649 characters.
