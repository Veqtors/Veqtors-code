"""One fixed CPU comparison on inherited training/development rows; final stays closed."""
import argparse
import importlib.metadata
import json
import math
import os
import pickle
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import OneHotEncoder
from sklearn.tree import DecisionTreeRegressor
from threadpoolctl import threadpool_info, threadpool_limits

from dataset import SOURCE_SHA, URL, ZIP_SHA, code_hash, encoded, logical_hash, parse, sha, source_bytes, versions, write_json
from protocol import CONTRACT, FEATURES, features, freeze, partitions, validate_features
from reader_lab import check

ROOT = Path(__file__).parent
REFERENCE = json.loads((ROOT / "baseline-reference.json").read_text(encoding="utf-8"))
# Numerical reproduction tolerances, deliberately separate from the MAE ranking tie.
TOLERANCES = {"metric_atol": 1e-8, "metric_rtol": 1e-12, "prediction_atol": 1e-9, "prediction_rtol": 1e-12, "constant_atol": 1e-12, "ranking_mae_atol": 1e-9}


def estimators():
    return {
        "median": DummyRegressor(strategy="median"),
        "mean": DummyRegressor(strategy="mean"),
        "ols": LinearRegression(fit_intercept=True, positive=False, copy_X=True, n_jobs=1),
        "tree": DecisionTreeRegressor(criterion="squared_error", max_depth=6, min_samples_leaf=20, random_state=42),
        "forest": RandomForestRegressor(n_estimators=100, criterion="squared_error", max_depth=6, min_samples_leaf=20, max_features=0.7, bootstrap=True, random_state=42, n_jobs=1),
        "diagnostic": DecisionTreeRegressor(criterion="squared_error", max_depth=None, min_samples_leaf=1, random_state=42),
    }


def require_development(frame, partition):
    t = frame.target_time
    b0, b1, b2 = (pd.Timestamp(CONTRACT[k]) for k in ["train_start", "validation_start", "reserved_start"])
    allowed = (t >= b0) & (t < b1) if partition == "train" else (t >= b1) & (t < b2)
    if partition not in {"train", "validation"} or frame.empty or not allowed.all():
        raise ValueError("only declared train/development windows may be fitted/predicted/scored")
    if frame.record_id.duplicated().any() or not t.is_monotonic_increasing:
        raise ValueError("unique ordered scoring IDs required")


def prepare(train, val):
    require_development(train, "train")
    require_development(val, "validation")
    if set(train.record_id) & set(val.record_id):
        raise ValueError("training/development ID overlap")
    issue = val.target_time.min() - pd.Timedelta(hours=1)
    if not (train.target_time + pd.Timedelta(hours=1) <= issue).all():
        raise ValueError("training labels not ready")
    a, b = features(train), features(val)
    validate_features(a)
    validate_features(b)
    encoder = OneHotEncoder(categories="auto", drop="first", handle_unknown="ignore", sparse_output=False)
    x = encoder.fit_transform(a)
    return encoder, x, encoder.transform(b)


def metrics(y, pred):
    if len(y) != len(pred) or not np.isfinite(pred).all():
        raise ValueError("paired finite raw predictions required")
    residual = np.asarray(y) - np.asarray(pred)
    mse = float(np.mean(residual ** 2))
    return {"mae": float(np.mean(np.abs(residual))), "mse": mse, "rmse": math.sqrt(mse), "rows": len(y), "negative_count": int((pred < 0).sum()), "minimum_prediction": float(np.min(pred))}


def measured(call):
    wall, cpu = time.perf_counter(), time.process_time()
    result = call()
    return result, {"wall_seconds": time.perf_counter() - wall, "process_cpu_seconds": time.process_time() - cpu}


def verify_baselines(scores, models, predictions):
    differences = {}
    for name, parts in REFERENCE["scores"].items():
        differences[name] = {}
        for part, expected in parts.items():
            differences[name][part] = {}
            for key in ["mae", "mse", "rmse"]:
                actual = scores[name][part][key]
                np.testing.assert_allclose(actual, expected[key], atol=TOLERANCES["metric_atol"], rtol=TOLERANCES["metric_rtol"])
                differences[name][part][key] = actual - expected[key]
            assert scores[name][part]["negative_count"] == expected["negative_count"]
    for name, expected in REFERENCE["constants"].items():
        np.testing.assert_allclose(models[name].constant_.item(), expected, rtol=0, atol=TOLERANCES["constant_atol"])
    first = predictions["validation"].ols.iloc[0]
    np.testing.assert_allclose(first, REFERENCE["first_validation_ols"], atol=TOLERANCES["prediction_atol"], rtol=TOLERANCES["prediction_rtol"])
    return {"passed": True, "metric_differences": differences, "first_validation_ols_difference": float(first - REFERENCE["first_validation_ols"])}


