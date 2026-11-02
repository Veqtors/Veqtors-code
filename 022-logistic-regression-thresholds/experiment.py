"""Standalone #22 classification experiment. No cross-issue runtime imports."""
import argparse
import importlib.metadata
import json
import math
import os
import platform
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.dummy import DummyClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.preprocessing import OneHotEncoder
from threadpoolctl import threadpool_info, threadpool_limits

from dataset import SOURCE_SHA, ZIP_SHA, code_hash, encoded, logical_hash, parse, sha, source_bytes, versions, write_json
from protocol import CONTRACT, FEATURES, features, freeze, partitions, validate_features

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / "model-config.json").read_text())
EXPECTED = json.loads((ROOT / "inherited-identity.json").read_text())
PREDICTION_COLUMNS = ["record_id", "target_time", "y", "logistic_p1", "logistic_z",
                      "decision_050", "decision_030", "dummy_p1", "dummy_decision_050", "dummy_decision_030"]


def durable_freeze(path, value):
    """Write once before fitting, fsync, then reject policy/state drift on reruns."""
    if path.exists():
        if json.loads(path.read_text()) != value:
            raise ValueError(f"Frozen artifact changed: {path.name}; stop, do not adapt")
    else:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
    return sha(path.read_bytes())


def allowed(frame, partition):
    """Guard every target/feature modeling entry point; reserved rows lack cnt."""
    if partition not in ("train", "validation"):
        raise ValueError("Reserved/excluded period: metadata only")
    t = frame.target_time
    lower = pd.Timestamp(CONTRACT["train_start"] if partition == "train" else CONTRACT["validation_start"])
    upper = pd.Timestamp(CONTRACT["validation_start"] if partition == "train" else CONTRACT["reserved_start"])
    if frame.empty or not ((t >= lower) & (t < upper)).all():
        raise ValueError("Period guard")
    if partition == "train":
        issuance = pd.Timestamp(EXPECTED["first_validation_issuance"])
        if not (t + pd.Timedelta(hours=1) <= issuance).all():
            raise ValueError("Readiness guard")


def cutoff_recipe(train):
    allowed(train, "train")
    c = float(np.quantile(train.cnt.to_numpy(), CONTRACT["label"]["q"], method=CONTRACT["label"]["method"]))
    return {"cutoff": c, "q": 0.75, "method": "higher", "comparison": ">",
            "mapping": {"0": "cnt <= c", "1": "cnt > c"},
            "train_ordered_ids_sha256": sha(encoded(train.record_id.tolist())),
            "training_counts_sha256": sha(encoded(train.cnt.tolist())),
            "source_sha256": SOURCE_SHA, "frozen_before_fit": True}


def labels(frame, partition, c):
    allowed(frame, partition)
    return (frame.cnt.to_numpy() > c).astype(np.int64)


def both_classes(y):
    if not np.array_equal(np.unique(y), [0, 1]):
        raise ValueError("Training must contain both binary classes; no policy adaptation")


def positive_probability(model, X):
    classes = np.asarray(model.classes_)
    if set(classes.tolist()) != {0, 1} or len(classes) != 2:
        raise ValueError("Exactly binary classes required")
    probability = np.asarray(model.predict_proba(X), dtype=np.float64)
    if probability.shape != (len(X), 2) or not np.isfinite(probability).all():
        raise ValueError("Probability shape/finite guard")
    if not ((probability >= 0) & (probability <= 1)).all():
        raise ValueError("Probability bounds")
    np.testing.assert_allclose(probability.sum(axis=1), 1, rtol=1e-12, atol=1e-12)
    col = np.flatnonzero(classes == 1).item()
    return probability[:, col], col


def decisions(p, tau):
    return (np.asarray(p) >= tau).astype(np.int64)


def checked_fit(model, X, y):
    both_classes(y)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        model.fit(X, y)  # No sample weights; never called for held-out rows.
    receipt = [{"category": w.category.__name__, "message": str(w.message)} for w in caught]
    if any(issubclass(w.category, ConvergenceWarning) for w in caught):
        raise RuntimeError(f"ConvergenceWarning blocks experiment: {receipt}")
    if not np.array_equal(model.classes_, [0, 1]):
        raise ValueError("Pinned fit must produce classes [0,1]")
    return receipt


