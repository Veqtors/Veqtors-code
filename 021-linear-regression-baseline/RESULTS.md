# #21 — observed constant and OLS baselines

Executed 2026-11-01, after #19's mechanical audit and #20's frozen protocol and
sentinel. No feature/model/window was changed in response to these scores.
All results below concern training or **development validation**, never the
reserved final period. Full precision is retained in `report.json`.

## Same-record comparison

All three models fit the **same 8,644 eligible training IDs** and predict the
**same 4,358 development IDs**. Nominal training has 8,645 rows; one row fails
label readiness. Reserved final has 4,376 rows and is never predicted/scored.

| Model | Train MAE | Train MSE | Train RMSE | Development MAE | Development MSE | Development RMSE |
|---|---:|---:|---:|---:|---:|---:|
| Training median (main MAE reference) | 103.304026 | 19,111.955576 | 138.245997 | 159.947912 | 49,504.903855 | 222.496975 |
| Training mean | 106.595183 | 17,900.393761 | 133.792353 | 154.230524 | 43,326.014687 | 208.149020 |
| Fixed calendar OLS | 59.227721 | 6,341.699355 | 79.634787 | 116.680137 | 24,944.075272 | 157.936934 |

MAE/RMSE units: rentals per represented hourly observation. MSE units: squared
rental counts. Metrics are pooled over every row in this single fixed split;
no row is removed for a negative prediction. Primary MAE and median comparator
were declared before fitting; the mean happens to have lower development MAE
than the median, but that did not change the main comparator.

Training constants: median **109**, mean **143.80749652938454**.
OLS-minus-median development MAE is **−43.2677746708696**; OLS has lower MAE
under the predeclared 1e-9 tie tolerance. This is an observed development
comparison, not a significance test, causal finding or deployment guarantee.
OLS minimizes training squared error, not MAE. Reporting MAE is a deliberate
pedagogical absolute-error lens, not a measured operator cost or a consequence
uniquely required by count-valued targets. Keep both references for later work.

## Frozen representation and availability

Only target `hr`, `mnth` and date-derived `weekday_mon0` are model inputs.
Weather, season, holiday/workingday, row IDs, year, target and both target
components are absent. Dense training-only `OneHotEncoder(categories='auto',
drop='first', handle_unknown='ignore')` feeds unconstrained `LinearRegression`
with intercept, no weights, no scaling/imputation, no interactions and no
postprocessing. Learned reference levels are **hour 0, month 1, weekday 0
(Monday)**. Training contains every calendar category; development has zero
unknown categories in each field. Unknown-ignore would otherwise alias the
omitted reference rather than learn a new effect.

There are **40 encoded columns**, centered solver rank **40**, and augmented
matrix rank **41/41** including intercept. The rank audit supports this fitted
reference-coded arithmetic; it is not a general guarantee that dropping a
category always removes every cross-feature dependency. Coefficients describe
conditional additive model associations in rental-count units, never causal
effects or universal feature importance.

The contract is byte-identical to #20's `protocol.json` and was in an artifact
before any fitting. Partitions and model configuration are persisted before fit.
Nominal train: 2011; development: [2012-01-01, 2012-07-01); reserved: July onward.
First development issuance: **2011-12-31 23:00**. Target label `t` means interval
start by convention, issue `t−1h`, outcome ready `t+1h` with explicitly
hypothetical zero reporting delay, equality allowed. Hence training ends at
22:00, excluding source ID 8645 at 23:00. Selection uses actual calendar
timestamps, not row-count gaps. No zero-filled absent hours.

## Raw predictions and deterministic diagnostics

- OLS raw negatives: **805 training**, **733 development**; minimum
  **−99.44008721736398** in both. Both constants produce zero negatives.
  Fractional and negative outputs are preserved in saved predictions and all
  MAE/MSE/RMSE calculations; no clipping, rounding or row masking.
- Trace is the predeclared **first development row**, memberSHA:8646,
  2012-01-01 00:00, observed 48. Inputs: hour 0, month 1, weekday 6 (Sunday).
  The only active non-reference term is `weekday_mon0_6`:

  ```text
  intercept                 -47.4284499593889
  weekday_mon0_6 × 1          -2.237082683988098
  all other encoded terms     0
  prediction                 -49.665532643377
  ```

  Full-precision weighted sum equals estimator output with recorded absolute
  difference **0.0** (checked at absolute tolerance 1e-10). Signed residual
  observed−predicted is **97.66553264337699**. This concrete negative forecast
  illustrates a support failure despite better aggregate development error.
