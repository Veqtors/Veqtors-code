"""Fit fixed median/mean/OLS baselines and score development only."""
import argparse
import math
import os
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from threadpoolctl import threadpool_info, threadpool_limits

from dataset import code_hash, encoded, logical_hash, parse, sha, source_bytes, versions, write_json
from protocol import CONTRACT, FEATURES, features, freeze, partitions, validate_features


def require_development(frame, partition):
    """Fail before fitting/predicting/scoring when final or mislabelled rows enter."""
    t = frame.target_time
    b0, b1, b2 = (pd.Timestamp(CONTRACT[k]) for k in ["train_start", "validation_start", "reserved_start"])
    allowed = (t >= b0) & (t < b1) if partition == "train" else (t >= b1) & (t < b2)
    if partition not in {"train", "validation"} or frame.empty or not allowed.all():
        raise ValueError("only declared train/development windows may be scored")
    if frame.record_id.duplicated().any() or not t.is_monotonic_increasing:
        raise ValueError("unique ordered scoring IDs required")


def metrics(y, pred):
    if not np.isfinite(pred).all():
        raise ValueError("nonfinite raw prediction")
    mse = mean_squared_error(y, pred)
    return {"mae": mean_absolute_error(y, pred), "mse": mse, "rmse": math.sqrt(mse)}


def compare(train, val):
    require_development(train, "train")
    require_development(val, "validation")
    if set(train.record_id) & set(val.record_id):
        raise ValueError("training/validation ID overlap")
    issue = val.target_time.min() - pd.Timedelta(hours=1)
    if not (train.target_time + pd.Timedelta(hours=1) <= issue).all():
        raise ValueError("training labels not ready")
    x_train, x_val = features(train), features(val)
    validate_features(x_train); validate_features(x_val)
    models = {"median": DummyRegressor(strategy="median"), "mean": DummyRegressor(strategy="mean"), "ols": Pipeline([("encoder", OneHotEncoder(categories="auto", drop="first", handle_unknown="ignore", sparse_output=False)), ("linear", LinearRegression(fit_intercept=True, positive=False, copy_X=True, n_jobs=1))])}
    predictions = {"train": train[["record_id", "target_time", "hr", "cnt"]].copy(), "validation": val[["record_id", "target_time", "hr", "cnt"]].copy()}
    scores, timings = {}, {}
    for name, model in models.items():
        wall, cpu = time.perf_counter(), time.process_time()
        model.fit(x_train, train.cnt)
        train_pred, val_pred = model.predict(x_train), model.predict(x_val)
        timings[name] = {"fit_predict_wall_seconds": time.perf_counter() - wall, "fit_predict_cpu_seconds": time.process_time() - cpu}
        scores[name] = {}
        for key, rows, pred in [("train", train, train_pred), ("validation", val, val_pred)]:
            if not predictions[key].record_id.equals(rows.record_id):
                raise ValueError("paired ID mismatch")
            scores[name][key] = {**metrics(rows.cnt, pred), "negative_count": int((pred < 0).sum()), "minimum_prediction": float(np.min(pred)), "rows": len(rows)}
            predictions[key][name] = pred
            predictions[key][f"residual_{name}"] = rows.cnt.to_numpy() - pred
    output = pd.concat([v.assign(partition=k) for k, v in predictions.items()], ignore_index=True)
    return models, output, scores, timings


def trace_prediction(model, val):
    row = val.iloc[[0]]  # Predeclared first development row, never largest error.
    encoder, linear = model.named_steps["encoder"], model.named_steps["linear"]
    values = encoder.transform(features(row))[0]
    names = encoder.get_feature_names_out(FEATURES)
    terms = [{"feature": str(n), "value": float(x), "coefficient": float(c), "contribution": float(x * c)} for n, x, c in zip(names, values, linear.coef_, strict=True)]
    total = float(linear.intercept_) + math.fsum(t["contribution"] for t in terms)
    prediction = float(model.predict(features(row))[0])
    np.testing.assert_allclose(total, prediction, rtol=0, atol=1e-10)
    return {"record_id": row.record_id.iloc[0], "target_time": str(row.target_time.iloc[0]), "features": {k: int(row[k].iloc[0]) for k in FEATURES}, "observed": int(row.cnt.iloc[0]), "intercept": float(linear.intercept_), "terms": terms, "summed_prediction": total, "estimator_prediction": prediction, "absolute_difference": abs(total - prediction), "interpretation": "Conditional additive model associations in rental-count units; not causal effects or universal feature importance"}


