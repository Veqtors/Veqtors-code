# #025 results: Many weak trees, one honest score

All numbers are from `outputs/report.json` (one run, seed 25, 2026-11-05). MAE in MPa; lower is better.
The test set (85 recipes, 211 rows) was opened once, after the decision in `outputs/decision.json` was written.

## Data

- 1,030 rows, 427 distinct recipes (seven ingredient columns). 181 recipes have more than one row; together they hold 784 rows. The most-tested recipe has 20 rows.
- Training: 819 rows, 342 recipes. Test: 211 rows, 85 recipes.
- Example training recipe R017 (cement 139.6, slag 209.4, water 192.0 kg/m³): 8.06 MPa at 3 days, 14.59 at 7, 28.24 at 28, 39.36 at 90, 44.21 at 180, 44.70 at 360.

## Grouped 5-fold CV on training recipes (mean ± fold SD)

- Median: 13.48 ± 1.01
- Linear regression: 8.67 ± 0.38
- Default boosting: 4.77 ± 0.41
- Random-search best (40 trials): 4.54 ± 0.32 (found at trial 10 of 40, the last of the 10 shared random start-up trials)
- GPSampler best (40 trials): 4.19 ± 0.37 (found at trial 37 of 40)

The GP and random studies share their first 10 trials (GPSampler's start-up sampler is `RandomSampler(seed=25)`). After those, random search found nothing better than 4.54; the GP search improved at trials 30, 31, 34 and 37 (1-based).

GP best settings: learning_rate 0.5, max_iter 800, max_leaf_nodes 4, min_samples_leaf 2, l2_regularization 10. Every one sits on an edge of the search range.

## Optimism from shuffled folds

- Default boosting: 3.17 shuffled vs 4.77 grouped (gap 1.60).
- GP search on shuffled folds: best 2.73. The same settings scored on grouped folds: 4.53 (gap 1.80). The shuffled search also picked different settings.

## Nested CV (outer grouped folds around the whole GP search)

- Tuned procedure: 4.41 ± 0.45. Best inner score of the full search: 4.19. Selection gap: 0.23.
- Default boosting on the same outer folds: 4.77. Paired gain per fold: 0.16, 0.07, 0.84, 0.61, 0.09; mean 0.353, SD 0.350.
- Pre-registered rule (gain mean > gain SD): passed by 0.003, so the final model is the GP-tuned one.

## One test opening (211 rows)

- Median 13.30 · linear 7.46 · default boosting 4.15 · random-tuned 3.85 · GP-tuned (final) 4.09 · GP tuned on shuffled folds 3.76.
- Recipe-bootstrap 95% range of the final model's test MAE: 3.22 to 5.14 (linear: 6.70 to 8.21).
- Median-error row: R402 at 7 days (cement 469, water 137.8): actual 54.9; linear 69.7, default 45.9, final 58.1.
- Largest-error row: R205 at 28 days (cement 252.3, water 146.3): actual 50.6; linear 36.8, default 41.5, final 31.0.

## Other checks

- Flat extrapolation: the final model predicts 40.91 MPa for the oldest training row at 365, 730 and 3,650 days; linear predicts 68.0, 109.7 and 443.4.
- One-knob GP demo (learning rate only): after 6 trials (best 4.68 at 0.098), the GP's next pick was 0.5, where its mean was 4.89 and its SD 0.255; EI = 0.029. That trial scored 5.08. The pick after it (0.113) scored 4.63, the demo's best.
- Compute: 1,711 model fits, 627 s wall time single-threaded; nested CV alone took 379 s.