- `trace.json` retains every named coefficient, encoded value and product,
  not just the displayed active term. Tests check column order, reference
  omission, feature-to-value mapping and the saved row's prediction.
- `diagnostics.json` holds the **first 48 development records** and all
  **24 target-hour slices**, chosen before scores. `residuals.svg` is the
  code-generated first-window residual figure. The window is by records, not
  a promise of 48 complete elapsed hours; positive residual means underprediction.
- Ignored `data/predictions.parquet` contains all train/development IDs,
  timestamps, observed counts, all three predictions, residuals and partition.
  It contains no reserved-period predictions or outcomes. Negative IDs remain
  retrievable there. Exact partition IDs/times are in ignored
  `data/partitions.parquet`, with compact count/ordered-ID hashes tracked
  in `partitions.json`. Dataset ZIP/canonical/prediction files are covered
  by existing ignore rules; no large CSV is written.

## Reproduction, identity and actual runtime

Latest complete run: **0.562 s wall, 0.515625 s process CPU**, verified local ZIP
read through preparation, pre-fit artifact persistence, fitting, training and
development prediction/metrics, rank, trace and diagnostics/output writes.
Excludes dependency installation and final report write. One repetition is
observational timing, not a benchmark. Numerical BLAS/OpenMP pools were limited
to one thread; exact libraries and per-model fit+predict times are in the report.
The earlier same-code-comparison run yielded identical full-precision metrics
and predictions; runtime varied. Test-only mapping assertions were then added.

Host: Windows 11, 12 logical CPUs, AMD64 Family 25 Model 33 Stepping 0.
Actual environment: CPython **3.13.12**, numpy **2.2.6**, pandas **2.3.3**,
scikit-learn **1.7.2**, pytest **8.4.2**, pyarrow **21.0.0**, scipy **1.18.1**.
These usable installed versions differ from later-version documentation labels
in the research. Actual parameter inventory, dense encoder behavior, solver
rank, constants, metrics and trace were exercised locally.

Tests: **6 passed in 1.67s**, including generated-artifact integration; none
skipped. Six expected sklearn unknown-category warnings arise in tiny synthetic
fixtures, where unseen weekdays intentionally map to the zero reference block;
the real experiment has no unknown development categories. Across the three
issues, the latest test runs total **23 passing tests**.

Source member SHA:
`e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f`.
All helpers have identical Git blob identity, with raw helper SHA-256
`beca12d7b9df34179a269fdc3fefa4d9fb9f5d40efd7bb9c9d7d0555abe758a7`.
Dataset logical SHA:
`4305923354cf9d3398076c9fc5d29553bf00e95adb0213fcb0c978d1bc82998a`.
Contract SHA:
`31a5009f7423323fd79907f1dbfb0ca31d57101f7ff423b088933e992333b334`.
`report.json` also records exact code, model-config, training-input,
development-input, ordered-partition and prediction-parquet hashes. Code hash
covers sorted Python filenames/bytes including tests; configuration is hashed
separately. The provenance helper is replicated byte-identically without imports
across folders. License/attribution/change notices are in [README.md](README.md).

Working directory: `content/issues/021-linear-regression-baseline/code`.

```powershell
uv run --python "C:/Users/Imtiaz/AppData/Local/Temp/opencode/ml-foundations-313/Scripts/python.exe" --no-project python experiment.py --archive "C:/Users/Imtiaz/AppData/Local/Temp/opencode/019-bike-sharing-dataset-2026-11-01.zip"
uv run --python "C:/Users/Imtiaz/AppData/Local/Temp/opencode/ml-foundations-313/Scripts/python.exe" --no-project python -m pytest -q
```

Independent uv setup and `--help` commands are documented in [README.md](README.md).

## Unresolved facts / later gates

No execution blocker remains for these scoped experiments. Source timezone/DST,
aggregation interval alignment, reporting delay, missing-hour causes, disputed
season labels and inverse temperature normalization remain external unknowns;
the declared retrospective calendar convention does not resolve them. No
business cost, significance threshold or causal identification was supplied.

**Final targets are unscored, not literally unseen.** #19's whole-source
mechanical schema/domain/component checks read their count values before the
protocol; this independent run repeats those checks. There are no reserved
target distributions, model fits, predictions, residuals, or scores. The
reserved period must remain closed to model selection until #25 locks the
candidate and later readiness-respecting refit/report authorization. Better
development MAE does not bypass that gate or repair OLS's negative support.