def residual_svg(rows, path):
    """Code-generated diagnostic: predeclared first 48 signed OLS residuals."""
    residuals = rows.residual_ols.to_numpy()
    extent = max(1., float(np.max(np.abs(residuals))))
    points = " ".join(f"{55 + i * 820 / max(1, len(rows)-1):.2f},{180 - r * 120 / extent:.2f}" for i, r in enumerate(residuals))
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="920" height="380" viewBox="0 0 920 380"><rect width="920" height="380" fill="white"/><g font-family="sans-serif" fill="#172333"><text x="55" y="28" font-size="18">First 48 development records: observed minus raw OLS prediction</text><text x="55" y="50" font-size="12">Positive = underprediction; naive source-calendar order; no final-test rows</text><text x="6" y="65" font-size="12">+{extent:.1f}</text><text x="20" y="184" font-size="12">0</text><text x="6" y="307" font-size="12">−{extent:.1f}</text><text x="55" y="345" font-size="12">{rows.target_time.iloc[0]}</text><text x="680" y="345" font-size="12">{rows.target_time.iloc[-1]}</text></g><path d="M55 60V305H880 M55 180H880" fill="none" stroke="#999"/><polyline points="{points}" fill="none" stroke="#146b79" stroke-width="2"/></svg>'
    path.write_text(svg + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", help="Official ZIP; exact hashes verified")
    args = parser.parse_args()
    root = Path(__file__).parent
    start, cpu_start = time.perf_counter(), time.process_time()
    df = parse(source_bytes(root / "data", args.archive))
    blocks = partitions(df)
    manifest = freeze(blocks, root / "partitions.json")  # Durable artifact before fit.
    train, val = blocks["train"], blocks["validation"]
    model_config = {"contract_sha256": manifest["contract_sha256"], "encoding": CONTRACT["encoding"], "linear": LinearRegression(fit_intercept=True, positive=False, copy_X=True, n_jobs=1).get_params(), "dummies": ["median", "mean"], "weights": None, "postprocessing": None, "threads": 1}
    write_json(root / "model-config.json", model_config)  # Also before fit.
    with threadpool_limits(limits=1):
        models, predictions, scores, timings = compare(train, val)
        trace = trace_prediction(models["ols"], val)
        enc = models["ols"].named_steps["encoder"]
        design = enc.transform(features(train))
        rank = int(np.linalg.matrix_rank(np.column_stack([np.ones(len(train)), design])))
        pools = threadpool_info()
    predictions.to_parquet(root / "data/predictions.parquet", index=False)
    write_json(root / "trace.json", trace)
    dev = predictions.loc[predictions.partition.eq("validation")]
    window = dev.head(48).copy()
    residual_svg(window, root / "residuals.svg")
    diagnostics = {"selection": CONTRACT["diagnostics"], "first48": [{"record_id": r.record_id, "target_time": str(r.target_time), "observed": int(r.cnt), "prediction": float(r.ols), "residual": float(r.residual_ols)} for r in window.itertuples()], "hour_slices": [{"hour": int(hour), "rows": len(rows), "mean_residual": float(rows.residual_ols.mean()), **metrics(rows.cnt, rows.ols)} for hour, rows in dev.groupby("hr")], "negative_ids_sha256": {name: sha(encoded(dev.loc[dev[name] < 0, "record_id"].tolist())) for name in models}}
    write_json(root / "diagnostics.json", diagnostics)
    delta = scores["ols"]["validation"]["mae"] - scores["median"]["validation"]["mae"]
    report = {"versions": versions(), "hardware": {"platform": platform.platform(), "processor": platform.processor(), "logical_cpus": os.cpu_count()}, "threadpools_during_fit": pools, "code_sha256": code_hash(), "dataset_helper_sha256": sha((root / "dataset.py").read_bytes()), "full_source_mechanical_logical_sha256": logical_hash(df), "train_input_sha256": logical_hash(train[["record_id", *FEATURES, "cnt"]]), "validation_input_sha256": logical_hash(val[["record_id", *FEATURES, "cnt"]]), "partitions": manifest, "model_config_sha256": sha(encoded(model_config)), "scores": scores, "timings": timings, "constants": {name: float(models[name].constant_.ravel()[0]) for name in ["median", "mean"]}, "encoding": {"categories": {name: cat.tolist() for name, cat in zip(FEATURES, enc.categories_, strict=True)}, "reference_categories": {name: int(cat[idx]) for name, cat, idx in zip(FEATURES, enc.categories_, enc.drop_idx_, strict=True)}, "names": enc.get_feature_names_out(FEATURES).tolist(), "encoded_columns": design.shape[1], "augmented_rank": rank, "augmented_columns": design.shape[1] + 1, "centered_solver_rank": int(models["ols"].named_steps["linear"].rank_), "unknown_validation_counts": {name: int((~val[name].isin(cat)).sum()) for name, cat in zip(FEATURES, enc.categories_, strict=True)}}, "ols_minus_median_validation_mae": delta, "comparison": "tie" if abs(delta) <= CONTRACT["comparison_tolerance"] else ("OLS lower MAE" if delta < 0 else "median lower MAE"), "predictions_parquet_sha256": sha((root / "data/predictions.parquet").read_bytes()), "final_metrics": None, "runtime": {"repetitions": 1, "wall_seconds": time.perf_counter() - start, "process_cpu_seconds": time.process_time() - cpu_start, "boundary": "verified local ZIP read through preparation/freeze, fit, train+dev predict/metrics, trace/rank/diagnostics/artifacts; excludes final report write and dependency installation"}}
    write_json(root / "report.json", report)
    print({"scores": scores, "rank": rank, "columns": design.shape[1] + 1, "trace_prediction": trace["estimator_prediction"], "delta_mae": delta, "runtime": report["runtime"]})


if __name__ == "__main__":
    main()
