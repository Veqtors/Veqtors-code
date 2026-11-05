# #024 — measured development-only tree/forest comparison

Executed **2026-11-04**. Full precision and machine/runtime identities are in
`report.json`; reproduction and attribution are in [README.md](README.md).
No publication, code push or final-period evaluation was performed.

## Same-row numerical results

All six models fit the same **8,644** eligible 2011 training rows and predict the
same **4,358** January–June 2012 development rows. Primary MAE is in rentals per
represented hourly observation; MSE is squared rental count, RMSE rental count.

| Model | Train MAE | Train MSE | Train RMSE | Development MAE | Development MSE | Development RMSE |
|---|---:|---:|---:|---:|---:|---:|
| Training median | 103.304026 | 19111.955576 | 138.245997 | 159.947912 | 49504.903855 | 222.496975 |
| Training mean | 106.595183 | 17900.393761 | 133.792353 | 154.230524 | 43326.014687 | 208.149020 |
| Unchanged calendar OLS | 59.227721 | 6341.699355 | 79.634787 | 116.680137 | 24944.075272 | 157.936934 |
| Tree: depth 6, minimum leaf 20 | 80.187533 | 10414.645421 | 102.052170 | 129.677565 | 30119.309405 | 173.549156 |
| Forest: 100 trees, depth 6, minimum leaf 20 | 80.309551 | 10054.885642 | 100.274053 | 124.628269 | 28434.770501 | 168.626126 |
| Unrestricted diagnostic tree | 27.707844 | 2178.675862 | 46.676288 | 99.962341 | 20205.539222 | 142.146190 |

Under the predeclared 1e-9 MAE tie tolerance, the constrained tree and forest are
respectively **12.997427** and **7.948132** MAE worse than OLS. The diagnostic
is **16.717796** better than OLS on this development period, despite its larger
training/development MAE gap. It is a predeclared capacity diagnostic, not an
outcome-selected replacement. Do not turn its result into a claim that stronger
training fit must worsen held-out error. Its training MAE is nonzero: duplicate
calendar feature vectors can carry different targets.

These are conditional observations on one fixed representation and one later
six-month period. They establish no significance, acceptable business improvement
or deployment choice. OLS/tree/forest fit squared error; MAE is the separate
primary evaluation question. Nonnegative tree outputs do not establish accuracy.
The constrained candidates provide no development-MAE reason to replace OLS here.

## Inherited identity and pre-fit receipts

- Official UCI archive SHA-256:
  `b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401`.
- `hour.csv` SHA-256:
  `e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f`.
  Actual rows: 17,379; metadata's 17,389 was not substituted.
- Ordered train/development/reserved/excluded IDs, logical full-source hash and
  training/development input hashes exactly match #21. All hashes/counts and
  ID/time bounds are in `partitions.json`, `baseline-reference.json`, `report.json`.
  Data helpers and inherited protocol are byte-identical replicas, confirmed with
  `git hash-object` pair comparisons. No cross-folder imports are used.
- `frozen-config.json` was written before encoder or estimator fitting. It records
  the exact approved estimators and every default, no search, one thread,
  no weights/postprocessing, and reproduction tolerances. Raw config SHA-256:
  `d1f8d7a005e6d30a260e3b7e683e4a8778a669b07ab85f2f8428a6ed83380946`.
  The inherited `protocol.json` is a historical #21 contract, not the entire
  #024 model declaration. “No interactions” means no engineered columns here;
  tree paths can learn conditional interactions.
- Same train-only dense reference-coded 40 columns: 23 hour, 11 month, six
  Monday-zero weekday. References hour 0/month 1/Monday; zero development unknown
  categories. Every estimator uses the same matrix, including the diagnostic.
