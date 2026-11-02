# Issue #22 — authoritative standalone experiment results

Executed 2026-11-02 on the official checksum-verified UCI archive. This is the
classification experiment receipt, not draft/publication approval. Full machine
precision, fitted parameters, identities and output hashes: `report.json`.
Commands and attribution: `README.md`.

## Frozen configuration — before fitting

- Target: `y = int(cnt > c)`, with training-only
  `numpy.quantile(cnt_train, .75, method='higher')`. **c = 211.0 rentals**.
  Class 0 means `cnt <= 211`; class 1 means `cnt > 211`. All ties are negative.
  The measured c and mapping were fsynced to `label-config.json` and printed
  before the first fit. This is a teaching convention, not capacity or demand.
- `protocol.json` and `model-config.json` were authored before execution;
  `frozen-config.json` durably captures their exact state before fitting.
  Existing frozen files reject changed content. The classification contract
  contains no inherited regression model or regression metric fields.
- Training-only dense OneHotEncoder: `drop='first'`,
  `handle_unknown='ignore'`. Inputs in order: `hr`, `mnth`, `weekday_mon0`.
  Learned categories: hours 0–23, months 1–12, Monday-zero weekdays 0–6;
  references 0, 1, 0. All **40 columns exactly match #21**, including order.
  Unknown development categories: 0 for each feature.
- `DummyClassifier(strategy='prior')`, training labels only.
- `LogisticRegression(solver='lbfgs', penalty='l2', C=1.0,
  fit_intercept=True, max_iter=1000, tol=1e-6, class_weight=None,
  n_jobs=1, warm_start=False)`. No sample weights; `multi_class` unspecified.
  Native BLAS/OpenMP limits: **one thread**, verified inside computation.
- Native L-BFGS-B configuration: `maxiter=1000`, `gtol=1e-6`,
  `ftol=64*float64_eps=1.4210854715202004e-14`. Mean fitting objective:
  binary cross entropy plus `sum(w**2)/(2*C*8644)`; unpenalized intercept.
  `tol` is a stopping input, not a claimed score or gradient guarantee.
- Both classes required before fitting; any ConvergenceWarning blocks completion,
  with no retries or adaptive changes to labels, iterations or C.
- Policies exactly `p >= .50` and `p >= .30`. Equality is positive. These custom
  comparisons differ from sklearn's binary built-in `z>0` prediction at z=0.
  No winning threshold, new costs, precision/recall or tuning.

## Partition identity and final-period boundary

The byte-identical source helper and partition helper are standalone copies of
#21. Exact ordered-ID SHA-256, counts, first/last timestamps, readiness-excluded
IDs and first development issuance match the original #21 manifest. The copied
identity projection deliberately excludes its old regression contract.

- Eligible training: **8,644** rows, 2011-01-01 00:00 through
  2011-12-31 22:00; ordered-ID hash
  `3d4ee7e6bd7caf76c004213eefcf2d3ed7c3bb9dca03a800ae723f949b5e695e`.
- Development: **4,358** rows, 2012-01-01 00:00 through
  2012-06-30 23:00; ordered-ID hash
  `01acde00b1aed53f4f42e2ba3727ad6f9a021ed69a4db61f18ac2cb9730dad74`.
- Reserved final metadata: **4,376** IDs/times, 2012-07-01 00:00 through
  2012-12-31 23:00; ordered-ID hash
  `a7717b2b28a7398ad331b7cb3bc1fc7b0931e88cc2e446806fc405e45a03342e`.
- One readiness exclusion: source instant **8645**, 2011-12-31 23:00;
  ordered-ID hash
  `01bebfc6b17a14a55a7b2759c31e125fde800e5d70f9c4142f221dd6b1bfb580`.
  First development issuance is 2011-12-31 23:00. Training t is eligible only
  when `t+1h <= issuance`, so the last included training label meets equality.

No final-period labels, class balance, fitted inputs, predictions or scores were
created. The inherited parser still mechanically validates count fields across
the official source, including the reserved period. Final targets are therefore
not literally unseen. This is integrity access, not period-specific analysis.

## Measurements — paired raw scores and decisions

Only train/development label counts were computed:

