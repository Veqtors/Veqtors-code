import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from dataset import encoded, sha
from experiment import compare, require_development, trace_prediction
from protocol import FEATURES, features


def tiny_rows():
    def rows(times, prefix):
        t = pd.to_datetime(times, format="mixed")
        return pd.DataFrame({"record_id": [f"{prefix}{i}" for i in range(len(t))], "target_time": t, "hr": t.hour, "mnth": t.month, "weekday_mon0": t.dayofweek, "cnt": np.arange(len(t)) * 3})
    return rows(["2011-01-01", "2011-01-01 01:00", "2011-02-01", "2011-02-01 01:00", "2011-02-02", "2011-02-02 01:00"], "t"), rows(["2012-01-01", "2012-01-01 01:00"], "v")


def test_paired_ids_trace_constants_and_raw_finite_outputs():
    train, val = tiny_rows()
    models, pred, scores, _ = compare(train, val)
    dev = pred.loc[pred.partition.eq("validation")]
    assert dev.record_id.tolist() == val.record_id.tolist()
    assert all(s["validation"]["rows"] == len(val) for s in scores.values())
    assert models["median"].constant_[0, 0] == np.median(train.cnt)
    assert models["mean"].constant_[0, 0] == np.mean(train.cnt)
    trace = trace_prediction(models["ols"], val)
    assert abs(trace["summed_prediction"] - trace["estimator_prediction"]) < 1e-10
    encoded_val = models["ols"].named_steps["encoder"].transform(features(val))
    linear = models["ols"].named_steps["linear"]
    np.testing.assert_allclose(dev.ols, encoded_val @ linear.coef_ + linear.intercept_, atol=1e-10)
    assert np.isfinite(pred[["ols", "mean", "median"]]).all().all()


@pytest.mark.parametrize("when", ["2012-07-01", "2012-12-31 23:00"])
def test_final_boundary_rejected_before_fit_or_score(when):
    train, val = tiny_rows()
    val.loc[0, "target_time"] = pd.Timestamp(when)
    with pytest.raises(ValueError, match="development windows"):
        require_development(val, "validation")
    with pytest.raises(ValueError, match="development windows"):
        compare(train, val)


def test_readiness_guard_and_overlap():
    train, val = tiny_rows()
    train.loc[len(train)-1, "target_time"] = pd.Timestamp("2011-12-31 23:00")
    with pytest.raises(ValueError, match="not ready"):
        compare(train, val)
    train, val = tiny_rows()
    val.loc[0, "record_id"] = train.record_id.iloc[0]
    with pytest.raises(ValueError, match="overlap"):
        compare(train, val)


def test_target_components_cannot_change_fit():
    train, val = tiny_rows()
    _, pred, _, _ = compare(train, val)
    altered_train = train.assign(casual=99999, registered=-999, temp=800, yr=800, instant=800)
    altered_val = val.assign(casual=-500, registered=100000, temp=-200, yr=-500, instant=500)
    _, changed_pred, _, _ = compare(altered_train, altered_val)
    np.testing.assert_array_equal(pred.ols, changed_pred.ols)
    assert list(features(altered_train)) == FEATURES


def test_real_artifact_identity_metrics_trace_and_reference_mapping():
    root = Path(__file__).parent
    if not (root / "data/predictions.parquet").exists():
        pytest.skip("run experiment.py first for artifact integration")
    pred = pd.read_parquet(root / "data/predictions.parquet")
    ids = pd.read_parquet(root / "data/partitions.parquet")
    report = json.loads((root / "report.json").read_text())
    trace = json.loads((root / "trace.json").read_text())
    assert report["final_metrics"] is None
    assert pred.target_time.max() < pd.Timestamp("2012-07-01")
    assert set(pred.partition) == {"train", "validation"}
    assert not set(pred.record_id) & set(ids.loc[ids.partition.eq("reserved"), "record_id"])
    for part in ["train", "validation"]:
        rows = pred.loc[pred.partition.eq(part)]
        assert rows.record_id.tolist() == ids.loc[ids.partition.eq(part), "record_id"].tolist()
        assert sha(encoded(rows.record_id.tolist())) == report["partitions"]["partitions"][part]["ordered_ids_sha256"]
        for model in ["mean", "median", "ols"]:
            residual = rows.cnt - rows[model]
            np.testing.assert_allclose(rows[f"residual_{model}"], residual)
            np.testing.assert_allclose(np.mean(np.abs(residual)), report["scores"][model][part]["mae"])
            np.testing.assert_allclose(np.mean(residual**2), report["scores"][model][part]["mse"])
            assert int((rows[model] < 0).sum()) == report["scores"][model][part]["negative_count"]
            assert np.isfinite(rows[model]).all()
    names = report["encoding"]["names"]
    assert [term["feature"] for term in trace["terms"]] == names
    for term in trace["terms"]:
        source_feature, category = term["feature"].rsplit("_", 1)
        assert term["value"] == float(trace["features"][source_feature] == int(category))
        assert term["contribution"] == term["value"] * term["coefficient"]
    assert report["encoding"]["reference_categories"] == {"hr": 0, "mnth": 1, "weekday_mon0": 0}
    for feature, categories in report["encoding"]["categories"].items():
        reference = report["encoding"]["reference_categories"][feature]
        assert f"{feature}_{reference}" not in names
        assert all(f"{feature}_{value}" in names for value in categories if value != reference)
    total = trace["intercept"] + math.fsum(t["value"] * t["coefficient"] for t in trace["terms"])
    np.testing.assert_allclose(total, trace["estimator_prediction"], rtol=0, atol=1e-10)
    row = pred.loc[pred.record_id.eq(trace["record_id"])].iloc[0]
    np.testing.assert_allclose(total, row.ols, rtol=0, atol=1e-10)
    assert report["encoding"]["augmented_rank"] == report["encoding"]["augmented_columns"] == 41
    assert report["scores"]["ols"]["train"]["mse"] <= report["scores"]["mean"]["train"]["mse"] + 1e-9
