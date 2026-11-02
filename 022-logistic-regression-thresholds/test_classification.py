"""Unit invariants plus mandatory integration against the real produced artifacts."""
import json
import math
import warnings

import numpy as np
import pandas as pd
import pytest
from scipy.special import expit
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.preprocessing import OneHotEncoder

import experiment as e
from dataset import ContractError, SOURCE_SHA, encoded, logical_hash, parse, sha, source_bytes
from protocol import features, partitions, validate_features


def read(name):
    return json.loads((e.ROOT / name).read_text())


@pytest.fixture(scope="module")
def actual():
    # No skip and no network fallback: official experiment must already have run.
    assert (e.ROOT / "data/bike.zip").is_file(), "Run experiment.py first"
    return partitions(parse(source_bytes(e.ROOT / "data")))


def test_inherited_identity_readiness_and_final_metadata(actual):
    manifest = read("partitions.json")
    assert manifest["partitions"] == e.EXPECTED["partitions"]
    for name, frame in actual.items():
        assert sha(encoded(frame.record_id.tolist())) == e.EXPECTED["partitions"][name]["ordered_ids_sha256"]
    train = actual["train"]
    issuance = pd.Timestamp(e.EXPECTED["first_validation_issuance"])
    assert (train.target_time + pd.Timedelta(hours=1) <= issuance).all()
    assert train.target_time.iloc[-1] + pd.Timedelta(hours=1) == issuance
    assert actual["readiness_excluded"].record_id.tolist() == e.EXPECTED["excluded_ids"]
    assert list(actual["reserved"].columns) == ["record_id", "target_time"]


@pytest.mark.parametrize("partition", ["reserved", "readiness_excluded"])
def test_reserved_label_and_model_entry_guard(actual, partition):
    frame = actual[partition]
    with pytest.raises(ValueError, match="metadata only"):
        e.labels(frame, partition, 200)
    with pytest.raises(ValueError, match="metadata only"):
        e.evaluate(frame, partition, None, None, None, None)
    with pytest.raises(ValueError):
        e.labels(frame, "validation", 200)
    with pytest.raises(ValueError):
        e.cutoff_recipe(frame)


def test_exact_source_hash_and_parser_rejection(actual, tmp_path):
    bad = tmp_path / "bad.zip"
    bad.write_bytes(b"not official bytes")
    with pytest.raises(ContractError, match="archive SHA mismatch"):
        source_bytes(tmp_path, archive=bad)
    with pytest.raises(ContractError, match="exact required header"):
        parse(b"cnt\n1\n")
    assert sha((e.ROOT / "dataset.py").read_bytes()) == e.EXPECTED["dataset_helper_sha256"]


def test_cutoff_is_train_only_and_strict_ties(actual):
    train = actual["train"]
    recipe = e.cutoff_recipe(train)
    assert recipe == read("label-config.json")
    with pytest.raises(ValueError, match="Period guard"):
        e.cutoff_recipe(actual["validation"])
    fixture = train.iloc[:5].copy()
    fixture["cnt"] = [0, 1, 2, 3, 4]
    assert e.cutoff_recipe(fixture)["cutoff"] == 3  # Integral quantile index.
    np.testing.assert_array_equal(e.labels(fixture, "train", 3), [0, 0, 0, 0, 1])
    fixture["cnt"] = [5] * 5
    assert e.cutoff_recipe(fixture)["cutoff"] == 5
    with pytest.raises(ValueError, match="both binary"):
        e.both_classes(e.labels(fixture, "train", 5))
    # Arbitrary held-out count changes cannot enter the training-only recipe.
    changed_val = actual["validation"].assign(cnt=999999)
    assert e.cutoff_recipe(train) == recipe
    assert e.labels(changed_val, "validation", recipe["cutoff"]).sum() == len(changed_val)


def test_allowlist_and_encoder_training_boundary(actual):
    X = features(actual["train"])
    validate_features(X)
    with pytest.raises(ValueError):
        validate_features(X.assign(cnt=1))
    enc = OneHotEncoder(**e.CONFIG["encoding"]).fit(X)
    names = enc.get_feature_names_out(e.FEATURES).tolist()
    assert names == e.EXPECTED["encoded_names"] == read("report.json")["material"]["encoding"]["names"]
    cats = [a.copy() for a in enc.categories_]
    unseen = X.iloc[:1].assign(hr=99)
    with pytest.warns(UserWarning, match="unknown categories"):
        out = enc.transform(unseen)
    assert not out[0, :23].any()
    for old, new in zip(cats, enc.categories_, strict=True):
        np.testing.assert_array_equal(old, new)


def synthetic_model():
    model = LogisticRegression(**e.CONFIG["logistic"])
    model.classes_ = np.array([0, 1])
    model.coef_ = np.array([[1.]])
    model.intercept_ = np.array([0.])
    model.n_features_in_ = 1
    return model


def test_positive_class_column_mapping():
    class Reversed:
        classes_ = np.array([1, 0])

        def predict_proba(self, X):
            return np.array([[.8, .2], [.3, .7]])

    p, col = e.positive_probability(Reversed(), [0, 1])
    assert col == 0
    np.testing.assert_array_equal(p, [.8, .3])
    bad = Reversed()
    bad.classes_ = np.array([0])
    with pytest.raises(ValueError, match="binary classes"):
        e.positive_probability(bad, [0, 1])


