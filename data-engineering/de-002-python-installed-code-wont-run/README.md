# DE-02: a lab that runs, and a script that checks it

`lab_check.py` runs four checks and prints `[ok]` or `[FAIL]` with the reason:

1. Python is 3.11 or newer.
2. You are inside a virtual environment (`sys.prefix` differs from `sys.base_prefix`).
3. `pandas`, `pyarrow`, `openpyxl` and `pytest` are installed.
4. `python -m pytest` passes.

It uses only the standard library, so it runs before you install anything.

## Use it

Put `lab_check.py` in the folder that holds the DE-01 files (`count_problems.py`,
`test_count_problems.py`, `requirements.txt`), then:

```
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
source .venv/bin/activate           # macOS / Linux
python -m pip install -r requirements.txt
python lab_check.py
```

Exit code 0 means every check passed. Never commit `.venv`.

## Tests

```
python -m pytest
```

`test_lab_check.py` has six tests for the four checks. They do not need the DE-01 files.

## What was measured, and where

Run on Windows 11, Windows PowerShell 5.1, Python 3.14.0, pandas 3.1.1, pytest 9.2.0
(see `RESULTS.md`). The macOS and Linux commands come from the Python documentation and were
not run by the author. `python -m pip` is the same installer as `pip`; the `python -m` form
guarantees it belongs to the Python you are looking at.