def evaluate(frame, partition, y, X, model, dummy):
    allowed(frame, partition)
    if len(frame) != len(y) or len(frame) != len(X):
        raise ValueError("Paired row lengths")
    p, col = positive_probability(model, X)
    d, dcol = positive_probability(dummy, X)
    z = np.asarray(model.decision_function(X), dtype=np.float64)
    if z.shape != (len(frame),) or not np.isfinite(z).all():
        raise ValueError("Raw score guard")
    np.testing.assert_allclose(p, expit(z), **CONTRACT["agreement_tolerance"])
    output = frame[["record_id", "target_time"]].reset_index(drop=True).copy()
    output["y"], output["logistic_p1"], output["logistic_z"] = y, p, z
    output["decision_050"], output["decision_030"] = decisions(p, .5), decisions(p, .3)
    output["dummy_p1"] = d
    output["dummy_decision_050"], output["dummy_decision_030"] = decisions(d, .5), decisions(d, .3)
    metrics = {}
    for name, prob in [("logistic", p), ("dummy", d)]:
        # Explicit sorted probability columns, float64; raw artifacts stay unclipped.
        loss = float(log_loss(y, np.column_stack([1 - prob, prob]), labels=[0, 1]))
        if not math.isfinite(loss):
            raise ValueError("Nonfinite paired log loss")
        a, b = decisions(prob, .5), decisions(prob, .3)
        metrics[name] = {"log_loss": loss, "positive_050": int(a.sum()),
                         "positive_030": int(b.sum()), "changed_decisions": int(np.count_nonzero(a != b))}
    return output[PREDICTION_COLUMNS], {"rows": len(output), "class_counts": np.bincount(y, minlength=2).tolist(),
                                      "positive_columns": {"logistic": col, "dummy": dcol}, "models": metrics}


def make_trace(frame, X, names, model, output):
    row, prediction = frame.iloc[0], output.iloc[0]
    terms = [{"feature": name, "encoded": float(x), "weight": float(w), "contribution": float(x * w)}
             for name, x, w in zip(names, X[0], model.coef_[0], strict=True)]
    b = float(model.intercept_[0])
    summed = b + math.fsum(t["contribution"] for t in terms)
    np.testing.assert_allclose(summed, prediction.logistic_z, **CONTRACT["agreement_tolerance"])
    return {"selection": "FIRST development row in inherited stable order; never selected by score",
            "record_id": row.record_id, "target_time": str(row.target_time),
            "allowed_inputs": {f: int(row[f]) for f in FEATURES}, "terms": terms,
            "intercept": b, "weighted_sum": summed, "decision_function_z": float(prediction.logistic_z),
            "sigmoid": float(expit(summed)),
            "outputs": {k: (int(prediction[k]) if k in ["y", "decision_050", "decision_030", "dummy_decision_050", "dummy_decision_030"] else float(prediction[k])) for k in PREDICTION_COLUMNS[2:]}}


def synthetic_receipts():
    return {"scope": "Synthetic arithmetic, not measured model results",
            "one_input_z": -1 + .5 * 2, "ln3": math.log(3),
            "sigmoid_zero": float(expit(0)), "sigmoid_ln3": float(expit(math.log(3))),
            "loss_y1_p08": -math.log(.8), "loss_y1_p02": -math.log(.2),
            "policy_fixtures": [{"p": p, "decision_050": int(p >= .5), "decision_030": int(p >= .3)} for p in [.4, .5, .3]]}


def verify_versions():
    if platform.python_version_tuple()[:2] != ("3", "13"):
        raise RuntimeError("Use the documented Python 3.13 runtime")
    for line in (ROOT / "requirements.txt").read_text().splitlines():
        name, version = line.split("==")
        if importlib.metadata.version(name) != version:
            raise RuntimeError(f"Pinned dependency mismatch: {line}")


