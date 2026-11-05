"""Fail-closed artifact integration: run experiment.py before pytest; no skipped checks."""
import json
import pickle
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.tree import DecisionTreeRegressor
from threadpoolctl import threadpool_limits

import experiment
from dataset import ContractError, SOURCE_SHA, code_hash, encoded, parse, sha, source_bytes
from experiment import REFERENCE, TOLERANCES, estimators, fit_compare, metrics, prepare, require_development, trace_tree, verify_baselines
from protocol import FEATURES, features, partitions, validate_features
from reader_lab import HOURS, TARGETS, check, mean, split, sse

ROOT = Path(__file__).parent


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def artifacts():
    # Missing receipts are a test failure, never a skipped integration test.
    return load("report.json"), pd.read_parquet(ROOT / "data/predictions.parquet"), pd.read_parquet(ROOT / "data/partitions.parquet")


def tiny_rows():
    def rows(times, prefix):
        t = pd.to_datetime(times, format="mixed")
        return pd.DataFrame({"record_id": [f"{prefix}{i}" for i in range(len(t))], "target_time": t, "hr": t.hour, "mnth": t.month, "weekday_mon0": t.dayofweek, "cnt": np.arange(len(t)) * 3})
    return rows(["2011-01-01", "2011-01-01 01:00", "2011-02-01", "2011-02-01 01:00"], "t"), rows(["2012-01-01", "2012-01-01 01:00"], "v")


def test_exact_rational_fixture_and_fresh_checkpoint():
    a, b = check()
    assert a["sse"] == Fraction(21400, 3) and b["sse"] == 1000
    assert sse(TARGETS) == 13800 and mean(TARGETS) == 75
    assert split(Fraction(25, 2), (10, 20, 30, 40, 70, 80, 90, 100))["right_mean"] == 85
    assert mean((90, 105, 120)) == 105
    # Independent installed estimator agrees with the hand-selected winning split.
    model = DecisionTreeRegressor(max_depth=1, random_state=42).fit(np.array(HOURS).reshape(-1, 1), TARGETS)
    assert model.tree_.threshold[0] == 12.5
    assert model.predict([[17]])[0] == 115
    assert np.sum((np.array(TARGETS) - model.predict(np.array(HOURS).reshape(-1, 1))) ** 2) == 1000


def test_configuration_and_inherited_helpers(artifacts):
    report, _, _ = artifacts
    config = load("frozen-config.json")
    assert config["models"] == {name: model.get_params() for name, model in estimators().items()}
    assert config["tolerances"] == TOLERANCES and config["declared_before_any_fit"]
    assert report["frozen_config_sha256"] == sha((ROOT / "frozen-config.json").read_bytes())
    assert report["code_sha256"] == code_hash()
    assert report["helper_sha256"]["dataset.py"] == REFERENCE["dataset_helper_sha256"]
    assert report["partitions"]["contract_sha256"] == REFERENCE["contract_sha256"]
    assert config["baseline_reference_sha256"] == sha((ROOT / "baseline-reference.json").read_bytes())
    assert config["search"] is None and config["postprocessing"] is None
    assert all(pool["num_threads"] == 1 for pool in report["threadpools_during_fit"])


def test_source_partitions_readiness_and_frozen_ids(artifacts):
    report, _, ids = artifacts
    blocks = partitions(parse(source_bytes(ROOT / "data")))
    assert list(blocks["reserved"]) == ["record_id", "target_time"]
    for part, expected in REFERENCE["partitions"].items():
        rows = blocks[part]
        assert len(rows) == expected["count"]
        assert sha(encoded(rows.record_id.tolist())) == expected["ordered_ids_sha256"]
        assert rows.record_id.tolist() == ids.loc[ids.partition.eq(part), "record_id"].tolist()
    assert blocks["train"].target_time.max() == pd.Timestamp("2011-12-31 22:00")
    assert blocks["readiness_excluded"].record_id.tolist() == [SOURCE_SHA + ":8645"]
    assert ids.record_id.is_unique
    assert report["source"]["rows"] == 17379
    # Corruption must fail at the archive boundary before parsing/model work.
    with pytest.raises(ContractError, match="archive SHA mismatch"):
        source_bytes(ROOT / "data", ROOT / "baseline-reference.json")