- Reproduction gates precede new-tree fits. Metrics use absolute 1e-8 plus relative
  1e-12 tolerance; first-row prediction absolute 1e-9 plus relative 1e-12;
  constants absolute 1e-12, relative zero. All checks passed. Constants exactly
  match median **109**, mean **143.80749652938454**. Maximum absolute OLS metric
  difference from #21 is **7.275957614183426e-12** (development MSE); first-row
  OLS difference is **4.618527782440651e-13**. The MAE ranking tie remains 1e-9,
  a distinct rule.

## Fitted structures and fixed diagnostics

`structures.json` persists all child indices, named feature mapping, thresholds,
node values/impurity, unweighted/weighted counts, seeds and fitted depth/leaf
counts for the two trees and all 100 forest members. The constrained tree fitted
**depth 6, 22 leaves, 43 nodes**. The unrestricted diagnostic fitted **depth 40,
2,014 leaves**. Forest bootstrap receipts retain 8,644 draws per tree, distinct
training-row counts and ordered draw-index hashes. Its nominal split feature
count is **28 of 40 encoded columns**, not 70% of three raw fields. A library
split may inspect more columns to find a valid partition.

The predeclared first development row is source ID **8646**, January 1 2012
00:00, observed count **48**, hour 0/month 1/Sunday. Predictions:

- OLS **-49.66553264337654** (raw; rounding/clipping would change the experiment).
- Constrained tree **112.47641800246609**.
- Forest mean **121.37639044577128** (per-tree mean; sequential estimator
  accumulation can differ by machine-rounding units).
- Unrestricted diagnostic **27.2**.

The constrained row follows `hr_17, hr_18, hr_8, hr_19, hr_16, hr_4 <= 0.5`,
taking the left branch each time to leaf 6. These are “not this hour” indicator
questions, not raw hour thresholds. `trace.json` preserves every branch for this
row through the constrained tree, diagnostic and each of the 100 forest trees,
as well as the encoded row and all individual forest predictions.

For **every training and development row**, the arithmetic average of the 100
tree outputs matches the actual forest estimator: maximum absolute difference
**2.2737367544323206e-13** in each partition. Ignored
`data/forest-predictions.parquet` retains those paired per-tree outputs.
`data/predictions.parquet` holds all six raw forecasts and signed residuals,
including OLS's **805 training and 733 development negative predictions**.
No model output is rounded, clipped or discarded for scoring.

`diagnostics.json` contains **first 48 development records and all 24 hour
slices**, all models, not chosen favorable rows. Full-precision paired values
are in parquet; the compact first-window JSON uses pandas' 15-decimal export.
Positive residual means observed minus predicted, hence underprediction.

## Runtime, sizes and actual environment

Latest complete cached-archive run: **1.233665900 s wall, 1.1875 s process CPU**.
Boundary: source cache verification/mechanical parse through partition/config
freeze, encoder preparation, fits, train/development predictions, metrics,
structure/path/forest checks and artifact writes; excludes installation, final
report write and tests. Initial download time is not part of this cached run.
One timing observation is not a benchmark; no hardware speed claim follows.

Per-model times below exclude encoder preparation, metrics, serialization and
inspection. Prediction columns are train plus development (sums of separately
recorded calls). Full timings, including separate prediction CPU, are in JSON.

| Model | Fit wall s | Fit CPU s | Train+dev predict wall s | Encoder+model pickle bytes |
|---|---:|---:|---:|---:|
| Median | 0.000271100 | 0 | 0.000028900 | 1304 |
| Mean | 0.000133900 | 0 | 0.000025200 | 1302 |
| OLS | 0.005175700 | 0.015625 | 0.000402000 | 2058 |
| Constrained tree | 0.005718500 | 0 | 0.000790200 | 5049 |
| Forest | 0.277891100 | 0.281250 | 0.018116600 | 331592 |
| Diagnostic | 0.016977300 | 0.015625 | 0.001639200 | 291908 |

Size is `len(pickle.dumps((fitted_encoder, fitted_estimator), protocol=5))`,
including serialization overhead and the encoder, without compression. Each
ignored `data/{model}.pkl` contains exactly those measured bytes. It is not
process memory or a cross-version deployment format. Zero short-call CPU readings
reflect timer resolution, not proof of zero work. Forest training prediction
CPU measured 0.015625 s; other prediction CPU readings were zero.

