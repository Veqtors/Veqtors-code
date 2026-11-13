# DE-05: a first look at UCI Online Retail II

Two scripts and a ten-row sample. The data stays in `data/`, which `.gitignore` keeps out of Git.

- `fetch_data.py` downloads UCI's zip into `data/`, checks it is whole (`zipfile.testzip`), and unzips `online_retail_II.xlsx`. The server ignores `Range` requests, so a failed download starts again from byte 0.
- `first_look.py` reads both sheets and prints the shape, types, missing values, a documented-versus-measured table, the overlap between the two sheets, and four answers to "how many orders?". `--sample` runs the same report on DE-01's ten rows with no download.
- `sample_rows.py` holds the ten rows.

Data source: UCI Machine Learning Repository, Online Retail II (Daqing Chen, 2012), DOI 10.24432/C5CG6D, licence CC BY 4.0.

## Use it

You need uv (see DE-02). From this folder:

```
uv sync
uv run python first_look.py --sample     # ten rows, a few seconds
uv run python fetch_data.py              # about an hour on a slow server
uv run python first_look.py              # about 35 seconds
```

Tests need no download: `uv run pytest`.

## When it breaks

- The download crawls or stops: the server is slow (measured at about 12 KB/s) and cannot resume. Run `fetch_data.py` again, or download the zip in a browser and unzip it into `data/`.
- The zip check fails: delete `data/online-retail-ii.zip` and download again.
- `first_look.py` says `data/online_retail_II.xlsx` is missing: run `fetch_data.py` first.
- `ModuleNotFoundError`: run `uv sync`.
- Your numbers differ from `RESULTS.md`: check that you read both sheets (`sheet_name=None`). The default reads only the first.
