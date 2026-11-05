"""Shared data, partition, fold and model helpers for issue #025."""
import os

os.environ.setdefault("OMP_NUM_THREADS", "1")

import hashlib
import json
import pathlib

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import GroupKFold, KFold

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "data" / "concrete.csv"
CONFIG = HERE / "model-config.json"
PARTITIONS = HERE / "partitions.json"
OUT = HERE / "outputs"

INGREDIENTS = ["Cement", "Blast Furnace Slag", "Fly Ash", "Water",
               "Superplasticizer", "Coarse Aggregate", "Fine Aggregate"]
FEATURES = INGREDIENTS + ["Age"]
TARGET = "Concrete compressive strength"


def sha256(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def load_config():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def fetch_data():
    """Download UCI id 165 once and cache it with its hash."""
    if not DATA.exists():
        from ucimlrepo import fetch_ucirepo
        DATA.parent.mkdir(exist_ok=True)
        fetch_ucirepo(id=165).data.original.to_csv(DATA, index=False)
    digest = sha256(DATA)
    (DATA.parent / "concrete.csv.sha256").write_text(f"{digest}  concrete.csv\n")
    return digest


def load_frame():
    """All rows with a stable recipe id (R001...) from the seven ingredient columns."""
    df = pd.read_csv(DATA)
    codes = df.groupby(INGREDIENTS, sort=True).ngroup()
    df["recipe"] = ["R%03d" % (c + 1) for c in codes]
    return df


def recipe_stats(df):
    counts = df["recipe"].value_counts()
    repeated = counts[counts > 1]
    return {
        "rows": int(len(df)),
        "recipes": int(counts.size),
        "repeated_recipes": int(repeated.size),
        "rows_in_repeated_recipes": int(repeated.sum()),
        "max_rows_per_recipe": int(counts.max()),
        "exact_duplicate_rows": int(df[FEATURES + [TARGET]].duplicated().sum()),
        "recipes_if_ingredients_rounded_to_integer": int(
            df[INGREDIENTS].round(0).drop_duplicates().shape[0]),
    }


class SealedTest:
    """Holds the test rows and releases them exactly once per process."""

    def __init__(self, frame):
        self._frame = frame
        self.openings = 0

    def open(self):
        if self.openings:
            raise RuntimeError("The sealed test set has already been opened once.")
        self.openings += 1
        return self._frame


def split(df):
    """Return (train frame, SealedTest) using partitions.json; the test frame is never returned bare."""
    part = json.loads(PARTITIONS.read_text(encoding="utf-8"))
    test_recipes = set(part["test_recipes"])
    is_test = df["recipe"].isin(test_recipes)
    train = df[~is_test].reset_index(drop=True)
    return train, SealedTest(df[is_test].reset_index(drop=True))


def grouped_folds(train, seed):
    cv = GroupKFold(n_splits=5, shuffle=True, random_state=seed)
    return list(cv.split(train[FEATURES], train[TARGET], groups=train["recipe"]))


def shuffled_folds(train, seed):
    cv = KFold(n_splits=5, shuffle=True, random_state=seed)
    return list(cv.split(train[FEATURES]))


def hgb(params, seed):
    return HistGradientBoostingRegressor(loss="squared_error", early_stopping=False,
                                         random_state=seed, **params)


def cv_mae(make_model, frame, folds):
    """Fit on each training part, return the MAE of each validation part."""
    X, y = frame[FEATURES].to_numpy(), frame[TARGET].to_numpy()
    scores = []
    for tr, va in folds:
        model = make_model().fit(X[tr], y[tr])
        scores.append(float(np.mean(np.abs(model.predict(X[va]) - y[va]))))
    return scores
