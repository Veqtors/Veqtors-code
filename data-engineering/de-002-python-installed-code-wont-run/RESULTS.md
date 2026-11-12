# DE-02 results (measured 2026-11-12, Windows 11, uv 0.10.0)

Throwaway folder holding the DE-01 files plus `lab_check.py`.

## Building the project

| Step | Result |
|---|---|
| `uv init --bare`, `uv python pin 3.13` | `pyproject.toml` and `.python-version` written |
| `uv run python count_problems.py ...` before any dependency was added | `ModuleNotFoundError: No module named 'pandas'` (the project's `.venv` held no packages) |
| `uv add "pandas>=2.2" "pyarrow>=15" "openpyxl>=3.1"` and `uv add --dev "pytest>=8"`, empty cache | Prepared 7 packages in 13.06 s, installed in 715 ms (first call); `uv.lock` written |
| `uv run pytest` | `2 passed in 2.92s` |

## The reader's path: a new folder, an empty cache, no Python visible to uv

Isolated with `UV_CACHE_DIR`, `UV_PYTHON_INSTALL_DIR` and `UV_PYTHON_PREFERENCE=only-managed`.

| Step | Result |
|---|---|
| `uv sync` | Downloaded CPython 3.13.12 (20.7 MiB) and installed 13 packages: **17.7 s** wall clock. pandas 3.1.1, pyarrow 26.0.1, openpyxl 3.1.5, pytest 9.2.0 |
| `uv run python -c "import sys; print(sys.executable)"` | `...\reader\.venv\Scripts\python.exe`, Python 3.13.12 |
| `uv run pytest` | `2 passed in 2.90s` |
| Delete `.venv`, `uv sync` again (warm cache) | 1.5 s |

`uv run python lab_check.py` (exit code 0):

```
[ok] python: Python 3.13 (needs 3.11 or newer)
[ok] environment: running inside a virtual environment: ...\reader\.venv
[ok] packages: pandas 3.1.1, pyarrow 26.0.1, openpyxl 3.1.5, pytest 9.2.0
[ok] tests: pytest: 2 passed in 0.58s
```

The same script run with the system Python, `C:\Python314\python.exe lab_check.py` (exit code 1):

```
[ok] python: Python 3.14 (needs 3.11 or newer)
[FAIL] environment: not inside a virtual environment: sys.prefix is the system Python (start it with: uv run python lab_check.py)
[FAIL] packages: missing: pyarrow (run: uv sync)
[ok] tests: pytest: 2 passed in 0.58s
```

The system Python had pandas 3.0.2 and pytest but no pyarrow: a shared install
that happens to half-work.

## Earlier measurement (pip and venv, other machine, superseded)

`python -m pip install -r requirements.txt` took 653 s on a slow connection
(Python 3.14.0, same package versions). Kept for comparison only; the issue no
longer teaches pip.

Not measured: macOS, Linux, the full DE-01 script on pandas 3.1.1.
