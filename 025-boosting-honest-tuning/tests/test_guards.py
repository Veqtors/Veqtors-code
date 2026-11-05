"""Guards for issue #025: recipes never cross a boundary; the test set is scored once."""
import json
import pathlib
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))

from common import (OUT, PARTITIONS, grouped_folds, load_config, load_frame, sha256,  # noqa: E402
                    shuffled_folds, split, DATA)

SEED = load_config()["seed"]


@pytest.fixture(scope="module")
def parts():
    df = load_frame()
    train, sealed = split(df)
    return df, train, sealed


def crossing(frame, folds):
    return sum(len(set(frame["recipe"].iloc[tr]) & set(frame["recipe"].iloc[va])) for tr, va in folds)


def test_data_hash_matches_partition():
    assert sha256(DATA) == json.loads(PARTITIONS.read_text())["data_sha256"]


def test_no_recipe_crosses_train_test(parts):
    df, train, _ = parts
    test_recipes = set(json.loads(PARTITIONS.read_text())["test_recipes"])
    assert not set(train["recipe"]) & test_recipes
    assert len(train) + int(df["recipe"].isin(test_recipes).sum()) == len(df)


def test_no_recipe_crosses_any_grouped_fold(parts):
    _, train, _ = parts
    outer = grouped_folds(train, SEED)
    assert crossing(train, outer) == 0
    for otr, ova in outer:
        a = train.iloc[otr].reset_index(drop=True)
        b = train.iloc[ova]
        assert not set(a["recipe"]) & set(b["recipe"])
        assert crossing(a, grouped_folds(a, SEED)) == 0


def test_shuffled_folds_do_leak_recipes(parts):
    """The trap the issue measures: plain shuffled folds put one recipe on both sides."""
    _, train, _ = parts
    assert crossing(train, shuffled_folds(train, SEED)) > 0


def test_sealed_test_opens_once(parts):
    _, _, sealed = parts
    sealed.open()
    with pytest.raises(RuntimeError):
        sealed.open()


def test_run_scored_test_exactly_once():
    ledger = OUT / "test_ledger.json"
    report = OUT / "report.json"
    if not ledger.exists():
        pytest.skip("run.py has not been run yet")
    assert json.loads(ledger.read_text())["openings"] == 1
    assert json.loads(report.read_text())["test"]["openings"] == 1


def test_run_refuses_a_second_opening():
    if not (OUT / "test_ledger.json").exists():
        pytest.skip("run.py has not been run yet")
    proc = subprocess.run([sys.executable, str(HERE / "run.py")], capture_output=True, text=True, cwd=HERE)
    assert proc.returncode != 0 and "already opened" in (proc.stdout + proc.stderr)


def test_toy_arithmetic():
    proc = subprocess.run([sys.executable, str(HERE / "toy.py")], capture_output=True, text=True, cwd=HERE)
    assert proc.returncode == 0, proc.stderr
