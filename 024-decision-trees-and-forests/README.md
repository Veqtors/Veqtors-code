# Decision trees and forests — independent CPU experiment (#024)

[RESULTS.md](RESULTS.md) records the observed run. This folder runs independently:
local helper replicas, no unpublished cross-issue runtime imports, GPU or API keys.

## Reader lab (Python standard library only)

```powershell
python reader_lab.py --help
python reader_lab.py
python reader_lab.py --answers
```

The eight bike-hour records are **invented**, not UCI observations. Exact
`Fraction` arithmetic checks the parent mean/SSE, candidate thresholds 7.5 and
12.5, fresh-hour routing, a separate fresh-target checkpoint and illustrative
forest averaging. `--answers` reveals checkpoint 85 separately from the question.
The lab runs without fitting a model, downloading data or writing receipts.

## Reproduce the experiment

From this folder, with [uv](https://docs.astral.sh/uv/) installed:

```sh
uv venv --python 3.13
uv pip install -r requirements.txt
uv run python experiment.py --help
uv run python experiment.py
uv run python -m pytest -q
```

Python 3.13 supports the pinned binary packages; the stdlib lab also ran on
Python 3.14.0.

By default the inherited helper downloads the official archive from
https://archive.ics.uci.edu/static/public/275/bike+sharing+dataset.zip into ignored
`data/bike.zip`. Optional `experiment.py --archive "C:/path/bike.zip"` uses the
same archive/member hash checks. An absent supplied archive path invokes the
inherited downloader at that path; prefer the default cache unless reusing a ZIP.
No source CSV or large parquet is tracked. Local pickle artifacts are also ignored;
load only the trusted artifacts this script generated, never an unknown pickle.

## Frozen contract

- `dataset.py`, `protocol.py` and `protocol.json` are byte-identical #21 replicas
  (#20 originally established the partition helper/contract). The inherited
  JSON retains #21's model list as historical evidence. **`frozen-config.json`
  supplies the complete #024 declaration**, including every estimator default,
  encoder configuration, size/timing definitions and numerical tolerances.
- The script verifies snapshot, ordered partition and train/development input
  identities against `baseline-reference.json`, an explicitly copied #21 report
  excerpt. It writes partition/config receipts **before encoder or estimator fit**.
  A conflicting existing frozen configuration fails rather than being replaced.
- Same 8,644 eligible training rows and 4,358 development rows; 4,376 reserved-final
  rows carry only ID/time in the partition artifact. Source ID 8645 is excluded:
  its label is not ready at first development issuance, December 31 2011 23:00.
- Dense train-only `OneHotEncoder(categories='auto', drop='first',
  handle_unknown='ignore', sparse_output=False)` produces 40 columns: 23 hour,
  11 month and six Monday-zero weekday indicators. References: hour 0, January,
  Monday. All six estimators receive this same matrix; constants ignore it.
  No target/components, weather, holidays, year/trend, IDs or engineered
  interactions enter. Tree paths may learn conditional interactions.
- Exact approved choices: depth-6/minimum-leaf-20 squared-error tree; 100-tree
  squared-error forest, depth 6, minimum leaf 20, `max_features=0.7`, bootstrap,
  seed 42, `n_jobs=1`; unrestricted depth/minimum-leaf-1 diagnostic, seed 42;
  unchanged unweighted OLS with intercept and training median/mean constants.
  No parameter/seed search, postprocessing, scaling or imputation.
- Primary MAE (median main reference); secondary MSE/RMSE. Squared-error tree/OLS
  fitting does **not** optimize MAE. Raw fractional/negative OLS forecasts remain
  in every metric. A 1e-9 MAE tie is separate from reproduction tolerances:
  metrics absolute 1e-8/relative 1e-12; predictions absolute 1e-9/relative 1e-12;
  constants absolute 1e-12/relative zero. Baseline checks run before new tree fits.
- Numerical BLAS/OpenMP pools are explicitly limited to one, in addition to
  forest `n_jobs=1`. Wall and process CPU are measured separately for fitting
  and each prediction partition; encoder preparation is separate. One observation
  is not a benchmark. Standalone size includes the fitted encoder and estimator
  serialized together with pickle protocol 5, including serialization metadata.

## Artifacts and tests

| Path | Evidence |
|---|---|
| `partitions.json`, ignored `data/partitions.parquet` | Counts/hashes and every ordered ID/time; no reserved targets |
| `frozen-config.json`, `baseline-reference.json` | Pre-fit declaration/tolerances and inherited identity/score reference |
| `report.json` | Full-precision numerical scores, baseline differences, actual versions, thread pools, CPU/wall timings, sizes, hashes |
| `structures.json` | Every tree's children, feature indices, thresholds, leaf means, counts/weights/impurity; bootstrap draw hashes and distinct counts |
| `trace.json` | Fixed first development row; tree/diagnostic and all 100 forest paths; first-row forest arithmetic and all-row average checks |
| `diagnostics.json` | Fixed first 48 development records and every one of the 24 target-hour slices, all models |
| ignored `data/predictions.parquet` | Paired train/development row IDs, calendar fields, targets, raw predictions and signed residuals |
| ignored `data/forest-predictions.parquet` | All 100 per-tree predictions paired with the same train/development IDs |
| ignored `data/{model}.pkl` | Exact serialized inference pairs for actual-estimator integration checks |

Run the experiment before pytest. Missing artifacts **fail**, never skip.
Tests verify stable ordered IDs/readiness, excluded-feature perturbations,
train-only vocabularies, no-final guards before model machinery, raw metrics,
saved artifacts against actual estimator outputs, tree/bootstrapped leaf means,
all-row forest averages and measured serialized byte sizes. A deliberately wrong
baseline score must trip the baseline gate. The synthetic hand split is also
checked against an actual installed sklearn depth-1 tree, without changing the
real experiment's configuration.

## Interpretation and limitations

This is a development comparison under **one encoded representation**, not each
algorithm's best pipeline. Encoded-column splits are indicator tests, not raw
`hour <= 12.5`; forest feature subsampling has nominal 28 encoded candidates and
may inspect more to find a valid split. The toy min-leaf configuration is separate:
eight invented examples cannot split under the real minimum leaf size of 20.

The source has 17,379 actual hourly rows despite the UCI page's 17,389 metadata.
Missing hours are never filled. Calendar label `t` denotes interval start by
convention; issue `t-1h`, readiness `t+1h`, zero reporting delay, equality allowed.
Actual timezone/DST, interval endpoints and reporting availability are unresolved.
Whole-source schema/domain/component checks mechanically read all counts,
including reserved counts: **reserved final is unscored, not literally unseen**.
No reserved fit, prediction, score or target-specific diagnostic is authorized.

Observed development differences and training/development gaps are not
significance tests, business costs or deployment justification. The unrestricted
diagnostic's result does not turn it into an authorized replacement candidate.
Later #25 owns selection/refit/final-report authorization. Publication and code
release require separate author approval.

## Attribution and changes

Hadi Fanaee-T (2013), *Bike Sharing*, UCI Machine Learning Repository,
https://doi.org/10.24432/C5W894, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Original publication: Hadi Fanaee-T and João Gama (2013), *Event labeling combining
ensemble detectors and background knowledge*, https://doi.org/10.1007/s13748-013-0040-3.
Changes: strict typed parsing, stable memberSHA:instant IDs, derived naive calendar
labels/weekday, readiness partitions, encoded calendar learners and development
predictions. No source-row repairs or zero filling. Invented fixtures are labeled.

Mechanism/API references: [sklearn 1.7 trees](https://scikit-learn.org/1.7/modules/tree.html),
[forests](https://scikit-learn.org/1.7/modules/ensemble.html#random-forests),
[DecisionTreeRegressor](https://scikit-learn.org/1.7/modules/generated/sklearn.tree.DecisionTreeRegressor.html),
[RandomForestRegressor](https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.RandomForestRegressor.html),
[OneHotEncoder](https://scikit-learn.org/1.7/modules/generated/sklearn.preprocessing.OneHotEncoder.html).
