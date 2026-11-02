"""Frozen calendar partition and exact feature allowlist; replicated in #21."""
import json
from pathlib import Path

import pandas as pd
from dataset import encoded, sha, write_json

CONTRACT = json.loads(Path(__file__).with_name("protocol.json").read_text(encoding="utf-8"))
FEATURES = CONTRACT["features"]


def features(frame):
    return frame.loc[:, FEATURES].copy()


def validate_features(frame):
    if list(frame.columns) != FEATURES or frame.isna().any().any():
        raise ValueError("exact nonmissing feature allowlist required")


def partitions(df):
    t = df.target_time
    start, b1, b2 = (pd.Timestamp(CONTRACT[k]) for k in ["train_start", "validation_start", "reserved_start"])
    nominal = df.loc[(t >= start) & (t < b1)].copy()
    val = df.loc[(t >= b1) & (t < b2)].copy()
    reserved = df.loc[t >= b2, ["record_id", "target_time"]].copy()
    if nominal.empty or val.empty or reserved.empty:
        raise ValueError("all declared windows must have records")
    issue = val.target_time.min() - pd.Timedelta(hours=CONTRACT["issue_lead_hours"])
    ready = nominal.target_time + pd.Timedelta(hours=CONTRACT["target_interval_hours"] + CONTRACT["reporting_delay_hours"])
    train = nominal.loc[ready <= issue].copy()
    excluded = nominal.loc[ready > issue, ["record_id", "target_time"]].copy()
    blocks = {"train": train, "validation": val, "reserved": reserved, "readiness_excluded": excluded}
    all_ids = []
    all_times = []
    for block in blocks.values():
        if not block.target_time.is_monotonic_increasing:
            raise ValueError("partition order")
        all_ids.extend(block.record_id)
        all_times.extend(block.target_time)
    if len(all_ids) != len(set(all_ids)) or len(all_times) != len(set(all_times)):
        raise ValueError("partition identity/time overlap")
    if len(all_ids) != len(df):
        raise ValueError("partition accounting")
    return blocks


def freeze(blocks, path):
    identity = {k: {"count": len(v), "ordered_ids_sha256": sha(encoded(v.record_id.tolist())), "first": str(v.target_time.min()), "last": str(v.target_time.max())} for k, v in blocks.items()}
    manifest = {"contract": CONTRACT, "contract_sha256": sha(encoded(CONTRACT)), "partitions": identity, "first_validation_issuance": str(blocks["validation"].target_time.min() - pd.Timedelta(hours=1)), "excluded_ids": blocks["readiness_excluded"].record_id.tolist()}
    write_json(path, manifest)
    # Persist exact ordered IDs and times without reserved targets.
    ordered = pd.concat([v[["record_id", "target_time"]].assign(partition=k) for k, v in blocks.items()], ignore_index=True)
    ordered.to_parquet(Path(path).parent / "data/partitions.parquet", index=False)
    return manifest