def fit_compare(train, val, encoder, x, v):
    # prepare() must run before this entry; repeat guards before any estimator call.
    require_development(train, "train")
    require_development(val, "validation")
    models = estimators()
    predictions = {part: rows[["record_id", "target_time", *FEATURES, "cnt"]].copy() for part, rows in [("train", train), ("validation", val)]}
    scores, timings, sizes = {}, {}, {}
    baseline_check = None
    for name, model in models.items():
        _, fit_time = measured(lambda: model.fit(x, train.cnt))
        a, train_time = measured(lambda: model.predict(x))
        b, val_time = measured(lambda: model.predict(v))
        timings[name] = {"fit": fit_time, "predict_train": train_time, "predict_validation": val_time}
        # Defined size: standalone (train-fitted encoder, estimator) pickle protocol 5.
        sizes[name] = len(pickle.dumps((encoder, model), protocol=5))
        scores[name] = {}
        for part, rows, pred in [("train", train, a), ("validation", val, b)]:
            assert predictions[part].record_id.equals(rows.record_id)
            predictions[part][name] = pred
            predictions[part][f"residual_{name}"] = rows.cnt.to_numpy() - pred
            scores[name][part] = metrics(rows.cnt, pred)
        if name == "ols":
            baseline_check = verify_baselines(scores, models, predictions)
    return models, pd.concat([rows.assign(partition=part) for part, rows in predictions.items()], ignore_index=True), scores, timings, sizes, baseline_check


def tree_structure(model, names):
    t = model.tree_
    return {"depth": int(model.get_depth()), "leaves": int(model.get_n_leaves()), "nodes": int(t.node_count),
            "random_state": int(model.random_state), "nominal_max_features": int(model.max_features_),
            "children_left": t.children_left.tolist(), "children_right": t.children_right.tolist(),
            "feature_index": t.feature.tolist(), "threshold": t.threshold.tolist(),
            "value": t.value[:, 0, 0].tolist(), "impurity": t.impurity.tolist(),
            "n_node_samples": t.n_node_samples.tolist(), "weighted_n_node_samples": t.weighted_n_node_samples.tolist()}


def trace_tree(model, vector, names):
    t, node, steps = model.tree_, 0, []
    while t.children_left[node] != -1:
        feature, threshold = int(t.feature[node]), float(t.threshold[node])
        left = bool(vector[feature] <= threshold)
        next_node = int(t.children_left[node] if left else t.children_right[node])
        steps.append({"node": node, "feature": names[feature], "value": float(vector[feature]), "threshold": threshold, "branch": "left" if left else "right", "next_node": next_node})
        node = next_node
    leaf = float(t.value[node, 0, 0])
    actual = float(model.predict(vector.reshape(1, -1))[0])
    np.testing.assert_allclose(leaf, actual, atol=TOLERANCES["prediction_atol"], rtol=TOLERANCES["prediction_rtol"])
    assert node == int(model.apply(vector.reshape(1, -1))[0])
    return {"steps": steps, "leaf": node, "leaf_training_mean": leaf, "estimator_prediction": actual}


def inspect_models(models, encoder, x, v, val):
    names = encoder.get_feature_names_out(FEATURES).tolist()
    forest = models["forest"]
    structures = {name: tree_structure(models[name], names) for name in ["tree", "diagnostic"]}
    structures["forest"] = [tree_structure(tree, names) for tree in forest.estimators_]
    paths = {name: trace_tree(models[name], v[0], names) for name in ["tree", "diagnostic"]}
    paths["forest"] = [trace_tree(tree, v[0], names) for tree in forest.estimators_]
    verification = {}
    per_tree = {}
    for part, matrix in [("train", x), ("validation", v)]:
        stacked = np.column_stack([tree.predict(matrix) for tree in forest.estimators_])
        average, actual = stacked.mean(axis=1), forest.predict(matrix)
        np.testing.assert_allclose(average, actual, atol=TOLERANCES["prediction_atol"], rtol=TOLERANCES["prediction_rtol"])
        verification[part] = {"rows": len(matrix), "max_absolute_difference": float(np.max(np.abs(average - actual)))}
        per_tree[part] = stacked
    bootstrap = [{"tree": i, "draws": len(ids), "unique_training_rows": len(np.unique(ids)), "ordered_draw_indices_sha256": sha(encoded(ids.tolist()))} for i, ids in enumerate(forest.estimators_samples_)]
    row = val.iloc[0]
    trace = {"record_id": row.record_id, "target_time": str(row.target_time), "observed": int(row.cnt), "features": {name: int(row[name]) for name in FEATURES}, "encoded_names": names, "encoded_values": v[0].tolist(), "paths": paths,
             "forest_first_row_per_tree": per_tree["validation"][0].tolist(), "forest_first_row_mean": float(per_tree["validation"][0].mean()), "forest_average_verification": verification}
    return structures, trace, bootstrap, per_tree