- Training: **6,488 class 0 / 2,156 class 1**, total 8,644.
- Development: **2,516 class 0 / 1,842 class 1**, total 4,358.
- Fitted dummy P(1): **0.24942156409069874**, held constant on every row.
- Both estimators' `classes_ = [0,1]`; independently mapped label-1 column = 1.
- Logistic `n_iter_ = [44]`; dummy/logistic captured fit warnings: **[] / []**.
  Sigmoid versus API probability agreement passed `rtol=atol=1e-12`.

Primary metric is mean binary **log loss**, natural log, explicit `labels=[0,1]`,
float64 `[P(0),P(1)]` columns, identical rows for both models. scikit-learn 1.7.2
clips probabilities internally to `[eps,1-eps]`,
`eps=2.220446049250313e-16`, without post-clipping renormalization. No fitting
penalty is added to evaluation loss; saved scores remain raw/unclipped.

- Training dummy log loss: **0.5616987751263304**.
- Training logistic log loss: **0.3027283799058408**.
- Development dummy log loss: **0.7525675653050563**.
- Development logistic log loss: **0.6510039000235885**.

Fixed policy counts, positive decisions at .50 / .30:

- Training logistic: **1,858 / 3,016**; **1,158** changed decisions.
- Development logistic: **680 / 1,110**; **430** changed decisions.
- Training dummy: **0 / 0**; **0** changed decisions.
- Development dummy: **0 / 0**; **0** changed decisions.

Lowering the policy threshold changes decisions without changing weights, scores
or their log loss. Logistic has lower development log loss on these rows. This
does not establish a preferred threshold, calibrated probabilities, cost savings,
serving readiness or improvement over #21's different regression task.

## First actual development-row trace

Stable ID:
`e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f:8646`.
Time: **2012-01-01 00:00:00**. Allowed inputs: hour 0, month 1,
date-derived Monday-zero weekday 6.

`trace.json` records **all 40** encoded terms, each feature name, encoded value,
weight and product. On this row only `weekday_mon0_6` is 1; the other 39 retained
indicators are 0 (hour 0 and month 1 are dropped references).

- Intercept: **−5.6838977772991415**.
- Nonzero contribution: `1 * 0.48934334824037506`.
- Weighted sum and raw `decision_function` z: **−5.194554429058766**.
- Sigmoid and mapped logistic P(1): **0.005516091174759622**.
- Observed derived label: **0**.
- Logistic decisions at .50 / .30: **0 / 0**.
- Dummy P(1): **0.24942156409069874**; dummy decisions: **0 / 0**.

The row is selected by earliest inherited order, not by a changed decision or
an impressive prediction. Its coincident policies are preserved.

## Synthetic arithmetic receipts — not measured model results

`synthetic.json` was executed independently of model measurements:

- `−1 + 0.5*2 = 0` (illustrative one-input weighted sum).
- `sigmoid(0) = 0.5`.
- `ln(3) = 1.0986122886681098`; `sigmoid(ln(3)) = 0.75`.
- At y=1: `−ln(.8)=0.2231435513142097` versus
  `−ln(.2)=1.6094379124341003` (0.2231 versus 1.6094, rounded to four decimals).
- p=.40 gives decisions **0 / 1** at .50 / .30.
- Exact p=.50 gives **1 / 1**; exact p=.30 gives **0 / 1**.

These calculations do not describe event frequencies or fitted parameters.

## Runtime and verification

- CPython **3.13.9**, NumPy **2.2.6**, pandas **2.3.3**, scikit-learn **1.7.2**,
  SciPy **1.16.3**, PyArrow **21.0.0**, pytest **8.4.2**, threadpoolctl **3.6.0**.
- Windows 11 build 26300; processor string
  `AMD64 Family 25 Model 24 Stepping 1, AuthenticAMD`; **192 logical CPUs**
  reported by the host, with computation restricted to **1 native thread**.
  NumPy OpenBLAS 0.3.29, SciPy OpenBLAS 0.3.29.dev and OpenMP each reported 1.
  Threadpool architecture strings are library metadata, not a CPU-model claim.
- First official-download run: **18.28263710000101 s** inside `run()`.
  This excludes interpreter/import startup and environment installation.
- One additional identical cached-source run: **0.39720499999748426 s** inside
  `run()`; combined two-estimator fitting: **0.018188599999120925 s**.
  Second-run time/environment metadata overwrite the report's runtime section;
  first-run elapsed time above is retained from terminal output. No third fit run.
