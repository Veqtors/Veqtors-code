# #19 — observed pipeline results

Executed 2026-11-01 with installed CPython 3.13.12, isolated uv environment.
No modeling was performed. `audit.json` contains full machine-readable
hashes, versions, fault receipts and timings.

## Observations

- Official ZIP SHA-256: `b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401`.
- `hour.csv` SHA-256: `e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f`.
- 17,379 accepted, zero rejected source rows; no missing fields, duplicate
  stable IDs or duplicate date-hour labels. The counted file agrees with the
  distributed README's count, not the current catalog's 17,389.
- Coverage: 2011-01-01 00:00 through 2012-12-31 23:00; 165 absent labels in
  the 17,544-label naive calendar grid. Their causes are unknown. No zero filling.
- Every source row satisfies `cnt = casual + registered`; raw month/year agree
  with date. The documented workingday rule agrees with the derived weekday.
- Empirical source weekday mapping: 0=Sunday, 1=Monday, …, 6=Saturday.
  Raw source values remain intact; canonical `weekday_mon0` derives from date.
- Two separate parses match exactly across all records, column order and dtypes;
  parquet readback is lossless and the two parquet files also match bytewise here.
  Logical-output SHA: `4305923354cf9d3398076c9fc5d29553bf00e95adb0213fcb0c978d1bc82998a`.
  Parquet SHA: `14366cab6ee1db8fad5a3c8db30746874bd602b3f15d2885dc245127958a6534`.
- Separate in-memory copies with a missing `cnt` header, `hr=not-an-hour`, and
  duplicated stable ID each raise a meaningful `ContractError`. No faulty
  success output is written. The numeric receipt identifies field `hr`, line 2
  and original token. These are deliberate faults, not source defects.
- Latest complete experiment: 0.855 seconds wall time, including verified local
  ZIP read, both preparations, comparisons, writes and fault checks; no download.
- `pytest`: **10 passed in 0.57s**. An initial test expected `NaN` to reach the
  range check; installed pandas rejects that lexical token during numeric
  conversion. The test now records actual behavior and separately tests range
  rejection with `1.2`. No source policy changed to make the test pass.

## Scope and qualifications

The **whole-source mechanical audit happened before the split/model protocol**.
It read all count/component fields, including those later reserved for final
testing. It did not compute target distributions, scores, or period-specific
target diagnostics and did not remove target-dependent outliers. Final targets
are therefore **not literally unseen**; subsequent issues reserve them from
model fitting, selection and scoring until #25's later selection/report gate.

Timestamps are naive source-calendar labels. Interval start, prediction issuance
and hypothetical zero reporting delay are declared in #20, not discovered here.
Timezone/DST, source aggregation endpoints, absent-hour semantics, disputed
season labels and inverse temperature normalization remain unresolved external
facts. Neither equal hashes nor successful schema checks resolve them. The
normalized [0,1] weather contract is a conservative explicit rule; no physical
denormalization was attempted. Exact equality is observed on one host/version
set, not promised cross-platform. Python's standard `csv` parser handles lexical
rows before explicit conversion; this is not evidence about every pandas CSV
engine/default. No additional root ignore rule is needed.

## Exact execution

Working directory: `content/issues/019-repeatable-data-pipeline/code`.

```powershell
uv run --python "C:/Users/Imtiaz/AppData/Local/Temp/opencode/ml-foundations-313/Scripts/python.exe" --no-project python experiment.py --archive "C:/Users/Imtiaz/AppData/Local/Temp/opencode/019-bike-sharing-dataset-2026-11-01.zip"
uv run --python "C:/Users/Imtiaz/AppData/Local/Temp/opencode/ml-foundations-313/Scripts/python.exe" --no-project python -m pytest -q
```

Environment: numpy 2.2.6, pandas 2.3.3, scikit-learn 1.7.2, pytest 8.4.2,
pyarrow 21.0.0, scipy 1.18.1. These are actual usable installed versions, not
the later-version labels observed in research docs. Setup and independent-run
commands, attribution, license and change notice: [README.md](README.md).
