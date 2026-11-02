# Repeatable checked records (#19)

Authoritative experiment report: [RESULTS.md](RESULTS.md).

From this folder (PowerShell), verify `Test-Path -LiteralPath .` first:

```powershell
uv venv --python 3.13 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
uv run --python .venv/Scripts/python.exe --no-project python experiment.py --help
uv run --python .venv/Scripts/python.exe --no-project python experiment.py
uv run --python .venv/Scripts/python.exe --no-project python -m pytest -q
```

`--archive C:/path/to/official.zip` reuses a download but verifies both exact
hashes. Otherwise downloads into ignored `data/bike.zip`. Large canonical and
rerun files are ignored parquet; `audit.json` is the small tracked receipt.
All raw fields are retained with explicit int64/float64/date syntax/domain
checks. Weather [0,1] is a conservative normalized-data contract, not a claim
about disputed inverse physical units. No source row is removed or repaired.
Synthetic failures are in-memory copies and never overwrite successful data.
Runtime failures raise meaningful exceptions; the command returns nonzero.
An old successful receipt describes its old run, not a later failed attempt.

The full-source mechanical audit precedes the modeling protocol and reads all
count/component values. It is not a claim that final targets were literally
unseen. No outcome distributions, model metrics or period-specific target
analyses occur here. Missing source-calendar labels are reported, never filled;
naive labels make no UTC/timezone/DST or true elapsed-hour claim. Source weekday
is preserved and its empirical mapping audited; Monday-zero is derived separately.
Exact logical equality includes multiplicity/dtypes; parquet byte agreement is
only an observation for these runs and versions, not a cross-platform guarantee.

## Attribution and changes

Data: Hadi Fanaee-T (2013), *Bike Sharing*, UCI Machine Learning Repository,
https://doi.org/10.24432/C5W894, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Original publication: Hadi Fanaee-T and João Gama (2013), *Event labeling combining
ensemble detectors and background knowledge*, https://doi.org/10.1007/s13748-013-0040-3.
Changes: strict typed parsing, stable memberSHA:instant identity, derived naive
calendar timestamps and weekday, sorted records, audits and synthetic fault copies.
Primary-source ledger: `../../../../wiki/sources/2026-11-01-bike-sharing-dataset-contract.md`.
Code is the compact pedagogical experiment, not an orchestrator or deployment system.
