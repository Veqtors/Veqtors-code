"""Issue #025 pipeline: baselines, two searches, optimism checks, nested CV, one test opening.

    uv run python partition.py   # once
    uv run python run.py
"""
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")

import json
import math
import platform
import sys
import time

import numpy as np
import optuna
import pandas as pd
import scipy
import sklearn
import torch
from scipy.stats import norm
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression

from common import (CONFIG, DATA, FEATURES, OUT, PARTITIONS, TARGET, grouped_folds, hgb,
                    load_config, load_frame, recipe_stats, sha256, shuffled_folds, split)

optuna.logging.set_verbosity(optuna.logging.WARNING)
import warnings
warnings.filterwarnings("ignore", category=optuna.exceptions.ExperimentalWarning)
torch.set_num_threads(1)

cfg = load_config()
SEED = cfg["seed"]
BUDGET = cfg["search"]["trial_budget"]
SPACE = cfg["search_space"]
if os.environ.get("SMOKE_DIR"):          # quick wiring check only; never the reported run
    import pathlib
    BUDGET, OUT = 11, pathlib.Path(os.environ["SMOKE_DIR"])
OUT.mkdir(exist_ok=True)
LEDGER = OUT / "test_ledger.json"
if LEDGER.exists():
    raise SystemExit("outputs/test_ledger.json exists: the test set was already opened. "
                     "Delete outputs/ only to reproduce the whole run from scratch.")

part = json.loads(PARTITIONS.read_text(encoding="utf-8"))
data_hash = sha256(DATA)
assert data_hash == part["data_sha256"], "data file changed since the partition was made"

FITS = {"count": 0}
T0 = time.perf_counter()
timings = {}


def cv(make_model, frame, folds):
    X, y = frame[FEATURES].to_numpy(), frame[TARGET].to_numpy()
    scores = []
    for tr, va in folds:
        model = make_model().fit(X[tr], y[tr])
        FITS["count"] += 1
        scores.append(float(np.mean(np.abs(model.predict(X[va]) - y[va]))))
    return scores


def summary(scores):
    return {"mean": float(np.mean(scores)), "sd": float(np.std(scores, ddof=1)), "folds": scores}


def suggest(trial):
    p = {}
    for name, s in SPACE.items():
        if s["type"] == "int":
            p[name] = trial.suggest_int(name, s["low"], s["high"], log=s["log"])
        else:
            p[name] = trial.suggest_float(name, s["low"], s["high"], log=s["log"])
    return p


def gp_sampler(seed=SEED, startup=10, cls=optuna.samplers.GPSampler):
    return cls(seed=seed, n_startup_trials=startup, deterministic_objective=True)


def search(sampler, frame, folds, n_trials, space_fn=suggest):
    log = []

    def objective(trial):
        params = space_fn(trial)
        scores = cv(lambda: hgb(params, SEED), frame, folds)
        log.append({"trial": trial.number, **params, "mae": float(np.mean(scores)),
                    "fold_sd": float(np.std(scores, ddof=1))})
        return float(np.mean(scores))

    study = optuna.create_study(direction="minimize", sampler=sampler)
    study.optimize(objective, n_trials=n_trials, n_jobs=1)
    best = min(log, key=lambda r: r["mae"])
    params = {k: best[k] for k in SPACE if k in best}
    return {"best_params": params, "best_mae": best["mae"], "best_trial": best["trial"],
            "log": log, "best_so_far": list(np.minimum.accumulate([r["mae"] for r in log]))}


# ---------------------------------------------------------------- data
df = load_frame()
stats = recipe_stats(df)
train, sealed = split(df)
assert not set(train["recipe"]) & set(part["test_recipes"])
inner = grouped_folds(train, SEED)
shuffled = shuffled_folds(train, SEED)

example = None  # one recipe tested once at each of several ages (training rows only)
for rid, g in train.groupby("recipe"):
    if g["Age"].nunique() >= 5 and g["Age"].is_unique:
        example = {"recipe": rid, **{c: float(g.iloc[0][c]) for c in FEATURES[:-1]},
                   "tests": [{"age": int(a), "mpa": float(s)} for a, s in
                             zip(g.sort_values("Age")["Age"], g.sort_values("Age")[TARGET])]}
        break

