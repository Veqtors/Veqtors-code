# DE-06: the same table in four files

Converts DE-05's workbook to CSV, JSON lines and Parquet and measures size and read time. Data stays in `data/` (ignored by Git).

- `hand_slice.py`: DE-01's ten rows as CSV, JSON lines and column lists, with character counts. No download.
- `convert_formats.py`: reads the xlsx once (both sheets), writes the three files, prints sizes and write times.
- `inspect_files.py`: the xlsx zip listing, the Parquet footer and the two write errors.
- `check_csv_timing.py`: cross-checks the CSV read time.
- `time_reads.py`: full read and one-column read per format, plus dtypes and missing Customer IDs.
- `fetch_data.py` (from DE-05): downloads the xlsx if you do not have it.
- `sample_rows.py`: the ten rows. `test_de06.py`: tests on them.

```
uv sync
uv run python hand_slice.py          # seconds, no download
uv run python fetch_data.py          # about 40 minutes to an hour, only once
uv run python convert_formats.py     # about 45 seconds
uv run python time_reads.py
uv run pytest
```

## When it breaks

- `data/online_retail_II.xlsx is missing`: run `fetch_data.py` (or copy the file from DE-05's `data/`).
- `ArrowInvalid` or `ArrowTypeError` writing Parquet: a column mixes types. `convert_formats.py` reads Invoice, StockCode and Description as text for this reason (the workbook has integer cells in all three).
- `ModuleNotFoundError: pyarrow`: run `uv sync`.
- Out of memory: the xlsx read needs about 0.6 GB (DE-05).
- Your timings differ from `RESULTS.md`: expected; read times depend on the machine and the disk cache.
