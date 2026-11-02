# #20 — observed validation-boundary results

Executed 2026-11-01, sequentially after #19. Contract: `protocol.json`,
created before **any** fitting. Exact partition receipts: `partitions.json`
and ignored `data/partitions.parquet`. Full observations: `report.json`.

## Fixed partitions and availability

| Partition | Rows | Target-label window / qualification |
|---|---:|---|
| Nominal training | 8,645 | 2011 calendar year |
| Eligible training | 8,644 | Through 2011-12-31 22:00 |
| Readiness exclusion | 1 | 2011-12-31 23:00, source ID 8645 |
| Development validation | 4,358 | [2012-01-01, 2012-07-01) |
| Reserved final | 4,376 | [2012-07-01, end] |

Predeclared from documented 2011–2012 coverage and user-prescribed dates,
not selected by scores. First development issuance is **2011-12-31 23:00**.
Label `t` denotes `[t,t+1h)` by explicit convention; issue at `t−1h` and
hypothetically observe outcome at `t+1h` with zero reporting delay. Equality
is allowed: training 22:00 completes exactly at first issuance; 23:00 does not.
The code uses actual timestamps, not a fixed row-count gap. All IDs and calendar
labels are pairwise disjoint, ordered and accounted for, including exclusion.

The calendar allowlist is exactly `hr`, `mnth`, derived `weekday_mon0`.
Target/components, weather, season, holiday, workingday, year and IDs are excluded.
The first development record is memberSHA:8646, 2012-01-01 00:00:
**5 casual + 43 registered = 48 total**. This is an arithmetic example, not a
leaky forecast model. #19 independently checked the component identity on all
17,379 rows; no period-specific reserved target outcome is reported here.

## Synthetic full-entry experiment

Fresh `prepare_fit(train, validation)` runs with the prescribed training and
validation A/B fixtures produced identical actual learned state:

- Mean imputer: **1**.
- Scaler mean: **1**; variance **0.6666666666666666**; scale **0.816496580927726**.
- Encoder vocabulary: **a,b**, trained on three rows.
- Transformed training rows: `[-1.224744871391589,1,0]`,
  `[1.224744871391589,0,1]`, `[0,1,0]`.
- Transforming validation did not mutate any captured state. Unknown category
  `sentinel_new` has a zero categorical block; it did not enter the vocabulary.
- Deliberately invalid full-data fitting **failed invariance**: imputer means
  **2 versus 334**, scaler variances **1.6 versus 133067.2**; B vocabulary adds
  `sentinel_new`. The negative control is required to fail, not hand-waved away.
- Changing the training value 2→6 changes valid mean-imputer/scaler mean to **3**,
  variance to **6**. Separate numeric-only and category-only perturbation tests
  also detect invalid fitting and preserve valid fitting.

No bike-demand estimator or score was needed. The synthetic preparation entry
is a boundary demonstration; these checks do not prove absence of every custom
or external leakage route. The real calendar-only baseline needs no imputer or
scaler. That distinction is intentional.

Latest experiment wall time **0.530 seconds**, verified local archive read through
partition persistence and sentinel. Tests: **7 passed in 1.76s**.
Python 3.13.12, numpy 2.2.6, pandas 2.3.3, scikit-learn 1.7.2, pytest 8.4.2,
pyarrow 21.0.0, scipy 1.18.1; API behavior verified locally, not inferred from
research's later-version documentation labels.

## Qualifications and remaining gates

Naive source-calendar arithmetic is not proof of real elapsed-hour lead, UTC,
DST, source interval alignment or reporting latency. These source facts remain
unresolved; this is an explicitly hypothetical retrospective evaluation.
**Final targets are unscored, not literally unseen:** #19's whole-source
mechanical schema/domain/component audit read them before the protocol; the
independent command repeats those mechanical checks. No final fitting, model
predictions, scores or target-specific diagnostics are produced. #25 must later
lock selection/refit/report authorization before final evaluation. No score-driven
window changes or target-distribution cleaning occurred.

## Exact execution

Working directory: `content/issues/020-leakage-safe-validation/code`.

```powershell
uv run --python "C:/Users/Imtiaz/AppData/Local/Temp/opencode/ml-foundations-313/Scripts/python.exe" --no-project python experiment.py --archive "C:/Users/Imtiaz/AppData/Local/Temp/opencode/019-bike-sharing-dataset-2026-11-01.zip"
uv run --python "C:/Users/Imtiaz/AppData/Local/Temp/opencode/ml-foundations-313/Scripts/python.exe" --no-project python -m pytest -q
```

Independent setup, attribution and changes: [README.md](README.md). Dataset/schema
and partition hashes in the JSON receipts identify exact records/configuration.