# ---------------------------------------------------------------- baselines
t = time.perf_counter()
makers = {
    "median": lambda: DummyRegressor(strategy="median"),
    "linear": LinearRegression,
    "default_boosting": lambda: hgb({}, SEED),
}
baselines = {k: summary(cv(m, train, inner)) for k, m in makers.items()}
default_shuffled = summary(cv(makers["default_boosting"], train, shuffled))
timings["baselines_s"] = time.perf_counter() - t

# ---------------------------------------------------------------- full searches
t = time.perf_counter()
bo = search(gp_sampler(), train, inner, BUDGET)
timings["gp_search_s"] = time.perf_counter() - t
t = time.perf_counter()
rs = search(optuna.samplers.RandomSampler(seed=SEED), train, inner, BUDGET)
timings["random_search_s"] = time.perf_counter() - t
t = time.perf_counter()
bo_shuf = search(gp_sampler(), train, shuffled, BUDGET)
timings["gp_search_shuffled_s"] = time.perf_counter() - t
bo_grouped_scores = summary(cv(lambda: hgb(bo["best_params"], SEED), train, inner))
rs_grouped_scores = summary(cv(lambda: hgb(rs["best_params"], SEED), train, inner))
shuf_pick_on_grouped = summary(cv(lambda: hgb(bo_shuf["best_params"], SEED), train, inner))