def run():
    started = time.perf_counter()
    verify_versions()
    data = ROOT / "data"
    data.mkdir(exist_ok=True)
    # Static contract and estimator recipe were authored before execution. This
    # fsynced snapshot makes their exact content binding before any fit/encoding.
    static_hash = durable_freeze(ROOT / "frozen-config.json", {"protocol": CONTRACT, "config": CONFIG})
    raw = source_bytes(data)  # Official download on first run, both hashes always checked.
    full = parse(raw)  # Inherited whole-source mechanical checks only.
    blocks = partitions(full)
    del full  # Reserved block contains only IDs and times, never modeled.
    identity = freeze(blocks, ROOT / "partitions.json")
    for key in ["partitions", "excluded_ids", "first_validation_issuance"]:
        if identity[key] != EXPECTED[key]:
            raise ValueError(f"Inherited #21 partition identity mismatch: {key}")
    if sha((ROOT / "dataset.py").read_bytes()) != EXPECTED["dataset_helper_sha256"]:
        raise ValueError("Inherited source helper byte identity mismatch")
    train, val = blocks["train"], blocks["validation"]
    recipe = cutoff_recipe(train)
    label_hash = durable_freeze(ROOT / "label-config.json", recipe)
    # c has now been durably frozen and is printed before the first fit.
    print(f"FROZEN BEFORE FIT: c={recipe['cutoff']}; label-config SHA256={label_hash}", flush=True)
    y_train, y_val = labels(train, "train", recipe["cutoff"]), labels(val, "validation", recipe["cutoff"])
    both_classes(y_train)
    X_train, X_val = features(train), features(val)
    validate_features(X_train)
    validate_features(X_val)
    encoder = OneHotEncoder(**CONFIG["encoding"])
    model, dummy = LogisticRegression(**CONFIG["logistic"]), DummyClassifier(**CONFIG["dummy"])
    with threadpool_limits(limits=CONFIG["native_threads"]):
        pools = threadpool_info()
        if any(p["num_threads"] != 1 for p in pools):
            raise RuntimeError("Native single-thread guard")
        A = encoder.fit_transform(X_train)
        B = encoder.transform(X_val)
        names = encoder.get_feature_names_out(FEATURES).tolist()
        if names != EXPECTED["encoded_names"]:
            raise ValueError("Encoded column identity mismatch")
        fit_start = time.perf_counter()
        warning_receipt = {"dummy": checked_fit(dummy, A, y_train), "logistic": checked_fit(model, A, y_train)}
        fit_seconds = time.perf_counter() - fit_start
        weights_before = model.coef_.copy(), model.intercept_.copy()
        train_out, train_metrics = evaluate(train, "train", y_train, A, model, dummy)
        val_out, val_metrics = evaluate(val, "validation", y_val, B, model, dummy)
        np.testing.assert_array_equal(weights_before[0], model.coef_)
        np.testing.assert_array_equal(weights_before[1], model.intercept_)
        trace = make_trace(val, B, names, model, val_out)
    artifacts = {}
    for name, output in [("train", train_out), ("validation", val_out)]:
        path = data / f"{name}-predictions.parquet"
        output.to_parquet(path, index=False)
        artifacts[str(path.relative_to(ROOT)).replace("\\", "/")] = {
            "rows": len(output), "columns": list(output.columns), "sha256": sha(path.read_bytes()),
            "logical_sha256": logical_hash(output), "ordered_ids_sha256": sha(encoded(output.record_id.tolist()))}
    write_json(ROOT / "trace.json", trace)
    write_json(ROOT / "synthetic.json", synthetic_receipts())
    material = {"partitions": identity, "identical_to_21": True, "label": recipe,
                "metrics": {"train": train_metrics, "validation": val_metrics},
                "encoding": {"names": names, "names_sha256": sha(encoded(names)),
                             "categories": {f: cats.tolist() for f, cats in zip(FEATURES, encoder.categories_, strict=True)},
                             "references": {f: int(cats[0]) for f, cats in zip(FEATURES, encoder.categories_, strict=True)},
                             "unknown_validation_counts": {f: int((~X_val[f].isin(cats)).sum()) for f, cats in zip(FEATURES, encoder.categories_, strict=True)}},
                "fitted": {"intercept": model.intercept_.tolist(), "weights": model.coef_.tolist(),
                           "classes": model.classes_.tolist(), "dummy_classes": dummy.classes_.tolist(),
                           "dummy_prior": dummy.class_prior_.tolist(), "n_iter": model.n_iter_.tolist(), "warnings": warning_receipt},
                "outputs": artifacts, "trace_sha256": sha((ROOT / "trace.json").read_bytes()),
                "synthetic_sha256": sha((ROOT / "synthetic.json").read_bytes()),
                "inputs": {"archive_sha256": ZIP_SHA, "member_sha256": SOURCE_SHA,
                           "dataset_helper_sha256": sha((ROOT / "dataset.py").read_bytes()),
                           "code_sha256": code_hash(), "frozen_config_sha256": static_hash, "label_config_sha256": label_hash,
                           "file_sha256": {p: sha((ROOT / p).read_bytes()) for p in ["protocol.json", "model-config.json", "inherited-identity.json", "requirements.txt"]}}}
    material_hash = sha(encoded(material))
    previous_path = ROOT / "report.json"
    previous = json.loads(previous_path.read_text()) if previous_path.exists() else None
    repeat = {"previous_material_sha256": previous["material_sha256"] if previous else None,
              "identical_material": previous["material_sha256"] == material_hash if previous else None,
              "scope": "All material values including raw prediction bytes, trace and frozen state; runtime metadata excluded"}
    report = {"material": material, "material_sha256": material_hash, "repeatability": repeat,
              "runtime": {"utc_completed": datetime.now(timezone.utc).isoformat(), "seconds": time.perf_counter() - started,
                          "fit_seconds": fit_seconds, "versions": versions(), "threadpoolctl": importlib.metadata.version("threadpoolctl"),
                          "hardware": {"platform": platform.platform(), "processor": platform.processor(), "logical_cpus": os.cpu_count()},
                          "native_pools_during_computation": pools}}
    write_json(previous_path, report)
    if previous and not repeat["identical_material"]:
        raise RuntimeError("Repeat material changed; investigate, do not adapt policy")
    print(json.dumps({"metrics": material["metrics"], "n_iter": material["fitted"]["n_iter"], "repeatability": repeat, "seconds": report["runtime"]["seconds"]}, indent=2))
    return report


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__).parse_args()
    run()
