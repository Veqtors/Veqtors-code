# Fixed constant and linear baselines (#21)

Authoritative experiment report: [RESULTS.md](RESULTS.md).

From this folder, first verify `Test-Path -LiteralPath .`:

```powershell
uv venv --python 3.13 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
uv run --python .venv/Scripts/python.exe --no-project python experiment.py --help
uv run --python .venv/Scripts/python.exe --no-project python experiment.py
uv run --python .venv/Scripts/python.exe --no-project python -m pytest -q
```

Optional `--archive C:/path/official.zip` still verifies exact archive/member
SHA. Independent: no cross-folder imports. `dataset.py` is byte-identical to #19
helper v1; `protocol.py` and `protocol.json` replicate #20. Provenance lives in
the helper docstrings and source ledgers. No GPU, paid API or secret required.

`protocol.json` was created before any fitting; `partitions.json`, exact ordered
`data/partitions.parquet` and `model-config.json` are persisted before model fit.
Train 2011, development Jan–Jun 2012, reserved July onward, with label-readiness
exclusion. Only target hour/month/derived Monday-zero weekday enter training.
Naive source-calendar label t denotes interval start by convention; issue t−1h,
ready t+1h, explicitly hypothetical zero reporting delay with equality allowed.
No actual source timezone/DST, endpoints or publication delay is established.

OLS uses dense train-discovered one-hot categories, drop-first, unknown-ignore,
intercept, unconstrained coefficients, no weights/scaling/imputation/interactions.
Reference categories and matrix rank are measured in `report.json`. Unknown
categories alias the omitted level, not a learned unseen effect. Named full
precision coefficients and one deterministic first development prediction are
in `trace.json`. These are conditional associations, never causal weights.
Installed sklearn 1.7.2 dense OLS is used; its actual parameter dictionary and
solver rank are recorded rather than assuming later docs' API defaults.

Mean/median dummies and OLS share exact train and evaluation IDs. Primary MAE
uses median as predeclared main reference; MSE/RMSE are secondary. OLS minimizes
training squared error, not MAE. This deliberate teaching mismatch is not a
business cost model or a loss uniquely justified by count targets. Comparisons
use 1e-9 rental-count MAE tolerance, one fixed development split, all-row pooled
metrics, no significance claim. Raw negatives/fractional outputs remain in every
metric, never clipped or rounded. No feature changes after scores.

`data/predictions.parquet` holds train/development targets, all three predictions,
signed residuals, row IDs and partition, never reserved outcomes/predictions.
All large ZIP/parquet files are covered by existing ignores; no CSV is emitted.
Tracked `diagnostics.json` and code-generated `residuals.svg` use predeclared
first 48 development records and all 24 hour slices. Positive residual means
underprediction. Negative-row IDs can be retrieved from prediction parquet.

One CPU run with numerical thread pools limited to one records per-model
fit+predict wall/process time plus end-to-end timing, host and actual versions.
Timing is observational, not a benchmark or promise. Main-guard execution only.
Tests use tiny synthetic fit data and validate actual generated artifacts when
available; run the experiment before pytest for full artifact integration checks.

Final data remain **unscored, not literally unseen**: #19 whole-source mechanical
schema/domain/component checks read all target values, and independent source
verification repeats them. No final target distributions, fitting, predictions
or diagnostics; #25 owns the later frozen selection/refit/report authorization.

## Attribution and changes

Hadi Fanaee-T (2013), *Bike Sharing*, UCI Machine Learning Repository,
https://doi.org/10.24432/C5W894,
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Original publication: Hadi Fanaee-T and João Gama (2013), *Event labeling combining
ensemble detectors and background knowledge*, https://doi.org/10.1007/s13748-013-0040-3.
Changes: strict typed parsing, stable memberSHA:instant IDs, derived naive
calendar labels/weekday, partition metadata, encoded calendar baselines and
development predictions. No source-row repairs or zero-filled missing hours.
Source ledgers: root `wiki/sources/2026-11-01-bike-sharing-dataset-contract.md`,
`2026-11-01-leakage-validation-primary-docs.md`, `2026-11-01-linear-baselines-primary-docs.md`.