def diagnostics(predictions, names):
    dev = predictions.loc[predictions.partition.eq("validation")]
    first = json.loads(dev.head(48).to_json(orient="records", date_format="iso", double_precision=15))
    hours = [{"hour": int(hour), "rows": len(rows), "models": {name: {**metrics(rows.cnt, rows[name].to_numpy()), "mean_residual": float(rows[f"residual_{name}"].mean())} for name in names}} for hour, rows in dev.groupby("hr")]
    assert len(hours) == 24
    return {"selection": CONTRACT["diagnostics"], "first48": first, "hour_slices": hours}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", help="Official UCI ZIP; both inherited SHA-256 hashes verified. Default: download/cache data/bike.zip")
    args = parser.parse_args()
    start, cpu = time.perf_counter(), time.process_time()
    df = parse(source_bytes(ROOT / "data", args.archive))
    assert sha((ROOT / "dataset.py").read_bytes()) == REFERENCE["dataset_helper_sha256"]
    assert logical_hash(df) == REFERENCE["full_source_mechanical_logical_sha256"]
    blocks = partitions(df)
    manifest = freeze(blocks, ROOT / "partitions.json")
    assert manifest["contract_sha256"] == REFERENCE["contract_sha256"]
    for part, expected in REFERENCE["partitions"].items():
        assert all(manifest["partitions"][part][k] == value for k, value in expected.items()), part
    train, val = blocks["train"], blocks["validation"]
    inputs = {part: logical_hash(rows[["record_id", *FEATURES, "cnt"]]) for part, rows in [("train", train), ("validation", val)]}
    for part, digest in inputs.items():
        assert digest == REFERENCE[f"{part}_input_sha256"]
    declaration = {"issue": 24, "declared_before_any_fit": True, "inherited_contract_sha256": manifest["contract_sha256"],
                   "models": {name: model.get_params() for name, model in estimators().items()},
                   "encoder": {**OneHotEncoder(categories="auto", drop="first", handle_unknown="ignore", sparse_output=False).get_params(), "dtype": "float64"},
                   "tolerances": TOLERANCES, "baseline_reference_sha256": sha((ROOT / "baseline-reference.json").read_bytes()),
                   "feature_policy_clarification": "No engineered interaction columns; tree paths may learn conditional interactions on the same 40 columns. protocol.json is the inherited #21 receipt, not the complete #24 model declaration.",
                   "objective": "OLS/tree/forest squared-error training; constants median/mean; primary evaluation MAE, secondary MSE/RMSE",
                   "weights": None, "postprocessing": None, "threads": 1, "search": None,
                   "size_definition": "len(pickle.dumps((fitted_encoder, fitted_estimator), protocol=5)); standalone inference pair, metadata overhead included; in memory only",
                   "timing_definition": "Separate perf_counter wall/process_time CPU fit and train/development predict calls; encoder preparation timed separately; metrics/serialization excluded from per-model times"}
    config_path = ROOT / "frozen-config.json"
    if config_path.exists() and json.loads(config_path.read_text(encoding="utf-8")) != declaration:
        raise ValueError("frozen configuration changed: disclose a new experiment instead of overwriting")
    write_json(config_path, declaration)  # Durable declaration BEFORE encoder or estimator fitting.
    config_sha = sha(config_path.read_bytes())
    check()  # Exact toy arithmetic, in memory, independent of fitted UCI models.
    with threadpool_limits(limits=1):
        (encoder, x, v), preparation_time = measured(lambda: prepare(train, val))
        assert x.shape == (8644, 40) and v.shape == (4358, 40)
        models, predictions, scores, timings, sizes, baseline_check = fit_compare(train, val, encoder, x, v)
        structures, trace, bootstrap, per_tree = inspect_models(models, encoder, x, v, val)
        pools = threadpool_info()
        assert all(pool["num_threads"] == 1 for pool in pools)
    predictions.to_parquet(ROOT / "data/predictions.parquet", index=False)
    for name, model in models.items():
        (ROOT / f"data/{name}.pkl").write_bytes(pickle.dumps((encoder, model), protocol=5))
    tree_predictions = pd.DataFrame(np.vstack([per_tree["train"], per_tree["validation"]]), columns=[f"tree_{i:03d}" for i in range(100)])
    tree_predictions.insert(0, "record_id", predictions.record_id.to_numpy())
    tree_predictions.insert(1, "partition", predictions.partition.to_numpy())
    tree_predictions.to_parquet(ROOT / "data/forest-predictions.parquet", index=False)
    write_json(ROOT / "structures.json", {"encoded_names": encoder.get_feature_names_out(FEATURES).tolist(), "models": structures, "bootstrap": bootstrap})
    write_json(ROOT / "trace.json", trace)
    write_json(ROOT / "diagnostics.json", diagnostics(predictions, models))
    assert sha(config_path.read_bytes()) == config_sha
    encoding = {"names": encoder.get_feature_names_out(FEATURES).tolist(), "encoded_columns": x.shape[1],
                "categories": {name: cat.tolist() for name, cat in zip(FEATURES, encoder.categories_, strict=True)},
                "reference_categories": {name: int(cat[idx]) for name, cat, idx in zip(FEATURES, encoder.categories_, encoder.drop_idx_, strict=True)},
                "unknown_validation_counts": {name: int((~val[name].isin(cat)).sum()) for name, cat in zip(FEATURES, encoder.categories_, strict=True)}}
    deltas = {name: scores[name]["validation"]["mae"] - scores["ols"]["validation"]["mae"] for name in models}
    report = {"versions": {**versions(), **{name: importlib.metadata.version(name) for name in ["joblib", "threadpoolctl"]}},
              "hardware": {"platform": platform.platform(), "processor": platform.processor(), "logical_cpus": os.cpu_count()},
              "source": {"url": URL, "zip_sha256": ZIP_SHA, "member_sha256": SOURCE_SHA, "mechanical_logical_sha256": logical_hash(df), "rows": len(df), "audit_scope": "Inherited whole-source schema/domain/component checks read reserved targets mechanically; no reserved model fit/prediction/score or target-specific diagnostic"},
              "helper_sha256": {name: sha((ROOT / name).read_bytes()) for name in ["dataset.py", "protocol.py"]}, "code_sha256": code_hash(),
              "frozen_config_sha256": config_sha, "inherited_input_sha256": inputs, "partitions": manifest, "encoding": encoding,
              "baseline_identity": baseline_check, "constants": {name: models[name].constant_.item() for name in ["median", "mean"]},
              "ols_state": {"intercept": float(models["ols"].intercept_), "coefficients": models["ols"].coef_.tolist(), "rank": int(models["ols"].rank_)},
              "scores": scores, "development_mae_minus_ols": deltas,
              "comparison_to_ols": {name: "tie" if abs(delta) <= TOLERANCES["ranking_mae_atol"] else ("lower MAE" if delta < 0 else "higher MAE") for name, delta in deltas.items()},
              "timings": timings, "preparation_time": preparation_time, "serialized_bytes": sizes, "threadpools_during_fit": pools,
              "forest_average_verification": trace["forest_average_verification"], "final_metrics": None,
              "artifacts_sha256": {name: sha((ROOT / name).read_bytes()) for name in ["partitions.json", "structures.json", "trace.json", "diagnostics.json", "data/partitions.parquet", "data/predictions.parquet", "data/forest-predictions.parquet", *[f"data/{name}.pkl" for name in models]]},
              "runtime": {"repetitions": 1, "wall_seconds": time.perf_counter() - start, "process_cpu_seconds": time.process_time() - cpu,
                          "boundary": "Source fetch/cache verification through mechanical parse, partition/config freeze, fit, train/dev prediction, metrics, structure/path/forest checks and artifact writes; excludes dependency installation, final report write and tests. Single observation, not benchmark."}}
    write_json(ROOT / "report.json", report)
    print(json.dumps({"scores": scores, "baseline_identity_passed": baseline_check["passed"], "runtime": report["runtime"]}, indent=2))


if __name__ == "__main__":
    main()
