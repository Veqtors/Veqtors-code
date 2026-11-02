import numpy as np
import pandas as pd
import pytest

from experiment import assert_invariant, fixtures, prepare_fit, sentinel
from protocol import FEATURES, features, partitions, validate_features


def test_full_entry_sentinel_and_negative_control():
    report = sentinel()
    assert report["invalid_detected"]
    train, a, b = fixtures()
    with pytest.raises(AssertionError):
        assert_invariant(prepare_fit(train, a, invalid_concat=True), prepare_fit(train, b, invalid_concat=True))


@pytest.mark.parametrize("numeric,category", [(True, False), (False, True)])
def test_separate_numeric_and_category_perturbations(numeric, category):
    train, a, b = fixtures()
    changed = a.copy()
    if numeric:
        changed["numeric"] = b.numeric
    if category:
        changed["category"] = b.category
    assert_invariant(prepare_fit(train, a), prepare_fit(train, changed))
    with pytest.raises(AssertionError):
        assert_invariant(prepare_fit(train, a, invalid_concat=True), prepare_fit(train, changed, invalid_concat=True))


def test_training_sensitivity():
    train, a, _ = fixtures()
    before = prepare_fit(train, a)
    train.loc[1, "numeric"] = 6
    with pytest.raises(AssertionError):
        assert_invariant(before, prepare_fit(train, a))


def test_exact_allowed_features():
    raw = pd.DataFrame({k: [1] for k in FEATURES + ["cnt", "casual", "registered", "yr", "season", "temp", "holiday", "workingday", "instant"]})
    assert list(features(raw)) == FEATURES
    validate_features(features(raw))
    for banned in ["cnt", "casual", "registered", "temp", "yr"]:
        with pytest.raises(ValueError, match="allowlist"):
            validate_features(features(raw).assign(**{banned: 1}))


def boundary_rows():
    # Irregular timestamps: readiness uses times, not the last N rows.
    ts = pd.to_datetime(["2011-01-01", "2011-12-31 21:00", "2011-12-31 22:00", "2011-12-31 23:00", "2012-01-01", "2012-06-30 23:00", "2012-07-01"], format="mixed")
    return pd.DataFrame({"record_id": list("abcdefg"), "target_time": ts})


def test_readiness_equality_and_reserved_boundary():
    blocks = partitions(boundary_rows())
    assert blocks["train"].record_id.tolist() == ["a", "b", "c"]
    assert blocks["readiness_excluded"].record_id.tolist() == ["d"]
    assert blocks["validation"].record_id.tolist() == ["e", "f"]
    assert blocks["reserved"].record_id.tolist() == ["g"]
    first_issue = blocks["validation"].target_time.min() - pd.Timedelta(hours=1)
    assert first_issue == pd.Timestamp("2011-12-31 23:00")
    assert (blocks["train"].target_time + pd.Timedelta(hours=1) <= first_issue).all()
    assert (blocks["train"].target_time + pd.Timedelta(hours=1)).max() == first_issue


def test_overlap_rejected():
    rows = boundary_rows()
    rows.loc[6, "record_id"] = "a"
    with pytest.raises(ValueError, match="overlap"):
        partitions(rows)
