# #025: Many weak trees, one honest score

Companion code for the Veqtors issue. It boosts trees on the UCI Concrete Compressive Strength data, tunes them with Optuna's Gaussian-process sampler against random search, and scores everything on folds that keep each recipe whole. Results: `RESULTS.md`. Every number the issue quotes is in `outputs/report.json`.

## Run it

Needs [uv](https://docs.astral.sh/uv/). From this folder:

```bash
uv sync
uv run python toy.py        # the issue's by-hand arithmetic (synthetic rows), asserted
uv run python partition.py  # once: seals 20% of recipes as the test set
uv run python run.py        # about 10 minutes on one core
uv run pytest -q
```

`run.py` refuses to start if `outputs/test_ledger.json` exists, because that file means the test set has already been opened. To reproduce from scratch, delete `outputs/` and `partitions.json` and run all three steps.

## Files

- `model-config.json`: seeds, search space, budget, samplers, decision rule and test protocol. It was written by hand before any model was fit.
- `common.py`: data loading, recipe ids, the `SealedTest` guard, fold builders and the model factory.
- `partition.py` → `partitions.json`: the test recipe ids.
- `run.py` → `outputs/`: `report.json`, `decision.json` (written before the test opens), `test_ledger.json`, `test_predictions.csv`, `trials_gp.csv`, `trials_random.csv`, `trials_gp_shuffled.csv`, `one_knob_demo.json` (trials, surrogate mean and SD, Optuna's logEI and EI in MPa on a 201-point grid; the source for diagram d4).
- `toy.py` → `outputs/toy.json`: the six-row and five-row teaching tables. These rows are invented. They are not UCI data.
- `tests/test_guards.py`: no recipe crosses train/test, the outer folds, or any inner fold; shuffled folds do leak recipes; the test guard opens once; the run opened the test exactly once and refuses a second opening; the toy arithmetic holds.

## Provenance

- Data: UCI id 165 via `ucimlrepo` 0.0.7, cached as `data/concrete.csv`. SHA-256 `3a8e1fe4362dc3fbff27ef2eaa42c8390ad970cdb6931479876f47dd23ead7d5`. Licence CC BY 4.0. Cite Yeh, I-C. (1998), *Cement and Concrete Research* 28(12):1797–1808.
- `partitions.json` SHA-256 `1927957ed4498934a0fcacdb6f23d7fe40a592ff766868136bad39138ac61a59`. `model-config.json` SHA-256 `c9026e760cc4cd710ed90fc3cc594d81abf1dea3d50753daf0ecf35bac0afa34`.
- Versions: Python 3.13.12, scikit-learn 1.9.1, Optuna 5.0.0, torch 2.15.0 (CPU), scipy 1.18.1, numpy 2.5.4, pandas 3.1.1. Exact pins: `pyproject.toml`, `uv.lock`, `requirements.txt`.
- `OMP_NUM_THREADS=1`, `torch.set_num_threads(1)`, `n_jobs=1`. Optuna logged that `greenlet` was missing and used sequential L-BFGS-B for the acquisition search. That affects speed only.

## Choices and limits

- **Recipe = exact tuple of the seven ingredient values.** The data has 25 exact duplicate rows. Rounding ingredients to whole kg/m³ would merge 427 recipes into 355, so some near-identical mixes still land on different sides of a fold. Grouping is therefore a lower bound on how strict the split could be.
- **Folds:** `GroupKFold(5, shuffle=True, random_state=25)` for inner and outer loops; the outer folds equal the inner folds of the full search, so default boosting has the same five scores in both views. The shuffled check uses `KFold(5, shuffle=True, random_state=25)`.
- **Model:** `HistGradientBoostingRegressor(loss="squared_error", early_stopping=False, random_state=25)`. Training loss is squared error; every score is MAE.
- **Samplers:** `GPSampler(seed=25, n_startup_trials=10, deterministic_objective=True)` (logEI acquisition) and `RandomSampler(seed=25)`, 40 trials each. Both studies share the same first 10 random trials. One seed only, so the GP-versus-random comparison is one run, not a benchmark.
- **The one-knob demo** subclasses `GPSampler._optimize_acqf` (the hook Optuna's source names for overrides) to record the fitted GP and its acquisition at each pick. Values are converted from Optuna's standardized scale back to MPa. The grid argmax of EI in MPa matches the argmax of Optuna's logEI, and the recorded next pick equals the trial Optuna ran.
- **Search-range edges:** the GP's best settings sit on the edge of every range in the config. A wider space might do better and would cost more fits; this run does not test that.
- **Decision rule** (pre-registered in the config) passed by 0.003 MPa. Treat the tuned and default models as close.
- **Test noise:** recipe-level bootstrap (2,000 resamples) of the test MAE is in `report.json`.
