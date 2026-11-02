# One score, two fixed decisions — standalone issue #22

Authoritative measurements: [RESULTS.md](RESULTS.md). This folder runs independently
of every other issue. CPU only; no GPU, credentials, paid API or cloud account.
No publication or model/threshold selection is performed.

## Reproduce with Python 3.13 and uv

From this `022-logistic-regression-thresholds/` directory, in Windows PowerShell:

```powershell
uv venv --python 3.13.9 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt
.venv/Scripts/python.exe -B experiment.py
.venv/Scripts/python.exe -B experiment.py
.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider
```

On Linux/macOS, use `.venv/bin/python` instead:

```sh
uv venv --python 3.13.9 .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python -B experiment.py
.venv/bin/python -B experiment.py
.venv/bin/python -B -m pytest -q -p no:cacheprovider
```

The first invocation downloads the official archive into ignored `data/bike.zip`.
Every invocation checks both archive and extracted `hour.csv` SHA-256 before
parsing. A mismatched source or partition, one-class training target, convergence
warning or changed frozen state blocks completion. Do not alter the policy or
increase iterations to make a failed run pass. The second invocation verifies
identical material state; the integration test requires that successful repeat
receipt. On a fresh checkout with the supplied report, even the first invocation
compares with that report. Exact byte reproducibility is verified on the recorded
Windows runtime; another BLAS/OS may produce last-bit differences and must report
that mismatch rather than silently relax the check.

All dependencies, including transitives, are pinned in `requirements.txt`.
Core pins: NumPy 2.2.6, pandas 2.3.3, scikit-learn 1.7.2, pytest 8.4.2,
PyArrow 21.0.0; SciPy 1.16.3 and threadpoolctl 3.6.0. The script checks Python
3.13 and every listed dependency before loading the source.

## Frozen sequence and boundaries

1. `protocol.json` is the classification contract; `model-config.json` fixes
   estimators, encoding, label recipe, native threads and policies. Their durable
   `frozen-config.json` snapshot is written/fsynced before any fit, including
   encoding. Existing snapshots must match, not be overwritten with changed state.
2. `dataset.py` and `protocol.py` are byte-identical #21 helper copies made using
   `apply_patch`. No runtime import or file access reaches into #21. The source
   helper retains exact parsing and whole-source mechanical integrity checks.
3. `inherited-identity.json` contains the original #21 partition identity
   projection and exact 40 encoded names, without inheriting its regression
   estimators/metrics. `partitions.json` and ignored `data/partitions.parquet`
   verify/save all ordered IDs and timestamps. Reserved rows contain metadata only.
4. Compute the 75th percentile only from eligible training counts with NumPy
   `method='higher'`. `label-config.json` stores `c`, strict `>`, class mapping,
   training IDs and training-count hash. It is fsynced and printed before fitting.
5. Apply frozen `c` to train/development only. Require both training classes.
   Train-only OneHotEncoder uses `drop='first'`, unknown-ignore and dense output;
   exact feature order is `hr`, `mnth`, `weekday_mon0`.
6. Fit the prior dummy and fixed logistic once per invocation. Native BLAS/OpenMP
   pools are limited to one thread throughout computation, not just `n_jobs=1`.
   Capture all fit warnings; any ConvergenceWarning raises before evaluation.
7. Map label 1 independently via each estimator's `classes_`; assert pinned
   fitted classes `[0,1]`. Save raw float64 `decision_function` and P(1), assert
   sigmoid agreement at `rtol=atol=1e-12`, then apply exactly `p>=0.50` and
   `p>=0.30` to the same saved scores. No refit or score/weight mutation by policy.
8. Evaluate mean log loss with explicit `labels=[0,1]` and sorted probability
   columns `[1-p,p]`. Its dtype-epsilon clipping is metric-internal; artifacts
   preserve raw probabilities. Fit regularization is not part of held-out loss.

The fitting objective is mean binary cross entropy plus
`sum(w**2)/(2*C*n_train)`; the intercept is unpenalized. `multi_class` is left
unspecified at the pinned binary default and no sample/class weights are passed.
Reference coding is an approved continuity choice; it breaks symmetry for
penalized models and aliases an unknown level to the dropped-reference block.

## Outputs and #23 handoff

Small portable text artifacts suitable for later review are `protocol.json`,
`model-config.json`, `frozen-config.json`, `label-config.json`,
`inherited-identity.json`, `partitions.json`, `report.json`, `trace.json`,
`synthetic.json`, and `RESULTS.md`. No public push is implied.

Local row-aligned tables are **ignored**:

- `data/train-predictions.parquet`: 8,644 training rows.
- `data/validation-predictions.parquet`: 4,358 development rows, the #23 handoff.
- `data/partitions.parquet`: ordered IDs/times/partition names, no targets.
- `data/bike.zip`: checksum-verified official source, never stage/upload.

Both prediction tables have only `record_id`, `target_time`, `y`, `logistic_p1`,
`logistic_z`, `decision_050`, `decision_030`, `dummy_p1`, `dummy_decision_050`,
`dummy_decision_030`. They contain no `cnt`, outcome components or original
calendar-input columns; target time is provenance metadata, not a model input.
All labels and predictions are train/development only. Compact JSON records
table byte hashes, logical hashes, row-ID hashes and all fitted coefficients, so
#23 can reproduce locally without publishing a downloaded dataset or large table.

