# DE-02 results (measured 2026-11-12, Windows 11, PowerShell 5.1)

Python 3.14.0. Throwaway folder holding the DE-01 files plus `lab_check.py`.

| Step | Result |
|---|---|
| `python -m venv .venv` | 5.6 s |
| Run `count_problems.py` with the fresh environment's Python | `ModuleNotFoundError: No module named 'pandas'` |
| `python -m pip install -r requirements.txt` | 653 s on a slow connection (not typical); pandas 3.1.1, pyarrow 26.0.1, openpyxl 3.1.5, pytest 9.2.0 |
| `python -m pytest` inside the environment | `2 passed in 1.59s` |

`python lab_check.py` inside the environment (exit code 0):

```
[ok] python: Python 3.14 (needs 3.11 or newer)
[ok] environment: running inside a virtual environment: ...\.venv
[ok] packages: pandas 3.1.1, pyarrow 26.0.1, openpyxl 3.1.5, pytest 9.2.0
[ok] tests: pytest: 2 passed in 0.46s
```

With the system Python (exit code 1): environment `[FAIL]`, the other three `[ok]`
(system packages: pandas 2.3.3, pyarrow 23.0.0, openpyxl 3.1.5, pytest 9.0.2).

Not measured: macOS, Linux, a machine with no Python, the full DE-01 script on pandas 3.1.1.