def test_sigmoid_threshold_ties_and_unchanged_weights():
    model = synthetic_model()
    X = np.array([[0.], [math.log(3)], [-1000.], [1000.]])
    w, b = model.coef_.copy(), model.intercept_.copy()
    p, _ = e.positive_probability(model, X)
    np.testing.assert_allclose(p, expit(model.decision_function(X)), rtol=1e-12, atol=1e-12)
    assert model.predict(X)[0] == 0
    assert e.decisions(p, .5)[0] == 1
    np.testing.assert_array_equal(e.decisions([.3, .4, .5], .5), [0, 0, 1])
    np.testing.assert_array_equal(e.decisions([.3, .4, .5], .3), [1, 1, 1])
    np.testing.assert_array_equal(model.coef_, w)
    np.testing.assert_array_equal(model.intercept_, b)
    np.testing.assert_array_equal(e.positive_probability(model, X)[0], p)


def test_finite_logloss_clipping_and_single_class():
    assert log_loss([1], np.array([0.], dtype=np.float64), labels=[0, 1]) == pytest.approx(-math.log(np.finfo(np.float64).eps))
    assert log_loss([0, 0], [.2, .2], labels=[0, 1]) == pytest.approx(-math.log(.8))
    fixture = e.synthetic_receipts()
    assert fixture["sigmoid_zero"] == .5 and fixture["sigmoid_ln3"] == .75
    assert fixture["loss_y1_p08"] == pytest.approx(.2231435513142097)
    assert fixture["loss_y1_p02"] == pytest.approx(1.6094379124341003)


def test_convergence_warning_blocks_without_retry():
    class Nonconverging:
        calls = 0

        def fit(self, X, y):
            self.calls += 1
            warnings.warn("synthetic failed solver", ConvergenceWarning)

    model = Nonconverging()
    with pytest.raises(RuntimeError, match="blocks experiment"):
        e.checked_fit(model, [[0], [1]], [0, 1])
    assert model.calls == 1


def test_durable_freeze_rejects_drift(tmp_path):
    path = tmp_path / "freeze.json"
    first = e.durable_freeze(path, {"c": 3})
    assert first == e.durable_freeze(path, {"c": 3})
    with pytest.raises(ValueError, match="Frozen artifact changed"):
        e.durable_freeze(path, {"c": 4})
    assert json.loads(path.read_text()) == {"c": 3}


def test_real_integration_artifacts_and_deterministic_trace(actual):
    report = read("report.json")  # Mandatory actual experiment; missing files fail.
    m = report["material"]
    assert sha(encoded(m)) == report["material_sha256"]
    assert report["repeatability"]["identical_material"] is True
    assert m["inputs"]["code_sha256"] == e.code_hash()
    assert read("frozen-config.json") == {"protocol": e.CONTRACT, "config": e.CONFIG}
    assert m["fitted"]["warnings"] == {"dummy": [], "logistic": []}
    assert 0 < m["fitted"]["n_iter"][0] < e.CONFIG["logistic"]["max_iter"]
    reserved = set(actual["reserved"].record_id)
    enc = OneHotEncoder(**e.CONFIG["encoding"]).fit(features(actual["train"]))
    model = LogisticRegression(**e.CONFIG["logistic"])
    model.classes_ = np.array(m["fitted"]["classes"])
    model.coef_ = np.array(m["fitted"]["weights"])
    model.intercept_ = np.array(m["fitted"]["intercept"])
    model.n_features_in_ = 40
    for name in ["train", "validation"]:
        path = e.ROOT / f"data/{name}-predictions.parquet"
        out = pd.read_parquet(path)
        entry = m["outputs"][f"data/{name}-predictions.parquet"]
        assert sha(path.read_bytes()) == entry["sha256"]
        assert logical_hash(out) == entry["logical_sha256"]
        assert list(out.columns) == e.PREDICTION_COLUMNS
        assert out.record_id.tolist() == actual[name].record_id.tolist()
        assert not reserved.intersection(out.record_id)
        np.testing.assert_array_equal(out.y, e.labels(actual[name], name, m["label"]["cutoff"]))
        X = enc.transform(features(actual[name]))
        np.testing.assert_allclose(model.decision_function(X), out.logistic_z, rtol=1e-12, atol=1e-12)
        np.testing.assert_allclose(expit(out.logistic_z), out.logistic_p1, rtol=1e-12, atol=1e-12)
        for model_name, col in [("logistic", "logistic_p1"), ("dummy", "dummy_p1")]:
            metric = m["metrics"][name]["models"][model_name]
            loss = log_loss(out.y, np.column_stack([1-out[col], out[col]]), labels=[0, 1])
            assert math.isfinite(loss) and loss == metric["log_loss"]
            for suffix, tau in [("050", .5), ("030", .3)]:
                dcol = ("dummy_" if model_name == "dummy" else "") + "decision_" + suffix
                np.testing.assert_array_equal(out[dcol], e.decisions(out[col], tau))
                assert int(out[dcol].sum()) == metric["positive_" + suffix]
        assert out.dummy_p1.nunique() == 1
        assert out.dummy_p1.iloc[0] == m["fitted"]["dummy_prior"][1]
        if name == "validation":
            trace = e.make_trace(actual[name], X, m["encoding"]["names"], model, out)
            assert trace == read("trace.json")
            assert len(trace["terms"]) == 40
            assert trace["record_id"] == actual[name].record_id.iloc[0]
    for key, filename in [("trace_sha256", "trace.json"), ("synthetic_sha256", "synthetic.json")]:
        assert sha((e.ROOT / filename).read_bytes()) == m[key]
    assert all(pool["num_threads"] == 1 for pool in report["runtime"]["native_pools_during_computation"])