- Full pytest: **12 passed in 2.88 s**, including mandatory real integration.
  No skips. It reads produced artifacts, not a mock experiment or another fit run.
- An additional read-only verification compared both helper files byte-for-byte
  and all partition identity fields directly against original #21 files: **MATCH**.
  The documented #23 consumer's hash/order/schema/policy checks executed on the
  actual saved development table: **4,358 rows, c=211.0**, passed. Git ignore
  checks confirmed ZIP, all three Parquet files and the virtual environment are
  ignored; the staged diff is empty.
- Repeat material fingerprint, identical on both runs:
  `fa6bceb3979dd7a4e1533ca32a006693d922e4b6af691b76ce48b06c895ef1d6`.
  All weights, scores, policy counts, metrics, frozen state, output Parquet bytes
  and deterministic trace matched exactly; runtime metadata are excluded.

## Input/output lineage and local #23 handoff

- Official ZIP SHA-256:
  `b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401`.
- Official `hour.csv` SHA-256:
  `e03de4ee4ef4dc376ac6e04bf829673c6269e8eba5c60fa121640fa2f829504f`.
- Byte-identical inherited `dataset.py` SHA-256:
  `beca12d7b9df34179a269fdc3fefa4d9fb9f5d40efd7bb9c9d7d0555abe758a7`.
- Python code aggregate SHA-256 (sorted filenames, NUL, file bytes):
  `fc4ad0f7f62a60c57bbcdcbfb9d9de57fff4e8f0280855c9b170cafa37c2490d`.
- Frozen config byte SHA-256:
  `574612fb661405b5e7af0d76f190a770ae3fa07c5afd34c21613a7af279c2148`.
- Label config byte SHA-256:
  `12a1e534d7c0f0c3a10863ddad954d15a954d7108c328ecfd613390902b626ce`.
- Train predictions byte SHA-256:
  `e2753e48a8e860d6c955984b944d4eba3a49c5e6d66f385c669ecd3c3e015318`.
- Development predictions byte SHA-256:
  `d20fcc17671f4165adc520d1ed96781e703785845ce4a6db269d4aeb9dfd1297`.
- Development predictions canonical logical SHA-256:
  `25511ba6c426b1d98ea3f70b0c10faf5211a39a044f935ba1446d8f59dd08101`.
- Full 40-term trace byte SHA-256:
  `2c9aa12a865236cb08c9383cae4813660ec9c6e77fd8f180dcf15bacf99e6496`.

Both prediction tables are ignored local Parquet: `data/train-predictions.parquet`
and **`data/validation-predictions.parquet`**. The latter is the 4,358-row #23
handoff, with stable ID/time, true binary label, raw P(1), raw z, both decisions,
and dummy probability/decisions. It contains no `cnt` or original calendar-input
columns, and no final rows. Compact portable `report.json` supplies all recipe,
score/parameter metadata and hashes; README supplies full reproduction plus a
read-only verified consumer. Reproduce locally if ignored files are absent.

Derived prediction publication is allowed by the user's stated policy in
principle; this delivery deliberately uses local ignored tables rather than
publishing any dataset/table. There is no CSV upload, downloaded dataset in
versioned artifacts, staged file, commit or public push.

## Source caveats and attribution

UCI Bike Sharing: Hadi Fanaee-T (2013), DOI `10.24432/C5W894`, **CC BY 4.0**.
Retain the README-requested Fanaee-T/Gama paper citation and links in README.
Changes here are parsing/order, derived calendar feature, partitions, binary
labels and model outputs. The official `cnt` is recorded total rentals, not
capacity, unmet demand or a natural binary event.

The UCI catalog's 17,389 description differs from the archive README and verified
**17,379** records in `hour.csv`; missing calendar coordinates are not filled. Source
weekday coding is not silently reused as the Monday-zero feature. Timezone/DST,
aggregation endpoints and historical as-of availability remain unverified.
Catalog/README season-name and temperature-normalization conflicts remain
unresolved; none of those fields is a model input or denormalized here.
Naive source-calendar interval-start labels, a one-hour forecast lead, zero
reporting delay and equality readiness are inherited hypothetical assumptions.
The whole-source mechanical count-access qualification remains explicit.

Reference coding and bounded scores do not prove calibration; this experiment
does not fit calibration or choose an operational policy. All evidence is for
the frozen derived task and allowed rows above.