Actual versions: **Python 3.13.9**, numpy **2.2.6**, pandas **2.3.3**,
scikit-learn **1.7.2**, scipy **1.18.1**, pyarrow **21.0.0**, pytest **8.4.2**,
joblib **1.5.2**, threadpoolctl **3.6.0**. All declared library versions were
available; Python differs from #21's 3.13.12, with numerical identity passing.
Host reports Windows 11 build 26300, AMD64 Family 25 Model 24 Stepping 1 and
192 logical CPUs. Both OpenBLAS pools and the OpenMP pool were measured at
**one thread** inside the fitting context; forest also has `n_jobs=1`.

## Tests, execution commands and repair history

**17 passed, none skipped, in 4.63 s.** Three expected unknown-category warnings
come from synthetic sentinel transforms, not the real development matrix.
Tests exercise partition/feature exclusion and no-final guard negative controls,
actual persisted sklearn predictions for all six models, raw metrics, exact
arithmetic versus a real synthetic depth-1 tree, every training leaf mean
(bootstrap-weighted for the forest), per-tree forecasts/paths and byte sizes.
A deliberately corrupted OLS score fails the baseline gate, proving its check
is sensitive rather than just asserting a saved success flag.

Working directory for Python commands:
`G:/imtiaz/substack/content/issues/024-decision-trees-and-forests/code`.
Environment creation/install commands ran from the repository root:

```powershell
Test-Path -LiteralPath "C:\Users\user\AppData\Local\Temp\opencode"; if ($?) { uv venv --python 3.13 "C:\Users\user\AppData\Local\Temp\opencode\024-trees-313" }
uv pip install --python "C:\Users\user\AppData\Local\Temp\opencode\024-trees-313\Scripts\python.exe" "numpy==2.2.6" "pandas==2.3.3" "scikit-learn==1.7.2" "pytest==8.4.2" "pyarrow==21.0.0" "scipy==1.18.1" "joblib==1.5.2" "threadpoolctl==3.6.0"
& "C:\Users\user\AppData\Local\Temp\opencode\024-trees-313\Scripts\python.exe" experiment.py --help
& "C:\Users\user\AppData\Local\Temp\opencode\024-trees-313\Scripts\python.exe" experiment.py
& "C:\Users\user\AppData\Local\Temp\opencode\024-trees-313\Scripts\python.exe" -m pytest -q
& "C:\Users\user\AppData\Local\Temp\opencode\024-trees-313\Scripts\python.exe" reader_lab.py --help
python reader_lab.py --answers
uv pip check --python "C:\Users\user\AppData\Local\Temp\opencode\024-trees-313\Scripts\python.exe"
python --version
```

Existing venvs were searched via glob before creating this isolated temporary
environment. The system Python is 3.14.0; only the dependency-free lab used it.
Package compatibility check passed (16 installed packages).

`experiment.py` ran three times during implementation: the first stopped
**before any fit** because the encoder's dtype class needed a JSON name; the
second reached fitting but stopped while exporting a NumPy integer leaf count;
the third completed after explicit integer serialization. These were receipt
serialization repairs. The persisted approved model parameters, input boundaries,
seed and tolerances were unchanged; no result-guided tuning or search occurred.
The latest complete run is the timing/report receipt above. Unit/integration
tests do not refit the UCI candidates; they load the locally generated models.

## Remaining boundaries

No execution blocker remains. The **4,376 reserved-final rows remain unfitted,
unpredicted and unscored**; only inherited mechanical source audits read their
counts. Prior access means they are not literally unseen. Calendar/DST/interval
semantics and actual reporting delay remain unresolved, and there is no business
cost/significance threshold. Keep the hypothetical readiness convention and the
later #25 selection/refit/report gate. Publication and code release are not approved.
