"""Audit frozen partitions and a full-entry synthetic preprocessing sentinel."""
import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from dataset import code_hash, logical_hash, parse, source_bytes, versions, write_json
from protocol import features, freeze, partitions, validate_features


def fixtures():
    train = pd.DataFrame({"numeric": [0., 2., np.nan], "category": ["a", "b", "a"]})
    a = pd.DataFrame({"numeric": [np.nan, 4.], "category": ["a", "a"]})
    b = pd.DataFrame({"numeric": [1000., np.nan], "category": ["sentinel_new", "a"]})
    return train, a, b


def snapshot(prep):
    numeric = prep.named_transformers_["numeric"].named_steps
    return {"imputer": numeric["imputer"].statistics_.tolist(), "scaler_mean": numeric["scaler"].mean_.tolist(), "scaler_var": numeric["scaler"].var_.tolist(), "scaler_scale": numeric["scaler"].scale_.tolist(), "scaler_samples": int(numeric["scaler"].n_samples_seen_), "categories": [c.tolist() for c in prep.named_transformers_["category"].categories_]}


def prepare_fit(train, validation, *, invalid_concat=False):
    """Full entry: fresh prep, select fit rows, learn, transform train/validation."""
    if list(train.columns) != ["numeric", "category"] or list(validation.columns) != list(train.columns):
        raise ValueError("sentinel schema")
    prep = ColumnTransformer([
        ("numeric", Pipeline([("imputer", SimpleImputer(strategy="mean")), ("scaler", StandardScaler())]), ["numeric"]),
        ("category", OneHotEncoder(categories="auto", drop=None, handle_unknown="ignore", sparse_output=False), ["category"]),
    ], remainder="drop", sparse_threshold=0)
    fit_rows = pd.concat([train, validation], ignore_index=True) if invalid_concat else train
    prep.fit(fit_rows)
    before = snapshot(prep)
    transformed_train = prep.transform(train)
    transformed_val = prep.transform(validation)
    after = snapshot(prep)
    if before != after:
        raise AssertionError("transform mutated fitted statistics")
    return {"state": after, "train": transformed_train, "validation": transformed_val}


def assert_invariant(a, b):
    assert a["state"]["categories"] == b["state"]["categories"], "category fit contamination"
    for key in ["imputer", "scaler_mean", "scaler_var", "scaler_scale", "scaler_samples"]:
        np.testing.assert_allclose(a["state"][key], b["state"][key], rtol=0, atol=1e-12, err_msg=key)
    np.testing.assert_allclose(a["train"], b["train"], rtol=0, atol=1e-12)


def sentinel():
    train, a, b = fixtures()
    va, vb = prepare_fit(train, a), prepare_fit(train, b)
    assert_invariant(va, vb)
    np.testing.assert_allclose(va["state"]["imputer"], [1])
    np.testing.assert_allclose(va["state"]["scaler_mean"], [1])
    np.testing.assert_allclose(va["state"]["scaler_var"], [2 / 3])
    np.testing.assert_array_equal(vb["validation"][0, 1:], [0, 0])
    ia, ib = prepare_fit(train, a, invalid_concat=True), prepare_fit(train, b, invalid_concat=True)
    try:
        assert_invariant(ia, ib)
    except AssertionError:
        detected = True
    else:
        raise AssertionError("invalid concatenated-fit control escaped")
    np.testing.assert_allclose(ia["state"]["imputer"], [2])
    np.testing.assert_allclose(ib["state"]["imputer"], [334])
    changed = train.copy(); changed.loc[1, "numeric"] = 6
    sensitivity = prepare_fit(changed, a)
    np.testing.assert_allclose(sensitivity["state"]["imputer"], [3])
    assert sensitivity["state"] != va["state"]
    return {"valid_A": va["state"], "valid_B": vb["state"], "valid_transformed_train": va["train"].tolist(), "validation_B_transform": vb["validation"].tolist(), "invalid_A": ia["state"], "invalid_B": ib["state"], "invalid_detected": detected, "training_changed": sensitivity["state"], "transform_state_unchanged": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", help="Official ZIP; exact hashes verified")
    args = parser.parse_args()
    root = Path(__file__).parent
    started = time.perf_counter()
    df = parse(source_bytes(root / "data", args.archive))
    blocks = partitions(df)
    manifest = freeze(blocks, root / "partitions.json")  # BEFORE sentinel .fit()
    for key in ["train", "validation"]:
        validate_features(features(blocks[key]))
    row = blocks["validation"].iloc[0]
    arithmetic = {"record_id": row.record_id, "target_time": str(row.target_time), "casual": int(row.casual), "registered": int(row.registered), "cnt": int(row.cnt)}
    assert arithmetic["casual"] + arithmetic["registered"] == arithmetic["cnt"]
    report = {"source_logical_sha256": logical_hash(df), "code_sha256": code_hash(), "versions": versions(), "partitions": manifest, "development_arithmetic_only": arithmetic, "sentinel": sentinel(), "final_metrics": None, "elapsed_seconds": time.perf_counter() - started}
    write_json(root / "report.json", report)
    print({"counts": {k: len(v) for k, v in blocks.items()}, "arithmetic": arithmetic, "sentinel": report["sentinel"], "seconds": report["elapsed_seconds"]})


if __name__ == "__main__":
    main()