# ---------------------------------------------------------------- one-knob demo for d4
class RecordingGPSampler(optuna.samplers.GPSampler):
    """GPSampler that records its surrogate and acquisition on a grid each time it picks."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self.snapshots = []

    def _optimize_acqf(self, acqf, best_params):
        x_next = super()._optimize_acqf(acqf, best_params)
        grid = np.linspace(0.0, 1.0, 201)[:, None]
        with torch.no_grad():
            mean, var = acqf._gpr.posterior(torch.from_numpy(grid))
        self.snapshots.append({
            "grid": grid[:, 0].tolist(), "mean_std": mean.numpy().tolist(),
            "var_std": var.numpy().tolist(),
            "log_acq": acqf.eval_acqf_no_grad(grid).tolist(),
            "train_x": acqf._gpr._X_train[:, 0].numpy().tolist() if hasattr(acqf._gpr, "_X_train") else None,
            "next_norm": float(np.asarray(x_next).ravel()[0]),
        })
        return x_next


demo_cfg = cfg["one_knob_demo"]
lo, hi = SPACE["learning_rate"]["low"], SPACE["learning_rate"]["high"]
to_lr = lambda u: math.exp(math.log(lo) + u * (math.log(hi) - math.log(lo)))
t = time.perf_counter()
rec = RecordingGPSampler(seed=SEED, n_startup_trials=4, deterministic_objective=True)
demo = search(rec, train, inner, demo_cfg["trials"],
              space_fn=lambda tr: {"learning_rate": tr.suggest_float("learning_rate", lo, hi, log=True)})
timings["one_knob_demo_s"] = time.perf_counter() - t
k = demo_cfg["surrogate_snapshot_after_trial"]          # trials seen by this snapshot
snap = rec.snapshots[k - 4]                              # first GP pick happens after 4 startup trials
seen = np.array([r["mae"] for r in demo["log"][:k]])
m, s = np.mean(-seen), np.std(-seen)
mean_mae = [-(v * s + m) for v in snap["mean_std"]]
sd_mae = [math.sqrt(max(v, 0.0)) * s for v in snap["var_std"]]
f_best = float(seen.min())
ei = []
for mu, sd in zip(mean_mae, sd_mae):
    if sd <= 1e-12:
        ei.append(max(f_best - mu, 0.0))
    else:
        z = (f_best - mu) / sd
        ei.append(float((f_best - mu) * norm.cdf(z) + sd * norm.pdf(z)))
nxt_u = snap["next_norm"]
gi = int(round(nxt_u * 200))
mu_n, sd_n = mean_mae[gi], sd_mae[gi]
z_n = (f_best - mu_n) / sd_n
demo_out = {
    "trials": demo["log"],
    "snapshot_after_trials": k,
    "grid_learning_rate": [to_lr(u) for u in snap["grid"]],
    "surrogate_mean_mae": mean_mae, "surrogate_sd_mae": sd_mae,
    "optuna_log_ei_standardized": snap["log_acq"], "expected_improvement_mae": ei,
    "next_pick_learning_rate": to_lr(nxt_u),
    "next_pick_trial_mae": demo["log"][k]["mae"],
    "best_seen_mae": f_best,
    "ei_substitution_at_next_pick": {"f_best": f_best, "mu": mu_n, "sigma": sd_n, "z": z_n,
                                     "Phi_z": float(norm.cdf(z_n)), "phi_z": float(norm.pdf(z_n)),
                                     "ei": ei[gi]},
    "grid_argmax_ei_learning_rate": to_lr(snap["grid"][int(np.argmax(ei))]),
    "grid_argmax_optuna_acq_learning_rate": to_lr(snap["grid"][int(np.argmax(snap["log_acq"]))]),
}
assert abs(demo_out["next_pick_learning_rate"] - demo["log"][k]["learning_rate"]) < 1e-9 * 10 + 1e-6, \
    "snapshot does not line up with the trial it picked"

# ---------------------------------------------------------------- nested CV
t = time.perf_counter()
outer = grouped_folds(train, SEED)
nested = {"tuned": [], "default_boosting": [], "linear": [], "median": [], "best_inner": [], "params": []}
for o, (otr, ova) in enumerate(outer):
    a, b = train.iloc[otr].reset_index(drop=True), train.iloc[ova].reset_index(drop=True)
    assert not set(a["recipe"]) & set(b["recipe"])
    res = search(gp_sampler(), a, grouped_folds(a, SEED), BUDGET)
    nested["best_inner"].append(res["best_mae"])
    nested["params"].append(res["best_params"])
    pair = [(np.arange(len(a)), np.arange(len(a), len(a) + len(b)))]
    both = pd.concat([a, b], ignore_index=True)
    nested["tuned"] += cv(lambda: hgb(res["best_params"], SEED), both, pair)
    for name in ("default_boosting", "linear", "median"):
        nested[name] += cv(makers[name], both, pair)
timings["nested_cv_s"] = time.perf_counter() - t
gains = np.array(nested["default_boosting"]) - np.array(nested["tuned"])
decision = {
    "paired_gain_mean": float(gains.mean()), "paired_gain_sd": float(gains.std(ddof=1)),
    "gains": gains.tolist(),
}
decision["keep_tuned"] = bool(decision["paired_gain_mean"] > decision["paired_gain_sd"])
decision["final_model"] = "gp_tuned_boosting" if decision["keep_tuned"] else "default_boosting"
(OUT / "decision.json").write_text(json.dumps(decision, indent=1))   # written before the test opens

# ---------------------------------------------------------------- one test opening
X, y = train[FEATURES].to_numpy(), train[TARGET].to_numpy()
final_models = {
    "median": makers["median"]().fit(X, y),
    "linear": LinearRegression().fit(X, y),
    "default_boosting": hgb({}, SEED).fit(X, y),
    "random_tuned_boosting": hgb(rs["best_params"], SEED).fit(X, y),
    "gp_tuned_boosting": hgb(bo["best_params"], SEED).fit(X, y),
    "gp_tuned_on_shuffled_folds": hgb(bo_shuf["best_params"], SEED).fit(X, y),
}
FITS["count"] += len(final_models)
test = sealed.open()
LEDGER.write_text(json.dumps({"openings": sealed.openings, "rows": int(len(test)),
                              "opened_at_s": time.perf_counter() - T0}))
Xt, yt = test[FEATURES].to_numpy(), test[TARGET].to_numpy()
preds = {k: mdl.predict(Xt) for k, mdl in final_models.items()}
test_scores = {k: float(np.mean(np.abs(p - yt))) for k, p in preds.items()}
pred_frame = test[["recipe"] + FEATURES + [TARGET]].copy()
for k, p in preds.items():
    pred_frame[k] = p
pred_frame.to_csv(OUT / "test_predictions.csv", index=False)
err = np.abs(preds[decision["final_model"]] - yt)
order = np.argsort(err)
named = []
for label, idx in (("median_error", order[len(order) // 2]), ("max_error", order[-1])):
    row = pred_frame.iloc[idx]
    named.append({"which": label, "recipe": row["recipe"], "age": int(row["Age"]),
                  "cement": float(row["Cement"]), "water": float(row["Water"]),
                  "actual": float(row[TARGET]), **{k: float(row[k]) for k in preds}})
# bootstrap the final model's and linear's test MAE over test recipes (noise of one opening)
rng = np.random.default_rng(SEED)
recipes = test["recipe"].to_numpy()
uniq = np.unique(recipes)
boot = {k: [] for k in ("final", "linear")}
idx_by = {r: np.where(recipes == r)[0] for r in uniq}
for _ in range(2000):
    pick = np.concatenate([idx_by[r] for r in rng.choice(uniq, size=len(uniq), replace=True)])
    boot["final"].append(float(np.mean(err[pick])))
    boot["linear"].append(float(np.mean(np.abs(preds["linear"][pick] - yt[pick]))))
test_noise = {k: {"p2_5": float(np.percentile(v, 2.5)), "p97_5": float(np.percentile(v, 97.5))}
              for k, v in boot.items()}

# ---------------------------------------------------------------- flat extrapolation (training row)
probe = train.iloc[[int(np.argmax(train["Age"]))]][FEATURES].copy()
ages = [365, 730, 3650]
flat = {}
for a in ages:
    probe["Age"] = a
    flat[a] = {"boosting": float(final_models[decision["final_model"]].predict(probe.to_numpy())[0]),
               "linear": float(final_models["linear"].predict(probe.to_numpy())[0])}

# ---------------------------------------------------------------- write
total_s = time.perf_counter() - T0
report = {
    "versions": {"python": platform.python_version(), "scikit-learn": sklearn.__version__,
                 "optuna": optuna.__version__, "torch": torch.__version__, "scipy": scipy.__version__,
                 "numpy": np.__version__, "pandas": pd.__version__},
    "hashes": {"data_sha256": data_hash, "partitions_sha256": sha256(PARTITIONS),
               "model_config_sha256": sha256(CONFIG)},
    "dataset": stats,
    "partition": {"train_rows": int(len(train)), "train_recipes": int(train["recipe"].nunique()),
                  "test_rows": int(len(test)), "test_recipes": int(test["recipe"].nunique())},
    "example_recipe": example,
    "grouped_cv": baselines,
    "default_boosting_shuffled_cv": default_shuffled,
    "search": {
        "budget": BUDGET,
        "gp": {k: bo[k] for k in ("best_params", "best_mae", "best_trial", "best_so_far")},
        "random": {k: rs[k] for k in ("best_params", "best_mae", "best_trial", "best_so_far")},
        "gp_shuffled_folds": {k: bo_shuf[k] for k in ("best_params", "best_mae", "best_trial")},
        "gp_best_rescored_grouped": bo_grouped_scores,
        "random_best_rescored_grouped": rs_grouped_scores,
        "shuffled_pick_scored_on_grouped": shuf_pick_on_grouped,
        "optimism_gap_search_mae": shuf_pick_on_grouped["mean"] - bo_shuf["best_mae"],
        "optimism_gap_default_mae": baselines["default_boosting"]["mean"] - default_shuffled["mean"],
    },
    "nested_cv": {**{k: summary(v) for k, v in nested.items() if k not in ("params", "best_inner")},
                  "best_inner_per_outer": nested["best_inner"], "params_per_outer": nested["params"],
                  "selection_gap_vs_full_search_best": float(np.mean(nested["tuned"])) - bo["best_mae"],
                  "selection_gap_vs_own_inner": float(np.mean(nested["tuned"]) - np.mean(nested["best_inner"]))},
    "decision": decision,
    "test": {"openings": sealed.openings, "rows": int(len(test)), "mae": test_scores,
             "named_errors": named, "bootstrap_95": test_noise},
    "flat_extrapolation_ages": flat,
    "one_knob_demo": {k: v for k, v in demo_out.items() if k not in
                      ("grid_learning_rate", "surrogate_mean_mae", "surrogate_sd_mae",
                       "optuna_log_ei_standardized", "expected_improvement_mae")},
    "compute": {"fits": FITS["count"], "wall_time_s": total_s, "timings_s": timings,
                "machine": platform.processor(), "n_jobs": 1,
                "omp_num_threads": os.environ.get("OMP_NUM_THREADS")},
}
(OUT / "report.json").write_text(json.dumps(report, indent=1))
(OUT / "one_knob_demo.json").write_text(json.dumps(demo_out, indent=1))
for name, res in (("gp", bo), ("random", rs), ("gp_shuffled", bo_shuf)):
    pd.DataFrame(res["log"]).to_csv(OUT / f"trials_{name}.csv", index=False)
print(json.dumps({"test": test_scores, "decision": decision, "fits": FITS["count"],
                  "wall_s": round(total_s)}, indent=1))