@pytest.mark.parametrize("when", ["2012-07-01", "2012-12-31 23:00"])
def test_final_rows_rejected_before_any_encoder_or_estimator_call(monkeypatch, when):
    train, val = tiny_rows()
    val.loc[0, "target_time"] = pd.Timestamp(when)
    def forbidden(*args, **kwargs):
        pytest.fail("reached fit/predict machinery with reserved rows")
    monkeypatch.setattr(experiment.OneHotEncoder, "fit_transform", forbidden)
    monkeypatch.setattr(experiment, "estimators", forbidden)
    with pytest.raises(ValueError, match="development windows"):
        prepare(train, val)
    with pytest.raises(ValueError, match="development windows"):
        fit_compare(train, val, None, None, None)
    with pytest.raises(ValueError, match="development windows"):
        require_development(train, "reserved")


def test_readiness_overlap_duplicate_and_order_guards():
    train, val = tiny_rows()
    train.loc[len(train) - 1, "target_time"] = pd.Timestamp("2011-12-31 23:00")
    with pytest.raises(ValueError, match="not ready"):
        prepare(train, val)
    train, val = tiny_rows()
    val.loc[0, "record_id"] = train.record_id.iloc[0]
    with pytest.raises(ValueError, match="overlap"):
        prepare(train, val)
    val.loc[1, "record_id"] = val.record_id.iloc[0]
    with pytest.raises(ValueError, match="unique ordered"):
        prepare(train, val)
    train, val = tiny_rows()
    with pytest.raises(ValueError, match="unique ordered"):
        prepare(train.iloc[::-1], val)


def test_train_only_encoding_and_excluded_feature_perturbation():
    train, val = tiny_rows()
    enc, x, v = prepare(train, val)
    changed_train = train.assign(casual=99999, registered=-999, cnt=train.cnt, temp=800, yr=800, instant=800, holiday=800)
    changed_val = val.assign(casual=-999, registered=888, cnt=-90000, temp=-800, yr=-800, instant=-800, holiday=-800)
    enc2, x2, v2 = prepare(changed_train, changed_val)
    np.testing.assert_array_equal(x, x2)
    np.testing.assert_array_equal(v, v2)
    assert list(features(changed_train)) == FEATURES
    for a, b in zip(enc.categories_, enc2.categories_, strict=True):
        np.testing.assert_array_equal(a, b)
    changed_val["mnth"] = 12  # Unseen category must not enter training vocabulary.
    enc3, x3, _ = prepare(train, changed_val)
    np.testing.assert_array_equal(x, x3)
    assert 12 not in enc3.categories_[1]
    with pytest.raises(ValueError, match="allowlist"):
        validate_features(changed_train)


def test_saved_metrics_pairing_and_no_final_predictions(artifacts):
    report, pred, ids = artifacts
    assert report["final_metrics"] is None
    assert pred.record_id.is_unique and set(pred.partition) == {"train", "validation"}
    assert pred.target_time.max() < pd.Timestamp("2012-07-01")
    assert not set(pred.record_id) & set(ids.loc[ids.partition.eq("reserved"), "record_id"])
    assert not set(pred.record_id) & set(ids.loc[ids.partition.eq("readiness_excluded"), "record_id"])
    for part in ["train", "validation"]:
        rows = pred.loc[pred.partition.eq(part)]
        assert rows.record_id.tolist() == ids.loc[ids.partition.eq(part), "record_id"].tolist()
        for name in estimators():
            actual = metrics(rows.cnt, rows[name].to_numpy())
            assert actual == report["scores"][name][part]
            np.testing.assert_array_equal(rows[f"residual_{name}"], rows.cnt - rows[name])
    assert report["scores"]["ols"]["validation"]["negative_count"] == 733
    assert pred.ols.min() < 0  # Clipping would break this and the frozen metric receipt.


@pytest.mark.parametrize("name", ["median", "mean", "ols", "tree", "forest", "diagnostic"])
def test_persisted_actual_estimator_agreement_and_size(artifacts, name):
    report, pred, _ = artifacts
    path = ROOT / f"data/{name}.pkl"
    payload = path.read_bytes()
    assert len(payload) == report["serialized_bytes"][name]
    assert sha(payload) == report["artifacts_sha256"][f"data/{name}.pkl"]
    encoder, model = pickle.loads(payload)  # Only our locally generated, hashed artifacts.
    assert model.get_params() == load("frozen-config.json")["models"][name]
    assert encoder.get_feature_names_out(FEATURES).tolist() == report["encoding"]["names"]
    assert len(report["encoding"]["names"]) == 40
    with threadpool_limits(limits=1):
        for part in ["train", "validation"]:
            rows = pred.loc[pred.partition.eq(part)]
            x = encoder.transform(features(rows))
            np.testing.assert_allclose(model.predict(x), rows[name], rtol=TOLERANCES["prediction_rtol"], atol=TOLERANCES["prediction_atol"])
            if name in {"tree", "diagnostic"}:
                saved = load("structures.json")["models"][name]
                assert saved["children_left"] == model.tree_.children_left.tolist()
                assert saved["value"] == model.tree_.value[:, 0, 0].tolist()
                # Independently recompute every training leaf's target mean.
                if part == "train":
                    leaves = model.apply(x)
                    for leaf in np.unique(leaves):
                        assert abs(rows.cnt.to_numpy()[leaves == leaf].mean() - model.tree_.value[leaf, 0, 0]) < 1e-9