The user permits derived predictions in principle, but this implementation
chooses the expressly allowed ignored-Parquet/reproduction handoff. No prediction
CSV, full dataset JSON or dataset upload is created. Check ignore rules before
any future staging; publishing the raw downloaded dataset is prohibited by this
project policy even though UCI licensing separately permits attributed reuse.

Read-only #23 consumer, after reproducing if the file is absent (run from this
directory; no fitting in the consumer):

```python
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd

root = Path('.')
report = json.loads((root / 'report.json').read_text())
material = report['material']
path = root / 'data/validation-predictions.parquet'
receipt = material['outputs']['data/validation-predictions.parquet']
assert hashlib.sha256(path.read_bytes()).hexdigest() == receipt['sha256']
pred = pd.read_parquet(path)
assert len(pred) == receipt['rows'] == 4358
ids = json.dumps(pred.record_id.tolist(), sort_keys=True,
                 separators=(',', ':'), allow_nan=False).encode()
assert hashlib.sha256(ids).hexdigest() == receipt['ordered_ids_sha256']
assert pred.target_time.lt(pd.Timestamp('2012-07-01')).all()
assert not {'cnt', 'hr', 'mnth', 'weekday_mon0'} & set(pred.columns)
np.testing.assert_array_equal(pred.decision_050, (pred.logistic_p1 >= .50).astype('int64'))
np.testing.assert_array_equal(pred.decision_030, (pred.logistic_p1 >= .30).astype('int64'))
print(len(pred), material['label']['cutoff'])  # 4358 211.0
```

#23 should preserve these rows/scores/policies and consume `y` rather than derive
another label convention. Any later approved error-cost analysis has its own
scope; this companion computes no precision/recall, costs or tuned thresholds.

## Trace, arithmetic and tests

`trace.json` selects the **first** actual development row, not an interesting
score. It contains its three allowed inputs, all 40 encoded values, weights and
products, intercept, summed z, API z, sigmoid, true binary label, dummy P(1), and
both policies for both models. `synthetic.json` separately records z=0,
z=ln(3), positive-label loss at .8/.2 and exact .30/.50 ties. These fixtures are
not UCI measurements or calibration evidence.

The 12 pytest cases (including parameter expansion) cover source/parser rejection,
inherited IDs/readiness, final guards, train-only cutoff/ties/one-class rejection,
allowlist/encoder boundary, class-column mapping, sigmoid/decision equality,
unchanged parameters/scores, finite clipped loss, convergence failure without
retry, frozen-state drift rejection and actual produced-artifact integration.
Integration is mandatory: no skip, source substitution or mock experiment. It
reads the real downloaded archive and artifacts, checks paired IDs, hashes,
recomputes losses, reconstructs the fitted logistic state without fitting,
rebuilds the first trace, and checks the repeat receipt. It does not rerun the
whole experiment or create reserved labels.

## Source, attribution and limitations

UCI Bike Sharing, Hadi Fanaee-T (2013), DOI
[10.24432/C5W894](https://doi.org/10.24432/C5W894),
[dataset catalog](https://archive.ics.uci.edu/dataset/275/bike+sharing+dataset),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
The original README requests citation of Hadi Fanaee-T and João Gama,
“Event labeling combining ensemble detectors and background knowledge,”
*Progress in Artificial Intelligence* (2013),
[doi:10.1007/s13748-013-0040-3](https://doi.org/10.1007/s13748-013-0040-3).
Changes: parsed/sorted records, date-derived weekday, chronological/readiness
partitions, derived training-cutoff binary labels and model prediction receipts.
No claim that UCI supplied an operational busy label.

The UCI catalog's 17,389-instance description conflicts with the archive README
and verified `hour.csv`'s 17,379 records. Calendar coordinates are not a complete hourly grid;
no gap filling occurs. Source weekday uses a different convention from the
explicitly date-derived Monday-zero feature. Catalog/README season names and
temperature normalization descriptions also conflict; those fields are not model
inputs, and no interpretation/denormalization resolves them here. Actual timezone/DST, aggregation
endpoints and historical publication latency remain unestablished. The naive
interval-start clock, one-hour lead, zero reporting delay and readiness equality
are hypothetical retrospective conventions. Prior whole-source mechanical
count/component validation includes reserved counts; those targets are not
literally unseen. No reserved label, class-balance, prediction or score analysis
is performed. A lower development log loss proves neither calibration nor
operational value, and is not comparable to #21's count-regression MAE.

Pinned implementation references:
[logistic mechanism/objective](https://scikit-learn.org/1.7/modules/linear_model.html#logistic-regression),
[thresholds](https://scikit-learn.org/1.7/modules/classification_threshold.html),
[calibration](https://scikit-learn.org/1.7/modules/calibration.html),
[quantile](https://numpy.org/doc/2.2/reference/generated/numpy.quantile.html),
[dummy](https://scikit-learn.org/1.7/modules/generated/sklearn.dummy.DummyClassifier.html),
[log loss](https://scikit-learn.org/1.7/modules/generated/sklearn.metrics.log_loss.html).
