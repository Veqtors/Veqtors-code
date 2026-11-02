# Prediction boundary and full-entry sentinel (#20)

Authoritative experiment report: [RESULTS.md](RESULTS.md).

Run from this folder after `Test-Path -LiteralPath .`:

```powershell
uv venv --python 3.13 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
uv run --python .venv/Scripts/python.exe --no-project python experiment.py --help
uv run --python .venv/Scripts/python.exe --no-project python experiment.py
uv run --python .venv/Scripts/python.exe --no-project python -m pytest -q
```

Optional `--archive C:/path/official.zip` reuses an exact-hash-verified ZIP.
No cross-issue imports or experiment execution at import time; no GPU/API/credentials.
`dataset.py` is a byte-identical replica of #19 helper v1, provenance in its
module docstring. It performs the same mechanical source checks before splitting.
Dataset ZIP/partition parquet in `data/` are ignored. No CSV output is written.

`protocol.json` is the **pre-fit artifact**, created before any experiment fit.
The windows were prescribed from documented 2011–2012 coverage, not scores:
2011 nominal training, Jan–Jun 2012 development, July 2012 onward reserved.
The script persists `partitions.json` plus exact ordered ID/time parquet before
even synthetic sentinel fitting. Train labels must be ready at first development
issuance. All clocks are naive calendar arithmetic: label t is interval start
by convention, issue t−1h, ready t+1h, hypothetical zero reporting delay,
equality allowed. This is not verified source serving latency or DST behavior.

Final targets are **unscored, not literally unseen**: #19's whole-source
mechanical component/schema checks already read them. This independent command
repeats those checks, but retains only ID/time for the reserved partition.
No final target distributions, scores or target-specific diagnostics. A real
development row illustrates `casual+registered=cnt` without fitting a proxy model.

Sentinel: fresh imputer → scaler numeric branch and auto-category encoder per
full `prepare_fit` call. Compare actual fitted attributes and transformed train;
verify validation transforms don't mutate state. Invalid concatenated fitting
must fail invariance; training perturbation must change state. This is a
synthetic boundary probe, not a bike-demand score experiment or complete proof
against every possible leakage path. The calendar-only baseline needs neither
imputation nor scaling; those branches exist to demonstrate learned-state access.

## Attribution / changes

Hadi Fanaee-T (2013), *Bike Sharing*, UCI, https://doi.org/10.24432/C5W894,
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Original publication:
Hadi Fanaee-T and João Gama (2013), *Event labeling combining ensemble detectors
and background knowledge*, https://doi.org/10.1007/s13748-013-0040-3.
Changes: strict typed parsing, stable memberSHA:instant IDs, derived naive calendar
labels/weekday, chronological partition metadata. Synthetic sentinel is separate.
Source/API ledgers: `wiki/sources/2026-11-01-bike-sharing-dataset-contract.md`
and `2026-11-01-leakage-validation-primary-docs.md` at repository root.
