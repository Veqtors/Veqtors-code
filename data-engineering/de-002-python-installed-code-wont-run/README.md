# DE-02: a lab that runs, and a script that checks it

`lab_check.py` runs four checks and prints `[ok]` or `[FAIL]` with the reason:

1. Python is 3.11 or newer.
2. You are inside a virtual environment (`sys.prefix` differs from `sys.base_prefix`).
3. `pandas`, `pyarrow`, `openpyxl` and `pytest` are installed.
4. `pytest` passes on the DE-01 tests.

It uses only the standard library, so it runs before you install anything.

## Use it

Install uv once ([official instructions](https://docs.astral.sh/uv/getting-started/installation/)):

```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"   # Windows PowerShell
curl -LsSf https://astral.sh/uv/install.sh | sh                                     # macOS / Linux
```

Copy `lab_check.py` into the DE-01 folder (the one with `pyproject.toml` and
`uv.lock`), then from that folder:

```
uv sync
uv run pytest
uv run python lab_check.py
```

Exit code 0 means every check passed. There is no activation step: `uv run`
runs the command with the project's `.venv`. Never commit `.venv`; do commit `uv.lock`.

## Tests

```
uv run pytest
```

`test_lab_check.py` has six tests for the four checks. They do not need the DE-01 files.

## What was measured, and where

Run on Windows 11 with uv 0.10.0 (see `RESULTS.md`). The macOS and Linux install
line comes from the uv documentation and was not run by the author.