def test_forest_per_tree_predictions_structure_and_first_row_paths(artifacts):
    report, pred, _ = artifacts
    encoder, forest = pickle.loads((ROOT / "data/forest.pkl").read_bytes())
    per_tree = pd.read_parquet(ROOT / "data/forest-predictions.parquet")
    saved, trace = load("structures.json"), load("trace.json")
    assert per_tree.record_id.tolist() == pred.record_id.tolist()
    np.testing.assert_allclose(per_tree.filter(like="tree_").mean(axis=1), pred.forest, rtol=TOLERANCES["prediction_rtol"], atol=TOLERANCES["prediction_atol"])
    dev = pred.loc[pred.partition.eq("validation")]
    x = encoder.transform(features(dev))
    assert trace["record_id"] == dev.record_id.iloc[0] == SOURCE_SHA + ":8646"
    with threadpool_limits(limits=1):
        for i, tree in enumerate(forest.estimators_):
            stored = saved["models"]["forest"][i]
            assert stored["depth"] == tree.get_depth() <= 6
            assert stored["leaves"] == tree.get_n_leaves() <= 64
            assert stored["nominal_max_features"] == tree.max_features_ == 28
            np.testing.assert_array_equal(per_tree.loc[per_tree.partition.eq("validation"), f"tree_{i:03d}"], tree.predict(x))
            assert trace_tree(tree, x[0], saved["encoded_names"]) == trace["paths"]["forest"][i]
            draws = forest.estimators_samples_[i]
            assert len(draws) == 8644 and len(np.unique(draws)) < len(draws)
            assert sha(encoded(draws.tolist())) == saved["bootstrap"][i]["ordered_draw_indices_sha256"]
            # Weighted leaf means must account for repeated bootstrap draws.
            train = pred.loc[pred.partition.eq("train")]
            bx = encoder.transform(features(train)).astype(np.float32)[draws]
            by = train.cnt.to_numpy()[draws]
            leaves = tree.apply(bx)
            for leaf in np.unique(leaves):
                assert abs(by[leaves == leaf].mean() - tree.tree_.value[leaf, 0, 0]) < 1e-9
    assert abs(np.mean(trace["forest_first_row_per_tree"]) - trace["forest_first_row_mean"]) < 1e-9


def test_diagnostics_and_artifact_hashes(artifacts):
    report, pred, _ = artifacts
    diagnostics = load("diagnostics.json")
    dev = pred.loc[pred.partition.eq("validation")]
    assert [r["record_id"] for r in diagnostics["first48"]] == dev.head(48).record_id.tolist()
    assert [r["hour"] for r in diagnostics["hour_slices"]] == list(range(24))
    for saved in diagnostics["hour_slices"]:
        rows = dev.loc[dev.hr.eq(saved["hour"])]
        for name in estimators():
            assert saved["models"][name]["mae"] == metrics(rows.cnt, rows[name].to_numpy())["mae"]
    for name, digest in report["artifacts_sha256"].items():
        assert sha((ROOT / name).read_bytes()) == digest, name


def test_baseline_gate_detects_wrong_metrics(artifacts):
    report, pred, _ = artifacts
    models = {name: pickle.loads((ROOT / f"data/{name}.pkl").read_bytes())[1] for name in ["median", "mean", "ols"]}
    parts = {part: pred.loc[pred.partition.eq(part)] for part in ["train", "validation"]}
    assert verify_baselines(report["scores"], models, parts)["passed"]
    wrong = json.loads(json.dumps(report["scores"]))
    wrong["ols"]["validation"]["mae"] += 0.01
    with pytest.raises(AssertionError):
        verify_baselines(wrong, models, parts)
